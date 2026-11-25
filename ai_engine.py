from google import genai
import os
import re

# ==========================================
# CONFIGURATION
# ==========================================
# This safely reads the key from Render's secret environment variables, 
# or uses your local key if you are running it on your laptop.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_ACTUAL_GEMINI_API_KEY_HERE")

# Cache the working model globally so we don't scan models every time
CACHED_WORKING_MODEL = None

# ==========================================
# DATABASE SCHEMA PROMPT
# ==========================================
DATABASE_SCHEMA = """
You are an expert SQL Assistant for a SQLite database named 'company.db'.
Your ONLY task is to convert natural language user questions into valid SQLite SELECT queries.

Database Schema:

1. Table: departments
   - department_id (INTEGER PRIMARY KEY)
   - department_name (TEXT)
   - location (TEXT)

2. Table: employees
   - employee_id (INTEGER PRIMARY KEY)
   - employee_name (TEXT)
   - email (TEXT)
   - salary (REAL)
   - department_id (INTEGER, Foreign Key referencing departments.department_id)
   - designation (TEXT)
   - joining_year (INTEGER)

RULES:
1. Return ONLY the raw SQL query.
2. DO NOT include markdown formatting like ```sql or ```.
3. DO NOT include any text before or after the SQL.
4. Only generate SELECT queries (No DROP, DELETE, INSERT, UPDATE, ALTER).
5. Join tables using department_id whenever department names or details are requested.
"""

def generate_sql_query(user_question: str) -> str:
    global CACHED_WORKING_MODEL

    if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_ACTUAL_GEMINI_API_KEY_HERE":
        return "ERROR_NO_KEY"

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = f"{DATABASE_SCHEMA}\n\nUser Question: {user_question}\n\nSQL Query:"

        # 1. If we already know which model works, use it directly (INSTANT RESPONSE)
        if CACHED_WORKING_MODEL:
            try:
                res = client.models.generate_content(
                    model=CACHED_WORKING_MODEL,
                    contents=prompt,
                )
                if res and res.text:
                    return clean_sql_text(res.text)
            except Exception:
                CACHED_WORKING_MODEL = None  # Reset cache if it fails

        # 2. Fast candidate list for first-time discovery
        candidates = [
            "gemini-1.5-flash",
            "gemini-2.5-flash",
            "gemini-1.5-pro",
        ]

        # Try fetching dynamic list if candidates fail
        for model_id in candidates:
            try:
                response = client.models.generate_content(
                    model=model_id,
                    contents=prompt,
                )
                if response and response.text:
                    CACHED_WORKING_MODEL = model_id
                    print(f"⚡ Cached active model: {model_id}")
                    return clean_sql_text(response.text)
            except Exception:
                continue

        # If static candidates fail, try dynamic listing once
        try:
            for m in client.models.list():
                m_name = getattr(m, 'name', '') or str(m)
                if 'gemini' in m_name.lower():
                    try:
                        response = client.models.generate_content(model=m_name, contents=prompt)
                        if response and response.text:
                            CACHED_WORKING_MODEL = m_name
                            return clean_sql_text(response.text)
                    except Exception:
                        continue
        except Exception as err:
            return f"ERROR_API: {str(err)}"

        return "ERROR_API: No responsive Gemini model found for this key."

    except Exception as e:
        return f"ERROR_API: {str(e)}"


def clean_sql_text(text: str) -> str:
    """Removes markdown code blocks."""
    sql = text.strip()
    sql = re.sub(r"^```sql\s*", "", sql, flags=re.IGNORECASE)
    sql = re.sub(r"^```\s*", "", sql)
    sql = re.sub(r"\s*```$", "", sql)
    return sql.strip()
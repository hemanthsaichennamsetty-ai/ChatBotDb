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
You are an expert SQL Assistant for a large, real-time enterprise SQLite database named 'company.db' modeled after Accenture's delivery structure.
Your ONLY task is to convert natural language user questions into valid SQLite SELECT queries.

Database Schema (10 Relational Tables):

1. Table: departments (Practices & Hubs)
   - department_id (INTEGER PRIMARY KEY)
   - department_name (TEXT)
   - location (TEXT: 'Bengaluru', 'Hyderabad', 'Mumbai', 'Gurugram', 'Chennai', 'Pune')
   - region (TEXT)
   - annual_budget (REAL)
   - cost_center_code (TEXT)

2. Table: employees (1,000 Staff across CL6 -> CL12)
   - employee_id (INTEGER PRIMARY KEY)
   - employee_name (TEXT)
   - email (TEXT)
   - salary (REAL)
   - department_id (INTEGER, Foreign Key -> departments.department_id)
   - manager_id (INTEGER, Self-referencing Foreign Key -> employees.employee_id; NULL for Practice Leads)
   - career_level (TEXT: 'CL6', 'CL7', 'CL8', 'CL9', 'CL10', 'CL11', 'CL12')
   - designation (TEXT)
   - employment_type (TEXT: 'Full-Time', 'Hybrid', 'Contract')
   - joining_year (INTEGER)
   - status (TEXT: 'Active', 'On Leave')

3. Table: clients
   - client_id (INTEGER PRIMARY KEY)
   - client_name (TEXT)
   - industry (TEXT)
   - hq_country (TEXT)
   - tier (TEXT: 'Platinum', 'Gold', 'Silver', 'Internal')
   - annual_contract_value (REAL)

4. Table: projects (Client & Internal Engagements)
   - project_id (INTEGER PRIMARY KEY)
   - project_name (TEXT)
   - client_id (INTEGER, Foreign Key -> clients.client_id)
   - department_id (INTEGER, Foreign Key -> departments.department_id)
   - billing_model (TEXT: 'Time & Materials', 'Fixed Price', 'Managed Services')
   - budget (REAL)
   - status (TEXT: 'In Progress', 'Completed', 'Planning')
   - start_year (INTEGER)
   - deadline_quarter (TEXT)

5. Table: employee_projects (Project Staffing & Billability)
   - assignment_id (INTEGER PRIMARY KEY)
   - employee_id (INTEGER, Foreign Key -> employees.employee_id)
   - project_id (INTEGER, Foreign Key -> projects.project_id)
   - role_on_project (TEXT)
   - allocation_percent (INTEGER)
   - is_billable (INTEGER: 1 = billable, 0 = non-billable)
   - assigned_date (TEXT, ISO YYYY-MM-DD)

6. Table: performance_reviews
   - review_id (INTEGER PRIMARY KEY)
   - employee_id (INTEGER, Foreign Key -> employees.employee_id)
   - review_year (INTEGER)
   - rating (REAL, 1.0 to 5.0)
   - bonus_awarded (REAL)
   - reviewer_notes (TEXT)

7. Table: salary_history
   - history_id (INTEGER PRIMARY KEY)
   - employee_id (INTEGER, Foreign Key -> employees.employee_id)
   - effective_year (INTEGER)
   - previous_salary (REAL)
   - new_salary (REAL)
   - change_reason (TEXT)

8. Table: employee_certifications
   - cert_id (INTEGER PRIMARY KEY)
   - employee_id (INTEGER, Foreign Key -> employees.employee_id)
   - certification_name (TEXT)
   - vendor (TEXT)
   - issued_year (INTEGER)
   - status (TEXT: 'Active', 'Renewal Due')

9. Table: delivery_incidents
   - incident_id (INTEGER PRIMARY KEY)
   - project_id (INTEGER, Foreign Key -> projects.project_id)
   - assigned_employee_id (INTEGER, Foreign Key -> employees.employee_id)
   - severity (TEXT: 'P1 - Critical', 'P2 - High', 'P3 - Medium', 'P4 - Low')
   - category (TEXT)
   - status (TEXT: 'Resolved', 'In Progress', 'Escalated')
   - resolution_hours (REAL)
   - reported_date (TEXT, ISO YYYY-MM-DD)

10. Table: attendance_logs
   - log_id (INTEGER PRIMARY KEY)
   - employee_id (INTEGER, Foreign Key -> employees.employee_id)
   - work_date (TEXT, ISO YYYY-MM-DD; latest date is '2026-11-25')
   - check_in_time (TEXT, HH:MM:SS or NULL)
   - work_mode (TEXT: 'Office', 'WFH', 'Client Site')
   - hours_logged (REAL)
   - attendance_status (TEXT: 'Present', 'On Leave', 'Half Day')

RULES:
1. Return ONLY the raw SQL query.
2. DO NOT include markdown formatting like ```sql or ```.
3. DO NOT include any text before or after the SQL.
4. Only generate SELECT queries (No DROP, DELETE, INSERT, UPDATE, ALTER).
5. Join tables so results include clear names (employee_name, department_name, client_name, project_name, and manager name via self-join) instead of raw IDs whenever helpful.
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

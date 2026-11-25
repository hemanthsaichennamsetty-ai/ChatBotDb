from flask import Flask, render_template, request, jsonify
import sqlite3
from pathlib import Path
import ai_engine

app = Flask(__name__)

DATABASE_PATH = Path(__file__).resolve().parent / "company.db"

def execute_query(query: str):
    """Executes SQL query on company.db and returns columns & rows."""
    if not DATABASE_PATH.exists():
        return None, "company.db not found. Run database.py first!"

    try:
        connection = sqlite3.connect(DATABASE_PATH)
        cursor = connection.cursor()
        cursor.execute(query)
        headers = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        connection.close()
        return headers, rows
    except Exception as e:
        return None, str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat_api():
    data = request.get_json()
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"error": "Empty message received"}), 400

    generated_sql = ai_engine.generate_sql_query(user_message)

    if generated_sql == "ERROR_NO_KEY":
        return jsonify({"error": "API Key missing in ai_engine.py"}), 400
    elif generated_sql.startswith("ERROR_API:"):
        return jsonify({"error": generated_sql.replace("ERROR_API: ", "")}), 400

    headers, rows = execute_query(generated_sql)

    if headers is None:
        return jsonify({
            "sql": generated_sql,
            "error": f"SQL Execution Error: {rows}"
        })

    return jsonify({
        "sql": generated_sql,
        "headers": headers,
        "rows": rows,
        "row_count": len(rows)
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
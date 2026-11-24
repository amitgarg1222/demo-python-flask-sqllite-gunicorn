import sqlite3
from datetime import datetime, timezone
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

# Named shared in-memory SQLite URI so multiple threads/connections in the same
# worker process share the exact same in-memory database while it stays open.
IN_MEMORY_DB_URI = "file:ec2_task_db?mode=memory&cache=shared"

# Keep a persistent anchor connection open so the in-memory database is not
# garbage-collected when request connections close.
_anchor_conn = sqlite3.connect(IN_MEMORY_DB_URI, uri=True, check_same_thread=False)
_anchor_conn.row_factory = sqlite3.Row


def get_db():
    conn = sqlite3.connect(IN_MEMORY_DB_URI, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                completed INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL
            )
            """
        )
        count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if count == 0:
            now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            conn.executemany(
                "INSERT INTO tasks (title, completed, created_at) VALUES (?, ?, ?)",
                [
                    ("Verify Flask + SQLite in-memory database locally", 1, now),
                    ("Deploy project to AWS EC2 behind Gunicorn and Nginx", 0, now),
                    ("Test application in browser via EC2 Public IP", 0, now),
                ],
            )
    conn.close()


init_db()


@app.route("/")
def index():
    conn = get_db()
    tasks = conn.execute("SELECT id, title, completed, created_at FROM tasks ORDER BY id DESC").fetchall()
    conn.close()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return render_template("index.html", tasks=tasks, now=now)


@app.route("/tasks", methods=["POST"])
def add_task():
    title = request.form.get("title", "").strip()
    if title:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        conn = get_db()
        with conn:
            conn.execute(
                "INSERT INTO tasks (title, completed, created_at) VALUES (?, 0, ?)",
                (title, now),
            )
        conn.close()
    return redirect(url_for("index"))


@app.route("/tasks/<int:task_id>/toggle", methods=["POST"])
def toggle_task(task_id):
    conn = get_db()
    with conn:
        conn.execute(
            "UPDATE tasks SET completed = CASE WHEN completed = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (task_id,),
        )
    conn.close()
    return redirect(url_for("index"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    conn = get_db()
    with conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.close()
    return redirect(url_for("index"))


@app.route("/api/tasks", methods=["GET"])
def api_tasks():
    conn = get_db()
    rows = conn.execute("SELECT id, title, completed, created_at FROM tasks ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify(
        {
            "database": "sqlite:///:memory: (shared cache)",
            "count": len(rows),
            "tasks": [dict(row) for row in rows],
        }
    )


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "storage": "sqlite-in-memory"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)

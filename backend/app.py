from flask import Flask, jsonify, request
import os
import psycopg2

app = Flask(__name__)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("POSTGRES_DB", "tasksdb"),
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD", "admin123")
    )


@app.route("/")
def home():
    return jsonify({
        "message": "Hello from Flask Backend API"
    })


@app.route("/health")
def health():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify({
            "status": "healthy",
            "database": "connected"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "database": "disconnected"
        }), 500


@app.route("/tasks", methods=["GET"])
def get_tasks():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, description, completed
        FROM tasks
        ORDER BY id
    """)

    tasks = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify([
        {
            "id": task[0],
            "title": task[1],
            "description": task[2],
            "completed": task[3]
        }
        for task in tasks
    ])


@app.route("/tasks", methods=["POST"])
def create_task():
    data = request.get_json()

    title = data.get("title")
    description = data.get("description", "")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO tasks (title, description, completed)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (title, description, False)
    )

    task_id = cursor.fetchone()[0]

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({
        "message": "Task created",
        "id": task_id
    }), 201


@app.route("/tasks/<int:task_id>", methods=["PUT"])
def update_task(task_id):
    data = request.get_json()

    title = data.get("title")
    description = data.get("description")
    completed = data.get("completed")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE tasks
        SET title = %s,
            description = %s,
            completed = %s
        WHERE id = %s
        """,
        (title, description, completed, task_id)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Task updated"
    })


@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM tasks WHERE id = %s",
        (task_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "message": "Task deleted"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
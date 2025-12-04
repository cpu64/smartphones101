# models/requests.py
from models.db import execute, get_one, get_all, get_db_connection
from datetime import datetime
import psycopg2

def get_requests():
    try:
        requests = get_all("""
            SELECT r.id,
                   r.amount,
                   r.created_at,
                   u.username AS username,
                   r.user_id
            FROM requests r
            JOIN users u ON r.user_id = u.id
            ORDER BY r.created_at DESC
        """)
        return requests
    except Exception as e:
        print(f"Error fetching requests: {e}")
        return "Error fetching requests."

def approve_all():
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE users u
            SET credits = credits + r.total_amount
            FROM (
                SELECT user_id, SUM(amount) AS total_amount
                FROM requests
                GROUP BY user_id
            ) r
            WHERE u.id = r.user_id;
        """)
        cur.execute("DELETE FROM requests;")
        conn.commit()
    except Exception as e:
        print(f"Error approving requests: {e}")
        if conn:
            conn.rollback()
        return "Unknown error while approving requests."

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

def create_request(user_id, amount):
    try:
        execute("""
            INSERT INTO requests (amount, user_id)
            VALUES (%s, %s)
        """, (amount, user_id))
    except psycopg2.errors.ForeignKeyViolation:
        return "Invalid user ID."

    except psycopg2.errors.CheckViolation:
        return "Amount must be valid and non-empty."

    except psycopg2.errors.StringDataRightTruncation:
        return "Invalid input length. Please check your amount."

    except Exception as e:
        print(f"Error creating request: {e}")
        return "Unknown error while creating request."

def delete_request(request_id):
    try:
        execute("""
            DELETE FROM requests
            WHERE id = %s
        """, (request_id,))
    except Exception as e:
        print(f"Error deleting request: {e}")
        return "Error deleting request."

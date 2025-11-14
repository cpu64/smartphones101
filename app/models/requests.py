# models/requests.py
from models.db import execute, get_one, get_all
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

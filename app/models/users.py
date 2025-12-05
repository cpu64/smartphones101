# models/users.py
from models.db import execute, get_one, get_all, get_db_connection
from datetime import datetime
import psycopg2

USER_COLUMN_LENGTHS = {
    "username": [3, 30],
    "password": [3, 60]
}

def check_length(key, value):
    if USER_COLUMN_LENGTHS[key][0] <= len(value) <= USER_COLUMN_LENGTHS[key][1]:
        return False
    return f"{USER_COLUMN_LENGTHS[key][0]} and {USER_COLUMN_LENGTHS[key][1]}"

def get_credentials(username):
    try:
        credentials = get_one("SELECT id, password, role FROM users WHERE username = %s", (username,))
        if credentials:
            return credentials
        return "No such user."
    except Exception as e:
        print(f"Error occurred while fetching user credentials: {e}")
        return "Error occurred while fetching user credentials."

def get_users():
    try:
        data = get_all("SELECT id, username, email, password, role FROM users ORDER BY id ASC")
        if data:
            return data
        return "No users."
    except Exception as e:
        print(f"Error occurred while fetching users: {e}")
        return "Error occurred while fetching users."

def register_user(username, hashed_password, email, role='user'):
    try:
        print(username, hashed_password, email)
        execute("""
            INSERT INTO users (username, password, email, role)
            VALUES (%s, %s, %s, %s)
        """, (username, hashed_password, email, role))
    except psycopg2.errors.UniqueViolation:
        return "Username or email already exists."

    except psycopg2.errors.StringDataRightTruncation:
        return "Invalid input length. Please check your username and password."

    except Exception as e:
        print(f"Unknown error: {e}")
        return "Unknown error."

def get_consultants():
    try:
        consultants = get_all("""
            SELECT id, username, timetable
            FROM users
            WHERE role = 'consultant'
            ORDER BY username ASC
        """)
        return consultants
    except Exception as e:
        print(f"Error fetching consultants: {e}")
        return "Error fetching consultants."

def reserve_slot(consultant_id, username, day, hour):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:

            # Lock consultant row slot
            cur.execute("""
                SELECT timetable[%s][%s]
                FROM users
                WHERE id = %s AND role = 'consultant'
                FOR UPDATE
            """, (day, hour, consultant_id))
            slot = cur.fetchone()

            if not slot:
                conn.rollback()
                return "Consultant not found."

            if slot[0] is not None:
                conn.rollback()
                return "This time slot is already reserved."

            # Lock user row for credit update
            cur.execute("""
                SELECT id, credits
                FROM users
                WHERE username = %s
                FOR UPDATE
            """, (username,))
            user_row = cur.fetchone()

            if not user_row:
                conn.rollback()
                return "User not found."

            user_id, credits = user_row

            # Check credits
            if credits < 50:
                conn.rollback()
                return "You do not have enough credits. (50 credits required)"

            # Deduct credits
            cur.execute("""
                UPDATE users
                SET credits = credits - 50
                WHERE id = %s
            """, (user_id,))

            # Reserve slot
            cur.execute("""
                UPDATE users
                SET timetable[%s][%s] = %s
                WHERE id = %s
            """, (day, hour, user_id, consultant_id))

            conn.commit()
            return None  # success

    except psycopg2.Error as e:
        print(f"Database error reserving slot: {e}")
        if conn:
            conn.rollback()
        return "Database error while reserving slot."

    except Exception as e:
        print(f"Error reserving slot: {e}")
        if conn:
            conn.rollback()
        return "Error reserving time slot."

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()



def cancel_slot(consultant_id, username, day, hour):
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:

            # Lock consultant slot
            cur.execute("""
                SELECT timetable[%s][%s]
                FROM users
                WHERE id = %s AND role = 'consultant'
                FOR UPDATE
            """, (day, hour, consultant_id))
            slot = cur.fetchone()

            if not slot:
                conn.rollback()
                return "Consultant not found."

            # Get user
            cur.execute("""
                SELECT id
                FROM users
                WHERE username = %s
                FOR UPDATE
            """, (username,))
            user_row = cur.fetchone()

            if not user_row:
                conn.rollback()
                return "User not found."

            user_id = user_row[0]

            # Verify slot belongs to user
            if slot[0] != user_id:
                conn.rollback()
                return "You cannot cancel a slot you do not own."

            # Clear slot
            cur.execute("""
                UPDATE users
                SET timetable[%s][%s] = NULL
                WHERE id = %s
            """, (day, hour, consultant_id))

            # Refund credits
            cur.execute("""
                UPDATE users
                SET credits = credits + 50
                WHERE id = %s
            """, (user_id,))

            conn.commit()
            return None  # success

    except psycopg2.Error as e:
        print(f"Database error cancelling slot: {e}")
        if conn:
            conn.rollback()
        return "Database error while cancelling reservation."

    except Exception as e:
        print(f"Error cancelling slot: {e}")
        if conn:
            conn.rollback()
        return "Error cancelling time slot."

    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()


def add_credits(username, amount):
    try:
        amount = int(amount)
        if amount <= 0:
            return "Amount must be a positive number."

    except ValueError:
        return "Invalid amount value."

    try:
        user = get_one("""
            SELECT id FROM users WHERE username = %s
        """, (username,))

        if not user:
            return "User not found."

        execute("""
            UPDATE users
            SET credits = credits + %s
            WHERE id = %s
        """, (amount, user["id"]))

    except psycopg2.Error as e:
        print(f"PostgreSQL error adding credits: {e}")
        return "Database error while adding credits."

    except Exception as e:
        print(f"Unknown error in add_credits(): {e}")
        return "Unknown error while adding credits."

def remove_credits(user_id, amount):
    try:
        amount = int(amount)
        if amount <= 0:
            return "Amount must be a positive number."

    except ValueError:
        return "Invalid amount value."

    try:
        user = get_one("""
            SELECT credits
            FROM users
            WHERE id = %s
        """, (user_id,))

        if not user:
            return "User not found."

        current_credits = user[0]

        if current_credits < amount:
            return f"User only has {current_credits} credits."

        execute("""
            UPDATE users
            SET credits = credits - %s
            WHERE id = %s
        """, (amount, user_id))
    except psycopg2.Error as e:
        print(f"PostgreSQL error removing credits: {e}")
        return "Database error while removing credits."

    except Exception as e:
        print(f"Unknown error in remove_credits(): {e}")
        return "Unknown error while removing credits."

def get_credits(username):
    try:
        credits = get_one("SELECT credits FROM users WHERE username = %s", (username,))
        if credits:
            return credits['credits']
        return "No such user."
    except Exception as e:
        print(f"Error occurred while fetching user credits: {e}")
        return "Error occurred while fetching user credits."

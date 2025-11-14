# models/chat.py
from models.db import execute, get_one, get_all
import psycopg2

def create_chat(user_id, consultant_id):
    try:
        execute("""
            INSERT INTO chat (user_id, consultant_id)
            VALUES (%s, %s)
        """, (user_id, consultant_id))
        return None  # success

    except psycopg2.errors.UniqueViolation:
        return "Chat already exists."

    except Exception as e:
        print(f"Error creating chat: {e}")
        return "Database error creating chat."


def delete_chat(chat_id):
    try:
        execute("""
            DELETE FROM chat WHERE id = %s
        """, (chat_id,))
        return None

    except Exception as e:
        print(f"Error deleting chat: {e}")
        return "Database error deleting chat."


def get_chat(chat_id):
    try:
        return get_one("""
            SELECT id, user_id, consultant_id, created_at
            FROM chat
            WHERE id = %s
        """, (chat_id,))
    except Exception as e:
        print(f"Error fetching chat: {e}")
        return None


def get_or_create_chat(user_id, consultant_id):
    try:
        chat = get_one("""
            SELECT id
            FROM chat
            WHERE user_id = %s AND consultant_id = %s
        """, (user_id, consultant_id))

        if chat:
            return chat["id"]

        # Otherwise create fresh
        err = create_chat(user_id, consultant_id)
        if err:
            return None

        new_chat = get_one("""
            SELECT id
            FROM chat
            WHERE user_id = %s AND consultant_id = %s
        """, (user_id, consultant_id))

        return new_chat["id"]

    except Exception as e:
        print(f"Error get_or_create_chat: {e}")
        return None

def get_chat_pair(day, hour, user_id, role):
    if not (1 <= day <= 3 and 1 <= hour <= 8):
        return None

    # ---------- Consultant: check only his array ----------
    if role == "consultant":
        row = get_one("""
            SELECT timetable[%s][%s] AS booked_user
            FROM users
            WHERE id = %s AND role = 'consultant'
        """, (day, hour, user_id))

        if not row or row["booked_user"] is None:
            return None  # no meeting booked

        booked_user_id = row["booked_user"]

        user = get_one("SELECT id, username FROM users WHERE id = %s", (booked_user_id,))
        consultant = get_one("SELECT id, username FROM users WHERE id = %s", (user_id,))

        if not user or not consultant:
            return None

        return {"user": user, "consultant": consultant}

    # ---------- User: search all consultant timetables ----------
    elif role == "user":
        row = get_one("""
            SELECT id AS consultant_id
            FROM users
            WHERE role = 'consultant'
            AND timetable[%s][%s] = %s
            LIMIT 1
        """, (day, hour, user_id))

        if not row:
            return None

        consultant_id = row["consultant_id"]

        user = get_one("SELECT id, username FROM users WHERE id = %s", (user_id,))
        consultant = get_one("SELECT id, username FROM users WHERE id = %s", (consultant_id,))

        if not user or not consultant:
            return None

        return {"user": user, "consultant": consultant}

    # Unknown role → reject
    return None


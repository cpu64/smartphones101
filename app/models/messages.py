# models/messages.py
from models.db import execute, get_one, get_all
import psycopg2

def send_message(chat_id, message_text):
    if not message_text or message_text.strip() == "":
        return "Message cannot be empty."

    try:
        execute("""
            INSERT INTO messages (chat_id, message)
            VALUES (%s, %s)
        """, (chat_id, message_text.strip()))
        return None  # success

    except psycopg2.errors.CheckViolation:
        return "Message cannot be empty."

    except Exception as e:
        print(f"Error sending message: {e}")
        return "Database error sending message."


def get_messages(chat_id):
    try:
        return get_all("""
            SELECT id, message, sent_at, chat_id
            FROM messages
            WHERE chat_id = %s
            ORDER BY sent_at ASC
        """, (chat_id,))
    except Exception as e:
        print(f"Error fetching messages: {e}")
        return []

def get_messages_after(chat_id, last_id):
    return get_all("""
        SELECT id, message, sent_at, sender_id
        FROM messages
        WHERE chat_id = %s AND id > %s
        ORDER BY id ASC
    """, (chat_id, last_id))

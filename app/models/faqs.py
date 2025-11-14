# models/faq.py
from models.db import execute, get_one, get_all
from datetime import datetime
import psycopg2

def get_faqs():
    try:
        faqs = get_all("""
            SELECT id, question, answer, created_at
            FROM faqs
            ORDER BY created_at DESC
        """)
        return faqs
    except Exception as e:
        print(f"Error fetching FAQs: {e}")
        return "Error fetching FAQs."


def create_faq(question, answer):
    try:
        execute("""
            INSERT INTO faqs (question, answer)
            VALUES (%s, %s)
        """, (question, answer))
    except psycopg2.errors.CheckViolation:
        return "Question and answer cannot be empty."

    except psycopg2.errors.StringDataRightTruncation:
        return "Invalid input length. Please check your question and answer."

    except Exception as e:
        print(f"Error creating FAQ: {e}")
        return "Unknown error while creating FAQ."


def delete_faq(faq_id):
    try:
        execute("""
            DELETE FROM faqs
            WHERE id = %s
        """, (faq_id,))
    except Exception as e:
        print(f"Error deleting FAQ: {e}")
        return "Error deleting FAQ."

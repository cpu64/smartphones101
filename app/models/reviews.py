# models/reviews.py
from models.db import execute, get_one, get_all
from datetime import datetime
import psycopg2

def get_reviews():
    try:
        reviews = get_all("""
            SELECT r.id, r.review_text, r.rating, r.created_at,
                   u.username AS user_name,
                   c.username AS consultant_name
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            JOIN users c ON r.consultant_id = c.id
            ORDER BY r.created_at DESC
        """)
        return reviews
    except Exception as e:
        print(f"Error fetching reviews: {e}")
        return "Error fetching reviews."

def get_popular_consultants(limit=None):
    try:
        query = """
            SELECT
                c.id AS consultant_id,
                c.username AS consultant_name,
                COUNT(r.id) AS review_count,
                ROUND(AVG(r.rating)::numeric, 2) AS average_rating
            FROM users c
            JOIN reviews r ON r.consultant_id = c.id
            WHERE c.role = 'consultant'
            GROUP BY c.id, c.username
            HAVING COUNT(r.id) > 0
            ORDER BY average_rating DESC, review_count DESC
        """

        if limit:
            query += " LIMIT %s"
            return get_all(query, (limit,))

        return get_all(query)

    except Exception as e:
        print(f"Error fetching popular consultants: {e}")
        return []


def create_review(review_text, rating, user_id, consultant_id):
    """Insert a new review."""
    try:
        execute("""
            INSERT INTO reviews (review_text, rating, user_id, consultant_id)
            VALUES (%s, %s, %s, %s)
        """, (review_text, rating, user_id, consultant_id))
        return "Review created successfully."

    except psycopg2.errors.UniqueViolation:
        return "You have already reviewed this consultant."

    except psycopg2.errors.CheckViolation:
        return "Rating must be between 1 and 5."

    except psycopg2.errors.ForeignKeyViolation:
        return "Invalid user or consultant ID."

    except psycopg2.errors.StringDataRightTruncation:
        return "Invalid input length. Please check your review text."

    except Exception as e:
        print(f"Error creating review: {e}")
        return "Unknown error while creating review."


def delete_review(review_id):
    """Delete a review by ID."""
    try:
        execute("""
            DELETE FROM reviews
            WHERE id = %s
        """, (review_id,))
        return "Review deleted successfully."

    except Exception as e:
        print(f"Error deleting review: {e}")
        return "Error deleting review."

def allow_review(user_id, consultant_id):
    execute("""
        INSERT INTO can_review (user_id, consultant_id)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
    """, (user_id, consultant_id))


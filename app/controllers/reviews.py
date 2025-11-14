# controllers/reviews.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.reviews import get_reviews, create_review, allow_review, get_popular_consultants
from models.db import get_one, execute

reviews_bp = Blueprint('reviews', __name__)


# ---------------------------------------------------------
# Show all reviews
# ---------------------------------------------------------
@reviews_bp.route('/reviews', methods=['GET'])
def reviews():
    data = {
        "role": session.get("role", "guest"),
        "reviews": get_reviews(),
        "popular_consultants": get_popular_consultants()
    }
    return render_template('reviews.html', data=data)



# ---------------------------------------------------------
# Create review (GET)
# ---------------------------------------------------------
@reviews_bp.route('/create_review', methods=['GET'])
def create_review_page():
    user_id = session.get("user_id")
    role = session.get("role")

    if role != "user":
        flash("Only users can leave reviews.", "error")
        return redirect(url_for("reviews.reviews"))

    # Check permission
    can = get_one("""
        SELECT * FROM can_review
        WHERE user_id = %s
    """, (user_id,))

    if not can:
        flash("You cannot leave a review at this time.", "error")
        return redirect(url_for("reviews.reviews"))

    # Load consultant
    consultant = get_one("""
        SELECT id, username
        FROM users
        WHERE id = %s
    """, (can["consultant_id"],))

    data = {
        "consultant": consultant
    }

    return render_template('create_review.html', data=data)



# ---------------------------------------------------------
# Create review (POST)
# ---------------------------------------------------------
@reviews_bp.route('/create_review', methods=['POST'])
def create_review_post():
    user_id = session.get("user_id")
    role = session.get("role")

    if role != "user":
        flash("You cannot leave a review.", "error")
        return redirect(url_for("reviews.reviews"))

    review_text = request.form.get("review_text", "").strip()
    rating = request.form.get("rating", "")
    consultant_id = request.form.get("consultant_id")

    # Check permission
    can = get_one("""
        SELECT * FROM can_review
        WHERE user_id = %s AND consultant_id = %s
    """, (user_id, consultant_id))

    if not can:
        flash("You cannot leave another review for this consultant.", "error")
        return redirect(url_for("reviews.reviews"))

    # Create review
    result = create_review(review_text, rating, user_id, consultant_id)

    # Remove permission if successful
    if result == "Review created successfully.":
        execute("""
            DELETE FROM can_review
            WHERE user_id = %s AND consultant_id = %s
        """, (user_id, consultant_id))

        flash("Review submitted!", "success")
        return redirect(url_for("reviews.reviews"))

    flash(result, "error")
    return redirect(url_for("reviews.reviews"))

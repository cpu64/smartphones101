# controllers/chat.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from datetime import datetime, timezone

from models.chat import get_or_create_chat, delete_chat, get_chat_pair
from models.messages import get_messages
from models.reviews import allow_review
from models.db import get_one, get_all, execute

chat_bp = Blueprint('chat', __name__)

# ---------------------------------------------------------
# Correct time-slot checker
# ---------------------------------------------------------
def get_current_slot():
    return 1, 1
    now = datetime.now(timezone.utc).astimezone()
    weekday = now.weekday()  # Monday=0
    if weekday not in (0, 1, 2):
        return None, None  # only Mon–Wed

    day = weekday + 1

    hour_of_day = now.hour
    if 8 <= hour_of_day <= 12:
        hour = hour_of_day - 7        # 8→1 … 12→5
    elif 13 <= hour_of_day <= 17:
        hour = hour_of_day - 8        # 13→5 … 17→9
    else:
        return None, None

    return day, hour


# ---------------------------------------------------------
# Main chat page
# ---------------------------------------------------------
@chat_bp.route('/chat', methods=['GET'])
def chat():
    role = session.get("role", "guest")
    user_id = session.get("user_id")
    username = session.get("username")

    if role not in ("user", "consultant"):
        flash("Only logged-in users or consultants can access chat.", "error")
        return redirect(url_for("login.login"))

    # Determine current time slot
    day, hour = get_current_slot()
    if not day:
        flash("There are no active consulting sessions right now.", "error")
        return redirect(url_for("timetables.timetables"))

    # Find scheduled pair
    pair = get_chat_pair(day, hour, user_id, role)
    if not pair:
        flash("This time slot is not booked.", "error")
        return redirect(url_for("timetables.timetables"))

    scheduled_user = pair["user"]
    scheduled_consultant = pair["consultant"]

    # Verify membership
    if role == "user" and scheduled_user["id"] != user_id:
        flash("You have no scheduled consultation at this time.", "error")
        return redirect(url_for("timetables.timetables"))

    if role == "consultant" and scheduled_consultant["id"] != user_id:
        flash("You have no scheduled consultation at this time.", "error")
        return redirect(url_for("timetables.timetables"))

    # Ensure chat record exists
    chat_id = get_or_create_chat(
        scheduled_user["id"],
        scheduled_consultant["id"]
    )

    if isinstance(chat_id, str):
        flash(chat_id, "error")
        return redirect(url_for("timetables.timetables"))

    data = {
        "role": role,
        "username": username,
        "chat_id": chat_id,
        "user_id": user_id,
        "user": scheduled_user,
        "consultant": scheduled_consultant
    }


    return render_template("chat.html", data=data)


# ---------------------------------------------------------
# Send message (AJAX)
# ---------------------------------------------------------
@chat_bp.route('/chat/send', methods=['POST'])
def send_message():

    role = session.get("role", "guest")
    user_id = session.get("user_id")

    if role not in ("user", "consultant"):
        return jsonify({"success": False, "error": "Not allowed"}), 403

    chat_id = request.form.get("chat_id")
    message = request.form.get("message", "").strip()

    if not chat_id or not chat_id.isdigit():
        return jsonify({"success": False, "error": "Invalid chat ID"}), 400

    if not message:
        return jsonify({"success": False, "error": "Empty message"}), 400

    chat_id = int(chat_id)

    # Check membership
    chat_row = get_one("""
        SELECT user_id, consultant_id
        FROM chat WHERE id = %s
    """, (chat_id,))

    if not chat_row or user_id not in (chat_row["user_id"], chat_row["consultant_id"]):
        return jsonify({"success": False, "error": "Forbidden"}), 403

    # Insert message
    msg = get_one("""
        INSERT INTO messages (message, chat_id, sender_id)
        VALUES (%s, %s, %s)
        RETURNING id, sent_at
    """, (message, chat_id, user_id))

    return jsonify({
        "success": True,
        "id": msg["id"],
        "sent_at": msg["sent_at"].strftime("%H:%M")
    })


# ---------------------------------------------------------
# Poll new messages
# ---------------------------------------------------------
@chat_bp.route("/chat/poll/<int:chat_id>", methods=["GET"])
def poll_chat(chat_id):
    user_id = session.get("user_id")
    role = session.get("role", "guest")

    if role not in ("user", "consultant") or not user_id:
        return jsonify({"messages": []})

    after_id = request.args.get("after", "0")
    after_id = int(after_id) if after_id.isdigit() else 0

    # Check membership
    chat_row = get_one("""
        SELECT user_id, consultant_id
        FROM chat WHERE id = %s
    """, (chat_id,))

    if not chat_row or user_id not in (chat_row["user_id"], chat_row["consultant_id"]):
        return jsonify({"messages": []})

    msgs = get_all("""
        SELECT id, message, sent_at,
        CASE WHEN sender_id = %s THEN TRUE ELSE FALSE END AS is_mine
        FROM messages
        WHERE chat_id = %s AND id > %s
        ORDER BY id ASC
    """, (user_id, chat_id, after_id))

    for m in msgs:
        m["sent_at"] = m["sent_at"].strftime("%H:%M")

    return jsonify({"messages": msgs})


# ---------------------------------------------------------
# Leave chat manually
# ---------------------------------------------------------
@chat_bp.route("/chat/leave", methods=["POST"])
def leave_chat():
    user_id = session.get("user_id")
    role = session.get("role", "guest")

    if role not in ("user", "consultant"):
        flash("Not allowed.", "error")
        return redirect(url_for("login.login"))

    chat_id = request.form.get("chat_id")

    if not chat_id or not chat_id.isdigit():
        flash("Invalid chat.", "error")
        return redirect(url_for("timetables.timetables"))

    chat_id = int(chat_id)

    chat_row = get_one("""
        SELECT user_id, consultant_id
        FROM chat WHERE id = %s
    """, (chat_id,))

    if not chat_row:
        flash("Chat does not exist.", "error")
        return redirect(url_for("timetables.timetables"))

    if user_id not in (chat_row["user_id"], chat_row["consultant_id"]):
        flash("You cannot exit this chat.", "error")
        return redirect(url_for("timetables.timetables"))

    # Free slot
    day, hour = get_current_slot()
    if day:
        execute("""
            UPDATE users
            SET timetable[%s][%s] = NULL
            WHERE id = %s
        """, (day, hour, chat_row["consultant_id"]))

    allow_review(chat_row["user_id"], chat_row["consultant_id"])

    delete_chat(chat_id)

    if role == "user":
        flash("Chat ended. You can now leave a review.", "success")
        return redirect(url_for("reviews.create_review_page", consultant_id=chat_row["consultant_id"]))
    return redirect(url_for("timetables.timetables"))



# ---------------------------------------------------------
# Auto-expire chat (polled every second)
# ---------------------------------------------------------
@chat_bp.route("/chat/check_active/<int:chat_id>")
def check_active(chat_id):

    user_id = session.get("user_id")
    role = session.get("role", "guest")

    if role not in ("user", "consultant") or not user_id:
        return jsonify({"active": False})

    chat_row = get_one("""
        SELECT user_id, consultant_id
        FROM chat WHERE id = %s
    """, (chat_id,))

    if not chat_row:
        return jsonify({"active": False})

    if user_id not in (chat_row["user_id"], chat_row["consultant_id"]):
        return jsonify({"active": False})

    # Current slot
    day, hour = get_current_slot()

    if not day:
        # Allow one review
        allow_review(chat_row["user_id"], chat_row["consultant_id"])

        delete_chat(chat_id)
        return jsonify({"active": False})


    # Check consultant's timetable slot
    scheduled = get_one("""
        SELECT timetable[%s][%s] AS u
        FROM users
        WHERE id = %s
    """, (day, hour, chat_row["consultant_id"]))

    if not scheduled or scheduled["u"] != chat_row["user_id"]:
        allow_review(chat_row["user_id"], chat_row["consultant_id"])
        delete_chat(chat_id)
        return jsonify({"active": False})


    return jsonify({"active": True})

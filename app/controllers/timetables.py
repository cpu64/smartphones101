# controllers/timetables.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.users import get_consultants, reserve_slot, cancel_slot
from .chat import get_current_slot

timetables_bp = Blueprint('timetables', __name__)

@timetables_bp.route('/timetables', methods=['GET', 'POST'])
def timetables():
    if request.method == 'GET':
        data = {}
        data["timeslot"] = get_current_slot()
        data["role"] = session.get('role', 'guest')
        data["consultants"] = get_consultants()
        return render_template('timetables.html', data=data)

    elif request.method == 'POST':
        username = session.get('username')
        role = session.get('role', 'guest')
        if not username or role != 'user':
            flash("You must be logged in as user to reserve or cancel a slot.", "error")
            return redirect(url_for('login.login'))

        consultant_id = request.form.get("consultant_id")
        day = request.form.get("day")
        hour = request.form.get("hour")
        action = request.form.get("action")

        if not consultant_id or not day or not hour or not action:
            flash("Invalid form submission.", "error")
            return redirect(url_for('timetables.timetables'))

        try:
            day = int(day)
            hour = int(hour)
        except ValueError:
            flash("Invalid time slot selection.", "error")
            return redirect(url_for('timetables.timetables'))

        # Perform reservation or cancellation
        if action == "reserve":
            if (err := reserve_slot(consultant_id, username, day, hour)):
                flash(f"{err}", "error")
            else:
                flash(f"Time slot reserved successfully.", "success")
        elif action == "cancel":
            if (err := cancel_slot(consultant_id, username, day, hour)):
                flash(f"{err}", "error")
            else:
                flash(f"Time slot canceled successfully.", "success")
        else:
            flash("Invalid action.", "error")

        return redirect(url_for('timetables.timetables'))


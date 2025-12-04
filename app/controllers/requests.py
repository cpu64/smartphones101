# controllers/requests.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.requests import get_requests, create_request, delete_request, approve_all
from models.users import add_credits

requests_bp = Blueprint('requests', __name__)

@requests_bp.route('/requests', methods=['GET', 'POST'])
def requests():
    role = session.get('role', 'guest')
    username = session.get('username')

    if request.method == 'GET':
        data = {}
        data["role"] = role

        if role == 'admin':
            # Admin sees all requests
            data["requests"] = get_requests()
        elif role == 'user':
            # User sees only their own requests
            all_requests = get_requests()
            user_id = session.get("user_id")
            data["requests"] = [r for r in all_requests if r["user_id"] == user_id]
        else:
            flash(f"You do not have permisions to access that page.", "error")
            return redirect(url_for('timetables.timetables'))

        return render_template('requests.html', data=data)

    if request.method == 'POST':

        action = request.form.get("action")

        if action == "create":
            if role != "user":
                flash("Only users can request credits.", "error")
                return redirect(url_for('requests.requests'))

            amount = request.form.get("amount")
            user_id = session.get("user_id")

            if not amount or not amount.isdigit():
                flash("Amount must be a positive number.", "error")
                return redirect(url_for('requests.requests'))

            amount = int(amount)
            if amount <= 0:
                flash("Amount must be positive.", "error")
                return redirect(url_for('requests.requests'))

            err = create_request(user_id, amount)
            if err:
                flash(err, "error")
            else:
                flash("Request submitted successfully.", "success")

            return redirect(url_for('requests.requests'))

        if action == "approve-all":
            if role != "admin":
                flash("Only admins can approve requests.", "error")
                return redirect(url_for('requests.requests'))

            err = approve_all()
            if err:
                flash(err, "error")
            else:
                flash("Requests approved and credits added.", "success")

            return redirect(url_for('requests.requests'))

        if action == "approve":
            if role != "admin":
                flash("Only admins can approve requests.", "error")
                return redirect(url_for('requests.requests'))

            req_id = request.form.get("request_id")
            username = request.form.get("username")
            amount = request.form.get("amount")

            err = add_credits(username, amount)
            if err:
                flash(err, "error")
            else:
                delete_request(req_id)
                flash("Request approved and credits added.", "success")

            return redirect(url_for('requests.requests'))

        if action == "deny":
            if role != "admin":
                flash("Only admins can deny requests.", "error")
                return redirect(url_for('requests.requests'))

            req_id = request.form.get("request_id")

            err = delete_request(req_id)
            if err:
                flash(err, "error")
            else:
                flash("Request denied and removed.", "success")

            return redirect(url_for('requests.requests'))

        flash("Unknown action.", "error")
        return redirect(url_for('requests.requests'))

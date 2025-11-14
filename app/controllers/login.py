# controllers/login.py
import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.users import check_length, get_credentials

login_bp = Blueprint('login', __name__)

@login_bp.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('role', 'guest') != 'guest':
        return redirect(url_for('timetables.timetables'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if (err := check_length('username', username)):
            flash(f"Username must be between {err} characters.", "error")
            return render_template('login.html')

        if (err := check_length('password', password)):
            flash(f"Password must be between {err} characters.", "error")
            return render_template('login.html')

        response = get_credentials(username)

        if isinstance(response, str):
            flash(response, "error")
            return render_template('login.html')

        password_is_valid = bcrypt.checkpw(password.encode('utf-8'), response['password'].encode('utf-8'))

        if password_is_valid:
            session['username'] = username
            session['role'] = response['role']
            session['user_id'] = response['id']
            return redirect(url_for('timetables.timetables'))
        else:
            flash("Invalid credentials, please try again.", "error")

    return render_template('login.html')

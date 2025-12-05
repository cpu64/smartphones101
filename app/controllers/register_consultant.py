# controllers/register_consultant.py
import bcrypt
from flask import Blueprint, request, redirect, url_for, flash, render_template, session
from models.users import check_length, register_user

register_consultant_bp = Blueprint('register_consultant', __name__)

@register_consultant_bp.route('/register_consultant', methods=['GET', 'POST'])
def register_consultant():
    if session.get('role', 'guest') != 'admin':
        flash(f"You do not have permisions to access that page.", "error")
        return redirect(url_for('timetables.timetables'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        if (err := check_length('username', username)):
            flash(f"Username must be between {err} characters.", "error")
            return render_template('register_consultant.html')

        if (err := check_length('password', password)):
            flash(f"Password must be between {err} characters.", "error")
            return render_template('register_consultant.html')

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        if (err := register_user(username, hashed, email, 'consultant')):
            flash(err, "error")
        else:
            flash("Consultant creation successful!", "success")
            return render_template('register_consultant.html')

    return render_template('register_consultant.html')

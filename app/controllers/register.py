# controllers/register.py
import bcrypt
from flask import Blueprint, request, redirect, url_for, flash, render_template
from models.users import check_length, register_user

register_bp = Blueprint('register', __name__)

@register_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if (err := check_length('username', username)):
            flash(f"Username must be between {err} characters.", "error")
            return render_template('register.html')

        if (err := check_length('password', password)):
            flash(f"Password must be between {err} characters.", "error")
            return render_template('register.html')

        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        if (err := register_user(username, hashed)):
            flash(err, "error")
        else:
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login.login'))

    return render_template('register.html')

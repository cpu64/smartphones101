# controllers/logout.py
from flask import Blueprint, session, redirect, url_for, flash

logout_bp = Blueprint('logout', __name__)

@logout_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    if session.get('role', '') != 'guest':
        session.clear()
        flash("Logged out successfully.", 'success')
    else:
        flash("You are not logged in.", 'info')
    return redirect(url_for('login.login'))

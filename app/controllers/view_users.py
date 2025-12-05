# controllers/view_users.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.users import get_users

view_users_bp = Blueprint('view_users', __name__)

@view_users_bp.route('/view_users', methods=['GET'])
def view_users():
    if session.get('role', 'guest') != 'admin':
        flash(f"You do not have permisions to access that page.", "error")
        return redirect(url_for('timetables.timetables'))
    data = get_users()
    return render_template('view_users.html', data=data)

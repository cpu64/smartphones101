# controllers/faq.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.faqs import get_faqs, delete_faq, create_faq

faq_bp = Blueprint('faq', __name__)

@faq_bp.route('/faq', methods=['GET', 'POST'])
def faq():
    if request.method == 'GET':
        data = {}
        data["role"] = session.get('role', 'guest')
        data["faqs"] = get_faqs()
        return render_template('faq.html', data=data)
    elif request.method == 'POST':
        if session.get('role', 'guest') != 'admin':
            flash(f"You do not have permisions to access that page.", "error")
            return redirect(url_for('timetables.timetables'))

        delete_id = request.form.get('delete_id')
        if delete_id:
            if (err := delete_faq(delete_id)):
                flash(f"{err}", "error")
            else:
                flash(f"FAQ deleted successfully.", "success")

        question = request.form.get('question')
        answer = request.form.get('answer')
        if question and answer:
            if (err := create_faq(question, answer)):
                flash(f"{err}", "error")
            else:
                flash(f"FAQ created successfully.", "success")

        return redirect(url_for('faq.faq'))

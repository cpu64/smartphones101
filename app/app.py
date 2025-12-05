# app.py
from flask import Flask, redirect, url_for, session, flash
from models.db import init_db
from models.users import get_credits
from controllers.faq import faq_bp
from controllers.view_users import view_users_bp
from controllers.chat import chat_bp
from controllers.login import login_bp
from controllers.logout import logout_bp
from controllers.reviews import reviews_bp
from controllers.register import register_bp
from controllers.requests import requests_bp
from controllers.timetables import timetables_bp
from controllers.register_consultant import register_consultant_bp
import secrets
import os

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

app.register_blueprint(faq_bp)
app.register_blueprint(view_users_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(login_bp)
app.register_blueprint(logout_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(register_bp)
app.register_blueprint(requests_bp)
app.register_blueprint(timetables_bp)
app.register_blueprint(register_consultant_bp)

@app.before_request
def ensure_default_session():
    if 'role' not in session:
        session['role'] = 'guest'
    if session['role'] == 'user':
        session['credits'] = get_credits(session['username'])

@app.route('/')
def index():
    return redirect(url_for('timetables.timetables'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host=os.getenv('FALSK_HOST', '0.0.0.0'), port=os.getenv('FALSK_PORT', '5000'))


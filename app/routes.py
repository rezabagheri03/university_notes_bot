from flask import Blueprint, redirect, url_for

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return redirect(url_for('admin.login'))

@main.route('/favicon.ico')
def favicon():
    return '', 204  # No content response for favicon requests 
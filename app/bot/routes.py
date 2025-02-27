from flask import Blueprint, jsonify, request
from . import bp

@bp.route('/webhook', methods=['POST'])
def webhook():
    return jsonify({'status': 'ok'}) 
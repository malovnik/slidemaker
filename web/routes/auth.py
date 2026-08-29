# -*- coding: utf-8 -*-
"""
Маршруты авторизации.
"""

from secrets import compare_digest

from flask import Blueprint, render_template, request, redirect, url_for, session

from web.config import get_config

config = get_config()

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Страница авторизации."""
    # Пин не задан — вход не нужен
    if not config.PIN_CODE:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        pin = request.form.get('pin', '')
        if compare_digest(pin, config.PIN_CODE):
            session['authenticated'] = True
            return redirect(url_for('main.index'))
        return render_template('login.html', error='Неверный пин-код')
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """Выход из системы."""
    session.pop('authenticated', None)
    return redirect(url_for('auth.login'))

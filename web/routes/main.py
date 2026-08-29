# -*- coding: utf-8 -*-
"""
Основные маршруты приложения.
"""

from flask import Blueprint, render_template, send_from_directory

from web.config import get_config
from web.utils import require_pin
from web.services import SettingsService, FontsService, BackgroundsService

config = get_config()

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@require_pin
def index():
    """Главная страница."""
    settings = SettingsService.load()
    fonts = FontsService.get_available()
    backgrounds = BackgroundsService.get_available()
    
    return render_template(
        'index.html',
        settings=settings,
        fonts=fonts,
        backgrounds=backgrounds,
        auth_enabled=bool(config.PIN_CODE)
    )


@main_bp.route('/uploads/backgrounds/<filename>')
@require_pin
def serve_background(filename):
    """Отдаёт загруженные фоны."""
    return send_from_directory(
        str(config.UPLOAD_FOLDER / 'backgrounds'),
        filename
    )


@main_bp.route('/uploads/fonts/<filename>')
@require_pin
def serve_font(filename):
    """Отдаёт загруженные шрифты."""
    return send_from_directory(
        str(config.UPLOAD_FOLDER / 'fonts'),
        filename
    )


@main_bp.route('/static/<path:filename>')
def serve_static(filename):
    """Отдаёт статические файлы."""
    return send_from_directory(
        str(config.BASE_DIR / 'static'),
        filename
    )

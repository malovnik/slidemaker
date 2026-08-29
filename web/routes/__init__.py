# -*- coding: utf-8 -*-
"""
Маршруты приложения.
Использует Flask Blueprints для модульной организации.
"""

from flask import Flask

from web.routes.auth import auth_bp
from web.routes.main import main_bp
from web.routes.api import api_bp


def register_blueprints(app: Flask) -> None:
    """
    Регистрирует все blueprints в приложении.
    
    Args:
        app: Flask приложение
    """
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

# -*- coding: utf-8 -*-
"""
Flask приложение для генерации презентаций из Markdown.

Архитектура:
- config.py      — конфигурация
- utils.py       — утилиты и декораторы
- routes/        — HTTP маршруты (Blueprints)
- services/      — бизнес-логика
"""

import os
import sys
from pathlib import Path

# Ensure parent directory is in Python path (for Railway deployment)
_app_root = str(Path(__file__).parent.parent.absolute())
if _app_root not in sys.path:
    sys.path.insert(0, _app_root)

from flask import Flask

from web.config import get_config
from web.utils import ensure_directories, cleanup_old_files
from web.routes import register_blueprints


def create_app(config_class=None):
    """
    Application Factory.
    
    Args:
        config_class: Класс конфигурации (опционально)
        
    Returns:
        Flask приложение
    """
    app = Flask(__name__)
    
    # Загружаем конфигурацию
    config = config_class or get_config()
    app.config.from_object(config)
    app.secret_key = config.SECRET_KEY
    
    # Создаём директории
    ensure_directories()
    
    # Регистрируем blueprints
    register_blueprints(app)
    
    return app


# Для запуска напрямую (python app.py)
if __name__ == '__main__':
    # Очищаем старые файлы
    cleanup_old_files()
    
    # Создаём приложение
    app = create_app()
    
    # Запускаем
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    
    app.run(host='0.0.0.0', port=port, debug=debug)

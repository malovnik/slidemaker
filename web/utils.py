# -*- coding: utf-8 -*-
"""
Утилиты и декораторы.
"""

import os
import uuid
import shutil
from datetime import datetime, timedelta
from functools import wraps
from flask import session, redirect, url_for, request, jsonify
from werkzeug.utils import secure_filename

from web.config import get_config

config = get_config()


def require_pin(f):
    """Декоратор для проверки авторизации по пин-коду.

    Если PIN_CODE не задан, приложение работает без входа — так удобнее
    запускать его локально на своём компьютере.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if config.PIN_CODE and not session.get('authenticated'):
            if request.is_json:
                return jsonify({'error': 'Требуется авторизация'}), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_safe_filename(filename: str) -> str:
    """
    Генерирует безопасное уникальное имя файла.
    
    Args:
        filename: Оригинальное имя файла
        
    Returns:
        Безопасное имя с UUID префиксом
    """
    safe_name = secure_filename(filename)
    if not safe_name:
        safe_name = 'file'
    
    name, ext = os.path.splitext(safe_name)
    unique_name = f"{uuid.uuid4().hex[:8]}_{name}{ext}"
    return unique_name


def is_allowed_extension(filename: str, allowed: set) -> bool:
    """
    Проверяет, разрешено ли расширение файла.
    
    Args:
        filename: Имя файла
        allowed: Множество разрешённых расширений
        
    Returns:
        True если расширение разрешено
    """
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed


def ensure_directories():
    """Создаёт необходимые директории если их нет."""
    for folder in [config.UPLOAD_FOLDER, config.GENERATED_FOLDER]:
        os.makedirs(folder, exist_ok=True)
    
    for subdir in config.UPLOAD_SUBDIRS:
        os.makedirs(config.UPLOAD_FOLDER / subdir, exist_ok=True)


def cleanup_old_files():
    """Удаляет старые сгенерированные файлы."""
    if not config.GENERATED_FOLDER.exists():
        return
    
    cutoff = datetime.now() - timedelta(hours=config.FILE_CLEANUP_HOURS)
    
    for filename in os.listdir(config.GENERATED_FOLDER):
        filepath = config.GENERATED_FOLDER / filename
        if filepath.is_file():
            file_time = datetime.fromtimestamp(filepath.stat().st_mtime)
            if file_time < cutoff:
                try:
                    filepath.unlink()
                except OSError:
                    pass

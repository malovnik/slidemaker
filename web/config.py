# -*- coding: utf-8 -*-
"""
Конфигурация приложения.
Все настройки в одном месте для удобного управления.
"""

import os
import secrets
from pathlib import Path


class Config:
    """Базовая конфигурация."""
    
    # Пути
    BASE_DIR = Path(__file__).parent
    ROOT_DIR = BASE_DIR.parent
    
    UPLOAD_FOLDER = BASE_DIR / 'uploads'
    GENERATED_FOLDER = BASE_DIR / 'generated'
    FONTS_FOLDER = ROOT_DIR / 'fonts'
    SETTINGS_FILE = BASE_DIR / 'user_settings.json'
    
    # Поддиректории uploads
    UPLOAD_SUBDIRS = ['backgrounds', 'fonts', 'markdown']
    
    # Ключ подписи сессий. Без переменной окружения генерируется случайный
    # при каждом старте: локально это безопасно, а на сервере задайте SECRET_KEY,
    # иначе при перезапуске все сессии слетят.
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

    # Пин-код на вход. Пусто — вход свободный (режим локального запуска).
    # Публикуете приложение в интернет — обязательно задайте PIN_CODE.
    PIN_CODE = os.environ.get('PIN_CODE', '').strip()

    # Максимальный размер загружаемого файла
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_MB', '32')) * 1024 * 1024
    
    # Разрешённые расширения файлов
    ALLOWED_MD_EXTENSIONS = {'.md', '.markdown', '.txt'}
    ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg'}
    ALLOWED_FONT_EXTENSIONS = {'.ttf', '.otf'}
    
    # Дефолтные настройки презентации
    DEFAULT_SETTINGS = {
        'font_name': 'Montserrat',
        'heading_color': 'e8e6e3',
        'text_color': 'b8b6b3',
        'heading_gradient': 'no',
        'heading_gradient_end': 'e8e6e3',
        'text_gradient': 'no',
        'text_gradient_end': 'b8b6b3',
        'bg_effect': 'none',
        'bg_effect_intensity': 0
    }
    
    # Время жизни файлов (в часах)
    FILE_CLEANUP_HOURS = 24


class DevelopmentConfig(Config):
    """Конфигурация для разработки."""
    DEBUG = True


class ProductionConfig(Config):
    """Конфигурация для продакшена."""
    DEBUG = False


# Выбор конфигурации по переменной окружения
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Получить текущую конфигурацию."""
    env = os.environ.get('FLASK_ENV', 'default')
    return config_map.get(env, DevelopmentConfig)

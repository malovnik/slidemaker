# -*- coding: utf-8 -*-
"""
Сервис работы с фоновыми изображениями.
"""

import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from werkzeug.datastructures import FileStorage

from web.config import get_config
from web.utils import get_safe_filename, is_allowed_extension

config = get_config()


class BackgroundsService:
    """Сервис для работы с фоновыми изображениями."""
    
    @staticmethod
    def get_available() -> List[Dict[str, str]]:
        """
        Получить список доступных фонов.
        
        Returns:
            Список словарей с информацией о фонах
        """
        backgrounds = []
        bg_folder = config.UPLOAD_FOLDER / 'backgrounds'

        # Добавляем стандартный фон (ищем с разными расширениями)
        default_bg_found = False
        for ext in ['.png', '.jpg', '.jpeg']:
            default_bg = config.ROOT_DIR / f'bg{ext}'
            if default_bg.exists():
                backgrounds.append({
                    'name': 'По умолчанию',
                    'path': 'default',
                    'file': f'bg{ext}'
                })
                default_bg_found = True
                break
        
        # Пользовательские фоны
        if bg_folder.exists():
            for file in os.listdir(bg_folder):
                ext = os.path.splitext(file)[1].lower()
                if ext in config.ALLOWED_IMAGE_EXTENSIONS:
                    backgrounds.append({
                        'name': os.path.splitext(file)[0],
                        'path': file,
                        'file': file
                    })
        
        return backgrounds
    
    @staticmethod
    def upload(file: FileStorage) -> Tuple[bool, str, Optional[str]]:
        """
        Загрузить фоновое изображение.
        
        Args:
            file: Загружаемый файл
            
        Returns:
            Tuple (успех, сообщение/имя_файла, имя или None)
        """
        if not file or file.filename == '':
            return False, 'Файл не выбран', None
        
        if not is_allowed_extension(file.filename, config.ALLOWED_IMAGE_EXTENSIONS):
            allowed = ', '.join(config.ALLOWED_IMAGE_EXTENSIONS)
            return False, f'Неподдерживаемый формат. Разрешены: {allowed}', None
        
        filename = get_safe_filename(file.filename)
        filepath = config.UPLOAD_FOLDER / 'backgrounds' / filename
        file.save(str(filepath))
        
        name = os.path.splitext(file.filename)[0]
        return True, filename, name
    
    @staticmethod
    def get_background_path(bg_value: str) -> Optional[Path]:
        """
        Получить путь к фоновому изображению.
        
        Args:
            bg_value: Значение фона ('default' или имя файла)
            
        Returns:
            Path к файлу или None
        """
        if bg_value == 'default':
            # Ищем дефолтный фон
            for ext in ['.png', '.jpg', '.jpeg']:
                default_path = config.ROOT_DIR / f'bg{ext}'
                if default_path.exists():
                    return default_path
            return None
        
        # Пользовательский фон
        bg_path = config.UPLOAD_FOLDER / 'backgrounds' / bg_value
        if bg_path.exists():
            return bg_path
        
        return None

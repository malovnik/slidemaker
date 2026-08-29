# -*- coding: utf-8 -*-
"""
Сервис работы с настройками пользователя.
"""

import json
from pathlib import Path
from typing import Dict, Any

from web.config import get_config

config = get_config()


class SettingsService:
    """Сервис для работы с настройками презентации."""
    
    @staticmethod
    def get_default() -> Dict[str, Any]:
        """Получить дефолтные настройки."""
        return config.DEFAULT_SETTINGS.copy()
    
    @staticmethod
    def load() -> Dict[str, Any]:
        """
        Загрузить настройки из файла.
        
        Returns:
            Словарь с настройками (дефолтные если файл не существует)
        """
        settings_file = Path(config.SETTINGS_FILE)
        
        if settings_file.exists():
            try:
                with open(settings_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    # Мержим с дефолтными чтобы новые поля тоже были
                    default = SettingsService.get_default()
                    default.update(saved)
                    return default
            except (json.JSONDecodeError, IOError):
                pass
        
        return SettingsService.get_default()
    
    @staticmethod
    def save(settings: Dict[str, Any]) -> bool:
        """
        Сохранить настройки в файл.
        
        Args:
            settings: Словарь с настройками
            
        Returns:
            True если успешно сохранено
        """
        try:
            with open(config.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            return True
        except IOError:
            return False

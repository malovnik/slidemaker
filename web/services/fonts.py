# -*- coding: utf-8 -*-
"""
Сервис работы со шрифтами.
"""

import os
import re
from pathlib import Path
from typing import List, Optional, Tuple
from werkzeug.datastructures import FileStorage

from web.config import get_config
from web.utils import get_safe_filename, is_allowed_extension

config = get_config()


class FontsService:
    """Сервис для работы со шрифтами."""

    @staticmethod
    def get_available() -> List[str]:
        """
        Получить список доступных шрифтов.

        Returns:
            Отсортированный список имён шрифтов
        """
        fonts = set()

        # Системные шрифты из папки fonts
        if config.FONTS_FOLDER.exists():
            for file in os.listdir(config.FONTS_FOLDER):
                if file.endswith(('.ttf', '.otf')):
                    font_name = file.rsplit('.', 1)[0]
                    fonts.add(font_name)

        # Пользовательские шрифты
        user_fonts = config.UPLOAD_FOLDER / 'fonts'
        if user_fonts.exists():
            for file in os.listdir(user_fonts):
                if file.endswith(('.ttf', '.otf')):
                    font_name = file.rsplit('.', 1)[0]
                    fonts.add(font_name)

        return sorted(list(fonts))

    @staticmethod
    def normalize_font_name(filename: str) -> str:
        """
        Нормализует имя шрифта из имени файла.
        Убирает спецсимволы, нормализует пробелы.

        Args:
            filename: Имя файла шрифта

        Returns:
            Нормализованное имя шрифта
        """
        # Убираем расширение
        name = os.path.splitext(filename)[0]
        
        # Заменяем подчёркивания и дефисы на пробелы для лучшего отображения
        # Но оставляем суффиксы типа -Regular, -Bold
        # Ищем паттерн FontName-Weight
        match = re.match(r'^(.+?)(-(?:Regular|Bold|Italic|Light|Medium|SemiBold|ExtraBold|ExtraLight|Thin|Black|Heavy).*)$', name, re.IGNORECASE)
        if match:
            base_name = match.group(1)
            weight_suffix = match.group(2)
            # Нормализуем базовое имя
            base_name = re.sub(r'[_\s]+', ' ', base_name).strip()
            return f"{base_name}{weight_suffix}"
        
        # Если нет суффикса веса, просто нормализуем
        name = re.sub(r'[_\s]+', ' ', name).strip()
        return name

    @staticmethod
    def validate_font_file(filepath: Path) -> Tuple[bool, str]:
        """
        Проверяет корректность файла шрифта.

        Args:
            filepath: Путь к файлу шрифта

        Returns:
            Tuple (валиден, сообщение об ошибке)
        """
        try:
            with open(filepath, 'rb') as f:
                # Читаем первые 4 байта для проверки магического числа
                magic = f.read(4)
                
                # TTF: 0x00010000 или 'true' или 'typ1'
                # OTF: 'OTTO'
                valid_magic = [
                    b'\x00\x01\x00\x00',  # TTF
                    b'true',              # TTF (Mac)
                    b'typ1',              # TTF (Type 1)
                    b'OTTO',              # OTF
                ]
                
                if magic not in valid_magic:
                    return False, 'Файл повреждён или не является шрифтом'
                
                return True, ''
        except Exception as e:
            return False, f'Ошибка чтения файла: {str(e)}'
    
    @staticmethod
    def upload(file: FileStorage) -> Tuple[bool, str, Optional[str]]:
        """
        Загрузить пользовательский шрифт.
        
        Args:
            file: Загружаемый файл
            
        Returns:
            Tuple (успех, сообщение/имя_файла, имя_шрифта или None)
        """
        if not file or file.filename == '':
            return False, 'Файл не выбран', None
        
        if not is_allowed_extension(file.filename, config.ALLOWED_FONT_EXTENSIONS):
            allowed = ', '.join(config.ALLOWED_FONT_EXTENSIONS)
            return False, f'Неподдерживаемый формат. Разрешены: {allowed}', None
        
        # Нормализуем имя файла
        original_ext = os.path.splitext(file.filename)[1].lower()
        normalized_name = FontsService.normalize_font_name(file.filename)
        filename = f"{normalized_name}{original_ext}"
        filename = get_safe_filename(filename)
        
        # Создаём папку если не существует
        fonts_dir = config.UPLOAD_FOLDER / 'fonts'
        fonts_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = fonts_dir / filename
        file.save(str(filepath))
        
        # Проверяем корректность шрифта
        is_valid, error_msg = FontsService.validate_font_file(filepath)
        if not is_valid:
            # Удаляем некорректный файл
            try:
                filepath.unlink()
            except OSError:
                pass
            return False, error_msg, None
        
        font_name = os.path.splitext(filename)[0]
        return True, filename, font_name
    
    @staticmethod
    def find_font_file(font_name: str) -> Optional[Path]:
        """
        Найти файл шрифта по имени.
        
        Args:
            font_name: Имя шрифта
            
        Returns:
            Path к файлу шрифта или None
        """
        # Сначала ищем точное совпадение, затем по началу имени
        
        # Пользовательские шрифты
        user_fonts = config.UPLOAD_FOLDER / 'fonts'
        if user_fonts.exists():
            for file in os.listdir(user_fonts):
                if file.endswith(('.ttf', '.otf')):
                    name_without_ext = file.rsplit('.', 1)[0]
                    # Точное совпадение
                    if name_without_ext == font_name:
                        return user_fonts / file
                    # Совпадение по началу (для поиска без суффикса веса)
                    if name_without_ext.startswith(font_name):
                        return user_fonts / file
        
        # Системные шрифты
        if config.FONTS_FOLDER.exists():
            for file in os.listdir(config.FONTS_FOLDER):
                if file.endswith(('.ttf', '.otf')):
                    name_without_ext = file.rsplit('.', 1)[0]
                    if name_without_ext == font_name:
                        return config.FONTS_FOLDER / file
                    if name_without_ext.startswith(font_name):
                        return config.FONTS_FOLDER / file
        
        return None

# -*- coding: utf-8 -*-
"""
Сервис генерации презентаций.
"""

import os
import sys
import base64
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
from werkzeug.datastructures import FileStorage

# Добавляем корень проекта для импорта md_to_slides
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from md_to_slides import MarkdownSlideConverter

from web.config import get_config
from web.utils import get_safe_filename, is_allowed_extension
from web.services.fonts import FontsService
from web.services.backgrounds import BackgroundsService
from web.services.settings import SettingsService

config = get_config()


@dataclass
class PresentationSettings:
    """Настройки для генерации презентации."""
    font_name: str = 'Montserrat'
    text_font_name: str = ''  # Если пусто, используется font_name
    heading_color: str = 'e8e6e3'
    text_color: str = 'b8b6b3'
    accent_color: str = 'ff6b6b'  # Цвет для **bold** текста
    heading_gradient: str = 'no'
    heading_gradient_end: str = 'e8e6e3'
    text_gradient: str = 'no'
    text_gradient_end: str = 'b8b6b3'
    bg_effect: str = 'none'
    bg_effect_intensity: str = '0'
    background: str = 'default'
    format: str = 'horizontal'
    export_format: str = 'pdf'  # pdf, pptx, jpg
    # Size settings
    heading_font_size: int = 50
    heading_width: int = 90
    text_font_size: int = 36
    text_width: int = 85

    @classmethod
    def from_form(cls, form: Dict[str, Any]) -> 'PresentationSettings':
        """Создать из данных формы."""
        defaults = config.DEFAULT_SETTINGS
        return cls(
            font_name=form.get('font_name', defaults['font_name']),
            text_font_name=form.get('text_font_name', ''),
            heading_color=form.get('heading_color', defaults['heading_color']).lstrip('#'),
            text_color=form.get('text_color', defaults['text_color']).lstrip('#'),
            accent_color=form.get('accent_color', 'ff6b6b').lstrip('#'),
            heading_gradient=form.get('heading_gradient', defaults['heading_gradient']),
            heading_gradient_end=form.get('heading_gradient_end', defaults['heading_gradient_end']).lstrip('#'),
            text_gradient=form.get('text_gradient', defaults['text_gradient']),
            text_gradient_end=form.get('text_gradient_end', defaults['text_gradient_end']).lstrip('#'),
            bg_effect=form.get('bg_effect', defaults['bg_effect']),
            bg_effect_intensity=form.get('bg_effect_intensity', str(defaults['bg_effect_intensity'])),
            background=form.get('background', 'default'),
            format=form.get('format', 'horizontal'),
            export_format=form.get('export_format', 'pdf'),
            heading_font_size=int(form.get('heading_font_size', 50)),
            heading_width=int(form.get('heading_width', 90)),
            text_font_size=int(form.get('text_font_size', 36)),
            text_width=int(form.get('text_width', 85))
        )

    def to_dict(self) -> Dict[str, Any]:
        """Конвертировать в словарь для сохранения."""
        return {
            'font_name': self.font_name,
            'text_font_name': self.text_font_name,
            'heading_color': self.heading_color,
            'text_color': self.text_color,
            'accent_color': self.accent_color,
            'heading_gradient': self.heading_gradient,
            'heading_gradient_end': self.heading_gradient_end,
            'text_gradient': self.text_gradient,
            'text_gradient_end': self.text_gradient_end,
            'bg_effect': self.bg_effect,
            'bg_effect_intensity': int(self.bg_effect_intensity),
            'heading_font_size': self.heading_font_size,
            'heading_width': self.heading_width,
            'text_font_size': self.text_font_size,
            'text_width': self.text_width
        }


class PresentationService:
    """Сервис для генерации презентаций из Markdown."""
    
    @staticmethod
    def validate_markdown(file: FileStorage) -> Tuple[bool, str]:
        """
        Проверить markdown файл.
        
        Returns:
            Tuple (валиден, сообщение об ошибке)
        """
        if not file or file.filename == '':
            return False, 'Файл не выбран'
        
        if not is_allowed_extension(file.filename, config.ALLOWED_MD_EXTENSIONS):
            allowed = ', '.join(config.ALLOWED_MD_EXTENSIONS)
            return False, f'Неподдерживаемый формат. Разрешены: {allowed}'
        
        return True, ''
    
    @staticmethod
    def generate(
        md_file: FileStorage,
        settings: PresentationSettings
    ) -> Tuple[bool, str, Optional[str], Optional[str]]:
        """
        Сгенерировать презентацию.

        Args:
            md_file: Markdown файл
            settings: Настройки презентации

        Returns:
            Tuple (успех, сообщение, имя_файла, base64_data)
        """
        # Сохраняем markdown файл
        md_filename = get_safe_filename(md_file.filename)
        md_path = config.UPLOAD_FOLDER / 'markdown' / md_filename
        md_file.save(str(md_path))

        try:
            # Определяем путь к фону
            bg_path = BackgroundsService.get_background_path(settings.background)
            if not bg_path:
                bg_path = config.ROOT_DIR / 'bg.jpg'

            # Определяем путь к шрифтам заголовков
            font_file = FontsService.find_font_file(settings.font_name)
            font_path = str(font_file.parent) if font_file else str(config.FONTS_FOLDER)

            # Определяем путь к шрифту текста (если указан отдельный)
            text_font_path = None
            if settings.text_font_name:
                text_font_file = FontsService.find_font_file(settings.text_font_name)
                text_font_path = str(text_font_file.parent) if text_font_file else None

            # Определяем расширение и MIME тип по формату экспорта
            export_format = settings.export_format.lower()
            if export_format == 'pptx':
                extension = '.pptx'
                mime_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            elif export_format == 'jpg':
                extension = '.zip'
                mime_type = 'application/zip'
            else:
                extension = '.pdf'
                mime_type = 'application/pdf'

            # Генерируем имя выходного файла
            output_name = os.path.splitext(md_file.filename)[0]
            safe_output_name = get_safe_filename(f"{output_name}{extension}")
            output_path = config.GENERATED_FOLDER / safe_output_name

            # Сохраняем текущую директорию
            original_cwd = os.getcwd()

            try:
                os.chdir(str(config.ROOT_DIR))

                # Создаём конвертер с новыми параметрами
                converter = MarkdownSlideConverter(
                    font_path=font_path,
                    font_name=settings.font_name,
                    text_font_name=settings.text_font_name if settings.text_font_name else None,
                    text_font_path=text_font_path,
                    background_image=str(bg_path),
                    heading_color=settings.heading_color,
                    text_color=settings.text_color,
                    accent_color=settings.accent_color,
                    heading_gradient=settings.heading_gradient,
                    heading_gradient_end=settings.heading_gradient_end,
                    text_gradient=settings.text_gradient,
                    text_gradient_end=settings.text_gradient_end,
                    bg_effect=settings.bg_effect,
                    bg_effect_intensity=settings.bg_effect_intensity,
                    format=settings.format,
                    heading_font_size=settings.heading_font_size,
                    heading_width=settings.heading_width,
                    text_font_size=settings.text_font_size,
                    text_width=settings.text_width
                )

                # Парсим markdown
                slides = converter.parse_markdown(str(md_path))

                # Генерируем в нужном формате
                if export_format == 'pptx':
                    converter.create_pptx(slides, str(output_path))
                elif export_format == 'jpg':
                    converter.create_jpg_archive(slides, str(output_path))
                else:
                    converter.create_pdf(slides, str(output_path))

            finally:
                os.chdir(original_cwd)

            # Сохраняем настройки
            SettingsService.save(settings.to_dict())

            # Читаем результат как base64
            with open(output_path, 'rb') as f:
                file_data = base64.b64encode(f.read()).decode('utf-8')

            # Удаляем файл
            try:
                output_path.unlink()
            except OSError:
                pass

            return True, 'OK', f"{output_name}{extension}", file_data

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f'Ошибка генерации: {str(e)}', None, None

        finally:
            # Удаляем исходный markdown
            try:
                md_path.unlink()
            except OSError:
                pass

# -*- coding: utf-8 -*-
"""
API маршруты.
"""

from flask import Blueprint, request, jsonify

from web.utils import require_pin
from web.services import (
    SettingsService,
    FontsService,
    BackgroundsService,
    PresentationService,
    PresentationSettings,
    AIAgentService
)

api_bp = Blueprint('api', __name__)


# === Settings ===

@api_bp.route('/settings', methods=['GET', 'POST'])
@require_pin
def settings():
    """API для работы с настройками."""
    if request.method == 'GET':
        return jsonify(SettingsService.load())
    
    # POST - сохранение настроек
    data = request.get_json()
    SettingsService.save(data)
    return jsonify({'success': True})


# === Uploads ===

@api_bp.route('/upload/background', methods=['POST'])
@require_pin
def upload_background():
    """Загрузка фонового изображения."""
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400
    
    success, result, name = BackgroundsService.upload(request.files['file'])
    
    if not success:
        return jsonify({'error': result}), 400
    
    return jsonify({
        'success': True,
        'filename': result,
        'name': name
    })


@api_bp.route('/upload/font', methods=['POST'])
@require_pin
def upload_font():
    """Загрузка пользовательского шрифта."""
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400
    
    success, result, font_name = FontsService.upload(request.files['file'])
    
    if not success:
        return jsonify({'error': result}), 400
    
    return jsonify({
        'success': True,
        'filename': result,
        'font_name': font_name
    })


# === Lists ===

@api_bp.route('/fonts')
@require_pin
def fonts():
    """Список доступных шрифтов."""
    return jsonify(FontsService.get_available())


@api_bp.route('/font/<font_name>')
@require_pin
def get_font_file(font_name):
    """Получить файл шрифта по имени."""
    from flask import send_file, abort
    
    font_path = FontsService.find_font_file(font_name)
    if not font_path or not font_path.exists():
        abort(404)
    
    # Определяем MIME тип
    mime_type = 'font/ttf' if font_path.suffix == '.ttf' else 'font/otf'
    return send_file(font_path, mimetype=mime_type)


@api_bp.route('/backgrounds')
@require_pin
def backgrounds():
    """Список доступных фонов."""
    return jsonify(BackgroundsService.get_available())


# === Generation ===

@api_bp.route('/generate', methods=['POST'])
@require_pin
def generate():
    """Генерация презентации."""
    if 'markdown' not in request.files:
        return jsonify({'error': 'Markdown файл не найден'}), 400
    
    md_file = request.files['markdown']
    
    # Валидация
    valid, error = PresentationService.validate_markdown(md_file)
    if not valid:
        return jsonify({'error': error}), 400
    
    # Настройки из формы
    settings = PresentationSettings.from_form(request.form)
    
    # Генерация
    success, message, filename, file_base64 = PresentationService.generate(
        md_file, settings
    )

    if not success:
        return jsonify({'error': message}), 500

    # Определяем MIME тип по расширению файла
    if filename.endswith('.pptx'):
        mime_type = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    elif filename.endswith('.zip'):
        mime_type = 'application/zip'
    else:
        mime_type = 'application/pdf'

    return jsonify({
        'success': True,
        'filename': filename,
        'file_base64': file_base64,
        'mime_type': mime_type
    })


# === AI Agent ===

@api_bp.route('/ai/prepare', methods=['POST'])
@require_pin
def ai_prepare():
    """AI агент для подготовки презентации из текста."""
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400

    file = request.files['file']

    if not file or file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400

    # Проверяем расширение
    if not AIAgentService.is_allowed_file(file.filename):
        return jsonify({
            'error': 'Неподдерживаемый формат. Разрешены: .txt, .md, .docx'
        }), 400

    # Обрабатываем файл
    success, result = AIAgentService.prepare_presentation(file)

    if not success:
        return jsonify({'error': result}), 500

    return jsonify({
        'success': True,
        'markdown': result
    })

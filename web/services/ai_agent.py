# -*- coding: utf-8 -*-
"""
AI Agent сервис для подготовки презентаций.
"""

import os
from typing import Tuple, Optional
from werkzeug.datastructures import FileStorage

# Промпт для преобразования текста в Markdown презентацию
PRESENTATION_PROMPT = """Преобразуй этот текст в Markdown файл для презентации.

КРИТИЧЕСКИ ВАЖНО:
- Выводи ТОЛЬКО готовый Markdown код
- НЕ добавляй пояснений, комментариев, примечаний
- НЕ добавляй технические параметры или метаданные
- НЕ добавляй текст вроде "Вот готовый Markdown:" или "---" в конце
- НЕ добавляй служебные пометки типа [Слайд 1], [Конец] и т.п.

Правила форматирования:
1. Каждый смысловой блок = один слайд с заголовком #
2. Заголовок — краткий тезис из 5-7 слов, суть мысли для зрителя
3. Под заголовком 2-4 пункта через "- " (тире и пробел)
4. Пункты — только ключевые факты, цифры, действия
5. Используй ## для разделов или слайдов без списка
6. Для акцента используй **жирный текст**

Пример структуры:
# Почему это важно
- Первый ключевой факт
- Второй **ключевой** факт
- Призыв к действию

## Следующий раздел
- Пункт раздела

Текст для преобразования:
"""


class AIAgentService:
    """Сервис AI агента для подготовки презентаций."""

    # Поддерживаемые расширения
    ALLOWED_EXTENSIONS = {'.txt', '.md', '.markdown', '.docx'}

    @staticmethod
    def is_allowed_file(filename: str) -> bool:
        """Проверить, поддерживается ли файл."""
        ext = os.path.splitext(filename)[1].lower()
        return ext in AIAgentService.ALLOWED_EXTENSIONS

    @staticmethod
    def extract_text(file: FileStorage) -> Tuple[bool, str]:
        """
        Извлечь текст из файла.

        Args:
            file: Загруженный файл

        Returns:
            Tuple (успех, текст или сообщение об ошибке)
        """
        if not file or file.filename == '':
            return False, 'Файл не выбран'

        filename = file.filename.lower()
        ext = os.path.splitext(filename)[1]

        if ext not in AIAgentService.ALLOWED_EXTENSIONS:
            allowed = ', '.join(AIAgentService.ALLOWED_EXTENSIONS)
            return False, f'Неподдерживаемый формат. Разрешены: {allowed}'

        try:
            # Читаем содержимое в зависимости от типа файла
            if ext in {'.txt', '.md', '.markdown'}:
                content = file.read().decode('utf-8')
            elif ext == '.docx':
                content = AIAgentService._read_docx(file)
            else:
                return False, 'Неизвестный формат файла'

            if not content.strip():
                return False, 'Файл пустой'

            return True, content

        except UnicodeDecodeError:
            return False, 'Ошибка кодировки файла. Используйте UTF-8'
        except Exception as e:
            return False, f'Ошибка чтения файла: {str(e)}'

    @staticmethod
    def _read_docx(file: FileStorage) -> str:
        """Прочитать текст из .docx файла."""
        try:
            from docx import Document
            import io

            # Читаем файл в память
            file_bytes = io.BytesIO(file.read())
            doc = Document(file_bytes)

            # Извлекаем текст из всех параграфов
            paragraphs = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:
                    paragraphs.append(text)

            return '\n\n'.join(paragraphs)

        except ImportError:
            raise Exception('Библиотека python-docx не установлена')
        except Exception as e:
            raise Exception(f'Ошибка чтения DOCX: {str(e)}')

    @staticmethod
    def process_with_ai(text: str) -> Tuple[bool, str]:
        """
        Обработать текст с помощью AI.

        Args:
            text: Исходный текст

        Returns:
            Tuple (успех, результат или ошибка)
        """
        api_key = os.environ.get('OPENAI_API_KEY')

        if not api_key:
            return False, 'OPENAI_API_KEY не настроен'

        try:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)

            # GPT-4o-mini с максимальным количеством токенов
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "Ты эксперт по созданию презентаций. Твоя задача — преобразовывать тексты в структурированный Markdown для слайдов. Отвечай ТОЛЬКО готовым Markdown, без пояснений."
                    },
                    {
                        "role": "user",
                        "content": PRESENTATION_PROMPT + text
                    }
                ],
                max_tokens=16384,  # Максимум для gpt-4o-mini
                temperature=0.3  # Низкая температура для более предсказуемого результата
            )

            result = response.choices[0].message.content

            # Убираем возможные markdown блоки кода
            if result.startswith('```markdown'):
                result = result[11:]
            elif result.startswith('```md'):
                result = result[5:]
            elif result.startswith('```'):
                result = result[3:]
            if result.endswith('```'):
                result = result[:-3]

            # Очищаем от служебных пометок и мусора
            import re
            
            # Убираем строки с техническими пометками
            lines = result.strip().split('\n')
            cleaned_lines = []
            for line in lines:
                stripped = line.strip()
                # Пропускаем пустые строки в начале/конце
                # Пропускаем служебные пометки
                if re.match(r'^\[.*\]$', stripped):  # [Слайд 1], [Конец] и т.п.
                    continue
                if re.match(r'^---+$', stripped):  # Разделители ---
                    continue
                if stripped.lower().startswith(('вот ', 'готово', 'ниже ', 'примечание', 'note:')):
                    continue
                if 'параметр' in stripped.lower() and ':' in stripped:
                    continue
                cleaned_lines.append(line)
            
            # Убираем пустые строки в начале и конце
            while cleaned_lines and not cleaned_lines[0].strip():
                cleaned_lines.pop(0)
            while cleaned_lines and not cleaned_lines[-1].strip():
                cleaned_lines.pop()

            result = '\n'.join(cleaned_lines)

            return True, result.strip()

        except ImportError:
            return False, 'Библиотека openai не установлена'
        except Exception as e:
            error_msg = str(e)
            if 'api_key' in error_msg.lower():
                return False, 'Неверный API ключ OpenAI'
            return False, f'Ошибка AI: {error_msg}'

    @staticmethod
    def prepare_presentation(file: FileStorage) -> Tuple[bool, str]:
        """
        Полный пайплайн подготовки презентации.

        Args:
            file: Загруженный файл

        Returns:
            Tuple (успех, markdown или ошибка)
        """
        # Извлекаем текст
        success, result = AIAgentService.extract_text(file)
        if not success:
            return False, result

        # Обрабатываем AI
        return AIAgentService.process_with_ai(result)

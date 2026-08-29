#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генерация фонов-градиентов для слайдов.

Запуск: python tools/make_backgrounds.py
Результат: bg.jpg (фон по умолчанию) и backgrounds/*.jpg

Все фоны рисуются кодом, поэтому свободны от чужих авторских прав.
"""

import os
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SIZE = (1920, 1080)

PRESETS = {
    'Ночь': (('#0b1120', '#1e293b'), ('#38bdf8', 0.22)),
    'Графит': (('#111111', '#2b2b2b'), None),
    'Закат': (('#1a1035', '#7c2d5e'), ('#f59e0b', 0.18)),
    'Океан': (('#04212b', '#0d5561'), ('#22d3ee', 0.16)),
    'Бумага': (('#f5f2ec', '#e2ddd3'), None),
}


def hex_to_rgb(value):
    value = value.lstrip('#')
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def linear_gradient(size, start, end):
    """Диагональный градиент из двух цветов."""
    width, height = size
    base = Image.new('RGB', size, start)
    top = Image.new('RGB', size, end)
    mask = Image.new('L', size)
    pixels = mask.load()
    for y in range(height):
        for x in range(0, width, 4):
            value = int(255 * ((x / width) * 0.65 + (y / height) * 0.35))
            for dx in range(4):
                if x + dx < width:
                    pixels[x + dx, y] = value
    base.paste(top, (0, 0), mask)
    return base


def add_glow(image, color, strength):
    """Мягкое световое пятно в правом верхнем углу."""
    width, height = image.size
    glow = Image.new('RGB', image.size, (0, 0, 0))
    draw = ImageDraw.Draw(glow)
    radius = int(width * 0.42)
    center = (int(width * 0.72), int(height * 0.28))
    draw.ellipse(
        [center[0] - radius, center[1] - radius, center[0] + radius, center[1] + radius],
        fill=color,
    )
    glow = glow.filter(ImageFilter.GaussianBlur(radius // 2))
    return Image.blend(image, Image.blend(image, glow, strength), 1.0)


def build(name, gradient, glow):
    image = linear_gradient(SIZE, hex_to_rgb(gradient[0]), hex_to_rgb(gradient[1]))
    if glow:
        image = add_glow(image, hex_to_rgb(glow[0]), glow[1])
    return image


def main():
    os.makedirs(os.path.join(ROOT, 'backgrounds'), exist_ok=True)
    for name, (gradient, glow) in PRESETS.items():
        image = build(name, gradient, glow)
        path = os.path.join(ROOT, 'backgrounds', f'{name}.jpg')
        image.save(path, quality=88, optimize=True)
        print(f'{path} — {os.path.getsize(path) // 1024} КБ')

    default = build('Ночь', *PRESETS['Ночь'])
    default_path = os.path.join(ROOT, 'bg.jpg')
    default.save(default_path, quality=88, optimize=True)
    print(f'{default_path} — {os.path.getsize(default_path) // 1024} КБ (фон по умолчанию)')


if __name__ == '__main__':
    main()

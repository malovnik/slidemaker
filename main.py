#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Запуск Slidemaker на своём компьютере.

    python main.py

Дальше откройте в браузере адрес, который появится в терминале
(обычно http://127.0.0.1:5000). Остановить — Ctrl+C.
"""

import os
import sys
import threading
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.absolute()))

from web.app import create_app
from web.utils import cleanup_old_files


def main():
    cleanup_old_files()

    app = create_app()

    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    url = f'http://{host}:{port}'

    print()
    print('  Slidemaker запущен')
    print(f'  Откройте в браузере: {url}')
    print('  Остановить: Ctrl+C')
    print()

    # Открываем браузер сами — чтобы не пришлось копировать адрес руками
    if os.environ.get('NO_BROWSER', '').lower() not in ('1', 'true', 'yes'):
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    main()

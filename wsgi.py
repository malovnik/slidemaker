# -*- coding: utf-8 -*-
"""WSGI entry point for gunicorn."""

import sys
import os

# Add app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.app import create_app

app = create_app()

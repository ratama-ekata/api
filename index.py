"""
Vercel Serverless Function Entry Point for api.ratamaekata.gov.lk
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.main import app

__all__ = ["app"]

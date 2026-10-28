"""
Mirror entry point for Vercel Serverless Function autodetection.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, ".."))
for p in [parent_dir, current_dir]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.main import app

__all__ = ["app"]


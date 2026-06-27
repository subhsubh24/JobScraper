"""Vercel serverless entry for the Career Operator API.

Vercel's @vercel/python runtime serves the ASGI `app` exported here. The FastAPI
app itself lives in /asgi.py (named to avoid colliding with this /api package dir).
All routes are rewritten to this function via vercel.json.
"""
import os
import sys

# Ensure the project root is importable from inside the /api function dir.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from asgi import app  # noqa: E402  (re-exported as the ASGI handler Vercel serves)

__all__ = ["app"]

"""API support layer: structured logging + a consistent error envelope.

These modules are deliberately framework-light and side-effect-free on import (except
`logging_config.setup_logging()`, which is called explicitly from `asgi.py`). Keeping them
here — rather than inline in `asgi.py` — lets the journey suite and unit tests exercise the
envelope/logging logic in isolation.
"""

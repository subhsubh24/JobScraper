"""The committed Google Play feature graphic meets the store spec and matches its generator.

Google Play REQUIRES a 1024x500, 24-bit PNG with NO alpha channel to publish (ACCEPTANCE_AUDIT
G7). The spec checks below read only the COMMITTED PNG (Pillow-only, always run in CI). The
generator checks call ``build()``, which needs the system DejaVu font; where that font isn't
installed they SKIP (an honest env gate, not a hidden failure) rather than hard-fail the gate.
"""
import importlib.util
import os

import pytest
from PIL import Image

_ROOT = os.path.dirname(os.path.dirname(__file__))
_ASSET = os.path.join(_ROOT, "docs", "store", "assets", "feature-graphic.png")
_SCRIPT = os.path.join(_ROOT, "scripts", "generate_feature_graphic.py")


def _build_or_skip():
    """Render via the generator, or skip if the DejaVu font isn't available in this env."""
    spec = importlib.util.spec_from_file_location("gen_feature_graphic", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    try:
        return mod.build()
    except OSError as e:  # ImageFont.truetype can't open the system font
        pytest.skip(f"DejaVu font not available in this environment: {e}")


def test_feature_graphic_exists():
    assert os.path.isfile(_ASSET), "committed feature graphic is missing"


def test_feature_graphic_meets_play_spec():
    with Image.open(_ASSET) as im:
        assert im.size == (1024, 500), f"Play requires 1024x500, got {im.size}"
        # 24-bit, NO alpha channel — Play rejects graphics with alpha.
        assert im.mode == "RGB", f"Play requires no alpha (24-bit RGB), got mode {im.mode}"
        assert im.format == "PNG"


def test_committed_asset_matches_the_generator_pixel_for_pixel():
    """Guards against a stale PNG: pixel equality (not PNG bytes, so it's robust to zlib)."""
    rendered = _build_or_skip()
    with Image.open(_ASSET) as committed:
        assert rendered.size == committed.size and rendered.mode == committed.mode
        assert rendered.tobytes() == committed.convert(rendered.mode).tobytes(), (
            "committed feature-graphic.png is stale — re-run scripts/generate_feature_graphic.py"
        )


def test_generator_output_is_deterministic():
    first = _build_or_skip()
    second = _build_or_skip()
    assert first.tobytes() == second.tobytes()

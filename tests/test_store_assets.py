"""Guard the committed store-listing image assets against the store specs.

A rendered store asset is a REAL artifact, not a spec: this test fails loud if the committed
Google Play feature graphic is missing, a placeholder, the wrong size, or carries an alpha
channel (Play rejects alpha). It reads the PNG header directly — no image library needed — so it
runs in the per-PR gate. Regenerate the asset with scripts/store/render_feature_graphic.sh.
"""
import struct
from pathlib import Path

FEATURE_GRAPHIC = Path(__file__).resolve().parent.parent / "docs" / "store" / "assets" / "feature-graphic.png"

_PNG_SIG = b"\x89PNG\r\n\x1a\n"


def _png_header(path: Path):
    data = path.read_bytes()
    assert data[:8] == _PNG_SIG, f"{path} is not a valid PNG"
    # IHDR: width (4), height (4) at offset 16; bit_depth (1) + color_type (1) at 24, 25.
    width, height = struct.unpack(">II", data[16:24])
    bit_depth, color_type = data[24], data[25]
    return width, height, bit_depth, color_type, len(data)


def test_feature_graphic_exists_and_nonzero():
    assert FEATURE_GRAPHIC.exists(), f"missing committed feature graphic: {FEATURE_GRAPHIC}"
    assert FEATURE_GRAPHIC.stat().st_size > 5000, "feature graphic is suspiciously small (placeholder?)"


def test_feature_graphic_matches_play_spec():
    """Google Play feature graphic: exactly 1024x500, 24-bit PNG, NO alpha channel."""
    width, height, bit_depth, color_type, size = _png_header(FEATURE_GRAPHIC)
    assert (width, height) == (1024, 500), f"feature graphic must be 1024x500, got {width}x{height}"
    assert bit_depth == 8, f"expected 8-bit depth, got {bit_depth}"
    # color_type 4 (gray+alpha) and 6 (RGBA) carry an alpha channel — Play rejects alpha.
    assert color_type in (0, 2, 3), f"feature graphic must have NO alpha channel (color_type={color_type})"
    assert size > 5000, "feature graphic is suspiciously small (placeholder?)"

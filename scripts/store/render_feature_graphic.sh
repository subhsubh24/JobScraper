#!/usr/bin/env bash
# Reproducibly render the Google Play feature graphic from its committed HTML source.
#
# The COMMITTED artifact is docs/store/assets/feature-graphic.png (1024x500, no alpha) — this
# script regenerates it byte-for-similar from scripts/store/feature_graphic.html so the asset is
# never a hand-edited binary blob: the design lives in reviewable HTML/CSS built from the real
# brand tokens (docs/brand/BRAND_KIT.md), and the PNG is its deterministic output.
#
# Requires a Chromium/Chrome headless binary. Resolution order:
#   1. $CHROME (explicit override)
#   2. a Playwright-managed Chromium under $PLAYWRIGHT_BROWSERS_PATH (or /opt/pw-browsers)
#   3. a system chromium / chromium-browser / google-chrome on PATH
#
# Google Play feature-graphic spec (re-verify at submission — Play console rules change):
#   1024 x 500 px, 24-bit PNG or JPEG, NO alpha channel.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
src="$here/feature_graphic.html"
out="$repo/docs/store/assets/feature-graphic.png"

find_chrome() {
  if [[ -n "${CHROME:-}" && -x "${CHROME}" ]]; then echo "$CHROME"; return; fi
  local roots="${PLAYWRIGHT_BROWSERS_PATH:-/opt/pw-browsers}"
  local c
  c="$(find "$roots" -type f -name chrome -path '*chrome-linux*' 2>/dev/null | sort | tail -1 || true)"
  if [[ -n "$c" && -x "$c" ]]; then echo "$c"; return; fi
  for b in chromium chromium-browser google-chrome google-chrome-stable chrome; do
    if command -v "$b" >/dev/null 2>&1; then command -v "$b"; return; fi
  done
  echo "ERROR: no Chromium/Chrome binary found. Set \$CHROME to a headless Chrome executable." >&2
  exit 1
}

chrome="$(find_chrome)"
echo "Rendering feature graphic with: $chrome"
# --force-device-scale-factor=1 => exact 1024x500 output (Play requires exactly 1024x500).
"$chrome" --headless --no-sandbox --disable-gpu --hide-scrollbars \
  --force-device-scale-factor=1 --window-size=1024,500 \
  --screenshot="$out" "file://$src" >/dev/null 2>&1

# Verify dimensions + non-zero (fail loud on a bad render — never leave a placeholder).
python3 - "$out" <<'PY'
import struct, sys
p = sys.argv[1]
d = open(p, "rb").read()
assert d[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
w, h = struct.unpack(">II", d[16:24])
assert (w, h) == (1024, 500), f"expected 1024x500, got {w}x{h}"
assert len(d) > 5000, f"suspiciously small render ({len(d)} bytes)"
print(f"OK: {p} -> {w}x{h}, {len(d)} bytes")
PY

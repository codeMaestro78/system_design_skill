# System Design assets

Brand artwork for the `system-design` skill. Every file here is original work
created for this repository and is covered by the repository's MIT licence.

| File | Purpose | Size | Notes |
| --- | --- | --- | --- |
| [`logo.svg`](./logo.svg) | Canonical mark | 512 x 512 SVG | The source of truth for the artwork. Vector, dark plate, full palette. |
| [`logo-512.png`](./logo-512.png) | Raster export of the canonical mark | 512 x 512 PNG | 8-bit RGBA, sRGB, 96 DPI. Regenerated from `logo.svg`; do not hand-edit. |
| [`icon.svg`](./icon.svg) | Small UI icon | 24 x 24 SVG | Reduction of the logo's node graph. Strokes use `currentColor`, so it adapts to the host surface. |
| [`icon-mono.svg`](./icon-mono.svg) | Single-colour icon | 24 x 24 SVG | Same glyph as `icon.svg`, drawn entirely in `currentColor` for hosts that cannot tint an accent. |

`logo.svg` is canonical. `logo-512.png` is a build artefact of it, and
`icon.svg` / `icon-mono.svg` are deliberate reductions of it rather than
separate drawings. Change `logo.svg` first, then regenerate the PNG, then
re-derive the icons if the composition changes.

## Light and dark usage

- `icon.svg` and `icon-mono.svg` paint their structural strokes with
  `currentColor`, so they inherit the host's text colour and stay legible on
  light and dark surfaces without a second asset. The single accent in
  `icon.svg` (`#F75858`) measures 3.2:1 on white and 5.6:1 on the `#0D1526`
  plate, so it clears the 3:1 non-text contrast bar on both.
- `logo.svg` and `logo-512.png` carry their own dark `#0D1526` plate. Place them
  on light surfaces as-is; on dark surfaces the plate reads as a raised tile
  rather than as a hole, which is intentional.
- Never recolour the structural strokes by hand. Use `icon-mono.svg` when a
  host needs a strictly single-colour mark.

## Palette

The logo's colours, as CSS custom properties:

```css
:root {
  --system-design-plate: #0D1526;  /* background plate */
  --system-design-yellow: #FFD400; /* client / gateway node */
  --system-design-sky: #38BDF8;    /* left service node */
  --system-design-orange: #FFA43D; /* right service node */
  --system-design-coral: #F75858;  /* database body, icon accent */
  --system-design-coral-light: #FF7A7A; /* database top cap */
  --system-design-coral-dark: #B93A3A;  /* database bottom disc */
  --system-design-slate: #475569;  /* connectors */
  --system-design-mist: #E2E8F0;   /* joint dots */
  --system-design-navy: #10233F;   /* left service node fill */
  --system-design-bronze: #2A1A10; /* right service node fill */
}
```

`--system-design-plate` is also the `brand_color` in
[`../agents/openai.yaml`](../agents/openai.yaml).

## Regenerating the PNG

`logo-512.png` is produced from `logo.svg` and must stay square, 8-bit per
channel, sRGB-tagged, and 96 DPI. Run this from the repository root:

```bash
python -m pip install cairosvg pillow
python - <<'PY'
import struct, zlib
from pathlib import Path
import cairosvg
from PIL import Image

src = Path("system-design/assets/logo.svg")
dst = Path("system-design/assets/logo-512.png")
tmp = dst.with_suffix(".tmp.png")

cairosvg.svg2png(url=str(src), write_to=str(tmp), output_width=512, output_height=512)
with Image.open(tmp) as im:
    im.convert("RGBA").save(tmp, format="PNG", optimize=True, compress_level=9)
raw = tmp.read_bytes()
tmp.unlink()

def chunks(data):
    pos = 8
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        yield data[pos + 4:pos + 8], data[pos + 8:pos + 8 + length]
        pos += 12 + length

def chunk(ctype, payload):
    crc = zlib.crc32(ctype + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + ctype + payload + struct.pack(">I", crc)

out = bytearray(b"\x89PNG\r\n\x1a\n")
idat = bytearray()
for ctype, payload in chunks(raw):
    if ctype in (b"pHYs", b"sRGB", b"IEND"):
        continue
    if ctype == b"IDAT":
        idat += payload
        continue
    out += chunk(ctype, payload)
    if ctype == b"IHDR":
        out += chunk(b"sRGB", bytes([0]))
        out += chunk(b"pHYs", struct.pack(">IIB", 3780, 3780, 1))
out += chunk(b"IDAT", zlib.compress(zlib.decompress(bytes(idat)), 9))
out += chunk(b"IEND", b"")
dst.write_bytes(bytes(out))
print(dst, dst.stat().st_size, "bytes")
PY
```

`rsvg-convert -w 512 -h 512 system-design/assets/logo.svg > system-design/assets/logo-512.png`
renders the same artwork but omits the `sRGB` and `pHYs` chunks, so prefer the
script above when the metadata matters.

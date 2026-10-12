"""Generate grey SVG teaser placeholders for portfolio items.

Usage: python scripts/make_placeholders.py <slug:Label> [<slug:Label> ...]
Writes images/placeholders/<slug>.svg (500x300).
"""
import sys
from pathlib import Path

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" width="500" height="300" viewBox="0 0 500 300">
  <rect width="500" height="300" fill="#e9ecef"/>
  <rect x="10" y="10" width="480" height="280" fill="none" stroke="#adb5bd" stroke-width="2" stroke-dasharray="8 6"/>
  <text x="250" y="150" font-family="Helvetica, Arial, sans-serif" font-size="24" fill="#495057"
        text-anchor="middle" dominant-baseline="middle">{label}</text>
  <text x="250" y="190" font-family="Helvetica, Arial, sans-serif" font-size="14" fill="#868e96"
        text-anchor="middle">figure coming soon</text>
</svg>
"""


def write_placeholder(out_dir: Path, slug: str, label: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{slug}.svg"
    safe = label.replace("&", "&amp;").replace("<", "&lt;")
    path.write_text(TEMPLATE.format(label=safe), encoding="utf-8")
    return path


def main(argv: list[str]) -> int:
    out_dir = Path(__file__).resolve().parents[1] / "images" / "placeholders"
    for arg in argv:
        slug, _, label = arg.partition(":")
        p = write_placeholder(out_dir, slug, label or slug)
        print("wrote", p.relative_to(out_dir.parents[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

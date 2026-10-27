"""Dibuja el icono de Climb Tracker: una montaña azul nevada y, abajo a la derecha,
una chapa naranja con una flecha blanca de tendencia al alza.

Genera climbtracker/assets/icon.ico (todos los tamaños de Windows) y
climbtracker/ui/icon.png (para la cabecera de la app). Uso: python tools/make_icon.py
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SS = 8  # se dibuja a 8x y se reduce, para que los bordes salgan suaves

BG_TOP, BG_BOTTOM = (31, 42, 61), (11, 15, 22)
BACK = (29, 56, 104)
MAIN_TOP, MAIN_BOTTOM = (84, 156, 255), (40, 92, 208)
SNOW = (232, 238, 247)
ORANGE_TOP, ORANGE_BOTTOM = (255, 170, 80), (255, 106, 16)
WHITE = (255, 255, 255)
RING = (13, 17, 23)  # borde oscuro que separa la chapa de la montaña

# Coordenadas de 0 a 1 sobre el lado del icono.
BADGE_C, BADGE_R, RING_R = (0.735, 0.735), 0.215, 0.255
TREND = [(0.585, 0.835), (0.685, 0.725), (0.745, 0.79), (0.875, 0.645)]


def _gradient(s: int, top, bottom) -> Image.Image:
    g = Image.new("RGB", (1, s))
    for y in range(s):
        t = y / max(1, s - 1)
        g.putpixel((0, y), tuple(round(a + (b - a) * t) for a, b in zip(top, bottom)))
    return g.resize((s, s))


def _fill(s: int, mask: Image.Image, fill) -> Image.Image:
    out = (fill if isinstance(fill, Image.Image) else Image.new("RGB", (s, s), fill)).convert("RGBA")
    out.putalpha(mask)
    return out


def _polygon(s: int, points, fill) -> Image.Image:
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).polygon([(x * s, y * s) for x, y in points], fill=255)
    return _fill(s, mask, fill)


def _circle(s: int, center, r: float, fill) -> Image.Image:
    (cx, cy), mask = center, Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).ellipse([(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s], fill=255)
    return _fill(s, mask, fill)


def _arrow(s: int, points, width: float, head_len: float, head_w: float, fill) -> Image.Image:
    """Línea quebrada gruesa (inicio redondo) que acaba en punta de flecha."""
    pts = [(x * s, y * s) for x, y in points]
    w = width * s
    (x1, y1), (x2, y2) = pts[-2], pts[-1]
    n = math.hypot(x2 - x1, y2 - y1)
    ux, uy = (x2 - x1) / n, (y2 - y1) / n
    bx, by = x2 - ux * head_len * s, y2 - uy * head_len * s
    hw = head_w * s
    mask = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(mask)
    d.polygon([(x2 + ux * w * 0.3, y2 + uy * w * 0.3), (bx - uy * hw, by + ux * hw), (bx + uy * hw, by - ux * hw)], fill=255)
    pts[-1] = (bx + ux * w * 0.5, by + uy * w * 0.5)
    d.line(pts, fill=255, width=round(w), joint="curve")
    x0, y0 = pts[0]
    d.ellipse([x0 - w / 2, y0 - w / 2, x0 + w / 2, y0 + w / 2], fill=255)
    return _fill(s, mask, fill)


def draw(px: int) -> Image.Image:
    s = px * SS
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    round_mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(round_mask).rounded_rectangle([0, 0, s - 1, s - 1], radius=round(s * 0.22), fill=255)
    img.paste(_gradient(s, BG_TOP, BG_BOTTOM).convert("RGBA"), (0, 0), round_mask)

    scene = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    for layer in (
        _polygon(s, [(0.40, 1.02), (0.74, 0.46), (1.06, 1.02)], BACK),                      # cumbre de atrás
        _polygon(s, [(-0.02, 1.02), (0.40, 0.20), (0.82, 1.02)],                            # montaña principal
                 _gradient(s, MAIN_TOP, MAIN_BOTTOM)),
        _polygon(s, [(0.40, 0.20), (0.285, 0.40), (0.34, 0.365), (0.40, 0.415),             # nieve de la cima
                     (0.46, 0.365), (0.515, 0.40)], SNOW),
        _circle(s, BADGE_C, RING_R, RING),                                                  # chapa
        _circle(s, BADGE_C, BADGE_R, _gradient(s, ORANGE_TOP, ORANGE_BOTTOM)),
        _arrow(s, TREND, 0.055, 0.095, 0.075, WHITE),                                       # flecha ↗
    ):
        scene.alpha_composite(layer)
    # La escena se recorta con las esquinas redondeadas del fondo.
    scene.putalpha(Image.composite(scene.getchannel("A"), Image.new("L", (s, s), 0), round_mask))
    img.alpha_composite(scene)
    return img.resize((px, px), Image.LANCZOS)


def main() -> None:
    sizes = [256, 128, 64, 48, 40, 32, 24, 20, 16]
    images = {px: draw(px) for px in sizes}
    assets = ROOT / "climbtracker" / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    images[256].save(assets / "icon.ico", format="ICO", sizes=[(px, px) for px in sizes],
                     append_images=[images[px] for px in sizes[1:]])
    images[64].save(ROOT / "climbtracker" / "ui" / "icon.png")
    print("icono generado:", assets / "icon.ico")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Regenerate clean Matrix PWA icons: neon-green terminal >_ on near-black, faint edge rain only."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "icons"; OUT.mkdir(parents=True, exist_ok=True)
BG, MARK, MARK_DIM = (2, 4, 2), (0, 255, 70), (0, 180, 50)
BOLD = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
MONO = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
def font(cands, size):
    for p in cands:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()
def edge_rain(img, seed, strength=0.4):
    rng = random.Random(seed); W, H = img.size; f = font(MONO, max(8, W // 32))
    col_w = max(14, W // 14); edge = int(W * 0.14); step = max(12, W // 24)
    for c in range((W // col_w) + 1):
        if rng.random() > 0.55: continue
        x = int(c * col_w + rng.randint(0, 3)); head = rng.randint(-H // 5, H)
        for i in range(rng.randint(2, 5)):
            y = head + i * step
            if y < 0 or y > H: continue
            if not ((x < edge or x > W - edge) or (y < edge or y > H - edge)): continue
            if edge < x < W - edge and edge < y < H - edge: continue
            a = int((90 if i == 0 else 45) * strength)
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(ov).text((x, y), rng.choice("01<>|/\\*+#="), font=f, fill=(*MARK_DIM, a))
            img.alpha_composite(ov)
def draw_prompt(img):
    W, H = img.size; draw = ImageDraw.Draw(img); cx, cy = W // 2, H // 2
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow); r = int(W * 0.22)
    for i in range(8, 0, -1):
        gd.ellipse([cx - r - i * 6, cy - r - i * 6, cx + r + i * 6, cy + r + i * 6], fill=(0, 255, 65, int(12 + 8 * i / 8)))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(radius=max(5, W // 30))))
    f = font(BOLD, int(W * 0.48)); text = ">_"; bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    ox, oy = cx - tw // 2 - bbox[0], cy - th // 2 - bbox[1] - int(H * 0.02)
    o = max(2, W // 90)
    for dx in range(-o, o + 1):
        for dy in range(-o, o + 1):
            if dx * dx + dy * dy <= o * o + 1:
                draw.text((ox + dx, oy + dy), text, font=f, fill=(0, 20, 4, 255))
    draw.text((ox, oy), text, font=f, fill=(*MARK, 255))
def make(size, maskable=False):
    img = Image.new("RGBA", (size, size), (*BG, 255))
    if size >= 64: edge_rain(img, seed=99 + size + (7 if maskable else 0), strength=0.5 if maskable else 0.35)
    draw_prompt(img)
    out = Image.new("RGB", (size, size), BG); out.paste(img, mask=img.split()[3]); return out
def main():
    make(512).save(OUT / "icon-512.png", optimize=True)
    make(192).save(OUT / "icon-192.png", optimize=True)
    make(180).save(OUT / "apple-touch-icon.png", optimize=True)
    make(512, maskable=True).save(OUT / "icon-512-maskable.png", optimize=True)
    make(32).save(OUT / "favicon-32.png", optimize=True)
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))
if __name__ == "__main__": main()

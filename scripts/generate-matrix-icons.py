#!/usr/bin/env python3
"""Regenerate Matrix-themed PWA icons (λ + rain) into public/icons/ and screenshots/."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, random, os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "icons"
SHOTS = ROOT / "screenshots"
OUT.mkdir(parents=True, exist_ok=True); SHOTS.mkdir(parents=True, exist_ok=True)

BG = (1, 6, 1); MARK = (0, 255, 70)
CHARS = "01アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン<>[]{}/\\|$#@*%+=;:ﾊﾋﾌﾍﾎｱｲｳｴｵ"
BOLD = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]
MONO = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"]
CJK = ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/noto/NotoSansCJKjp-Regular.otf",
       "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf", "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"]

def font(cands, size):
    for p in cands:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()

def paint_rain(base, seed, density=0.55, strength=0.9, clear_r=0.32):
    rng = random.Random(seed); W, H = base.size; cx, cy = W / 2, H / 2
    fsize = max(9, W // 26); rain_font = font(CJK + MONO, fsize)
    charset = CHARS if any(os.path.exists(p) for p in CJK) else "01<>[]{}/\\|$#@*%+=;:ABCDEFGHIJKLMNOPQRSTUVWXYZﾊﾋﾌﾍﾎ"
    col_w = max(11, W // 16); step = max(11, int(fsize * 1.15))
    for c in range((W // col_w) + 1):
        if rng.random() > density: continue
        x = int(c * col_w + rng.randint(0, max(1, col_w // 3))); head = rng.randint(-H // 3, H)
        length = rng.randint(H // 5, int(H * 0.7)); n = max(3, length // step)
        for i in range(n):
            y = head + i * step
            if y < -fsize or y > H + fsize: continue
            dist = math.hypot((x - cx) / W, (y - cy) / H)
            if dist < clear_r and rng.random() < 0.92: continue
            t = i / n
            rgb, a = ((180, 255, 190), int(210 * strength)) if t < 0.06 else \
                     ((0, 255, 70), int(160 * strength)) if t < 0.2 else \
                     ((0, 180, 50), int(110 * strength)) if t < 0.45 else \
                     ((0, 100, 35), int(75 * strength)) if t < 0.75 else ((0, 50, 20), int(45 * strength))
            if dist < clear_r + 0.1: a = int(a * 0.35)
            ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(ov).text((x, y), rng.choice(charset), font=rain_font, fill=(*rgb, a))
            base.alpha_composite(ov)
    return base

def draw_lambda(img):
    W, H = img.size; draw = ImageDraw.Draw(img); cx, cy = W // 2, H // 2
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow); r = int(W * 0.26)
    for i in range(10, 0, -1):
        a = int(14 + 10 * (i / 10))
        gd.ellipse([cx - r - i * 5, cy - r - i * 5 - int(H * 0.02), cx + r + i * 5, cy + r + i * 5 - int(H * 0.02)], fill=(0, 255, 65, a))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(radius=max(6, W // 28))))
    f = font(BOLD, int(W * 0.58)); text = "λ"; bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    ox, oy = cx - tw // 2 - bbox[0], cy - th // 2 - bbox[1] - int(H * 0.04)
    o = max(1, W // 160)
    for dx in range(-o * 2, o * 2 + 1):
        for dy in range(-o * 2, o * 2 + 1):
            if dx * dx + dy * dy <= (o * 2) ** 2:
                draw.text((ox + dx, oy + dy), text, font=f, fill=(0, 25, 5, 255))
    draw.text((ox, oy), text, font=f, fill=(*MARK, 255))
    uw, uh, uy = int(W * 0.20), max(3, W // 48), cy + int(H * 0.26)
    bar = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(bar).rounded_rectangle([cx - uw - 4, uy - 3, cx + uw + 4, uy + uh + 3], radius=3, fill=(0, 255, 70, 60))
    img.alpha_composite(bar.filter(ImageFilter.GaussianBlur(3)))
    draw.rounded_rectangle([cx - uw, uy, cx + uw, uy + uh], radius=max(1, uh // 2), fill=(*MARK, 240))
    return img

def make(size, maskable=False, rain_strength=0.95):
    img = Image.new("RGBA", (size, size), (*BG, 255))
    paint_rain(img, seed=(11 if maskable else 42) + size, density=0.8 if maskable else 0.55,
               strength=rain_strength, clear_r=0.34 if maskable else 0.30)
    draw_lambda(img)
    out = Image.new("RGB", (size, size), BG); out.paste(img, mask=img.split()[3]); return out

def main():
    icon_512 = make(512); icon_512.save(OUT / "icon-512.png", optimize=True)
    icon_192 = make(192); icon_192.save(OUT / "icon-192.png", optimize=True)
    make(180).save(OUT / "apple-touch-icon.png", optimize=True)
    make(512, maskable=True).save(OUT / "icon-512-maskable.png", optimize=True)
    make(32, rain_strength=0.4).save(OUT / "favicon-32.png", optimize=True)
    icon_192.save(SHOTS / "matrix-icon-192.png"); icon_512.save(SHOTS / "matrix-icon-512.png")
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))

if __name__ == "__main__":
    main()

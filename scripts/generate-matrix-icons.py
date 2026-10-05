#!/usr/bin/env python3
"""Matrix (1999) film-aesthetic PWA icons: cascading phosphor rain + bold Py glyph."""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "icons"; OUT.mkdir(parents=True, exist_ok=True)
BG, PHOSPHOR = (0, 0, 0), (0, 255, 65)
HEAD, MID, DIM, FAINT = (210, 255, 220), (0, 200, 55), (0, 100, 32), (0, 40, 12)
RAIN = "ﾊﾐﾋｰｳｼﾅﾓﾆｻﾜﾂｵﾘｱﾎﾃﾏｹﾒｴｶｷﾑﾕﾗｾﾈｽﾀﾇﾍ012345789ABCDEF:・.=*+-<>|"
BOLD = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"]
MONO = ["/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"]
CJK = ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
       "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"]
def font(cands, size):
    for p in cands:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    return ImageFont.load_default()
def paint_rain(base, seed, density=0.95):
    rng = random.Random(seed); W, H = base.size; fsize = max(11, W // 20)
    rf = font(CJK + MONO, fsize); col_w = max(fsize, W // 16); step = max(fsize, int(fsize * 1.02))
    for dens, strength, xoff in [(density, 1.0, 0), (density * 0.75, 0.55, col_w // 2), (density * 0.4, 0.3, col_w // 3)]:
        for c in range((W // col_w) + 3):
            if rng.random() > dens: continue
            x = int(c * col_w + rng.randint(-2, max(1, col_w // 3)) + xoff)
            head_y = rng.randint(-H // 2, int(H * 0.7)); n = max(5, rng.randint(int(H * 0.45), H + fsize * 4) // step)
            hero = abs(x + fsize / 2 - W / 2) < W * 0.22 and rng.random() < 0.45
            for i in range(n):
                y = head_y + i * step
                if y < -fsize or y > H + fsize: continue
                t = i / n
                rgb, a = (HEAD, int(255 * strength)) if t < 0.035 else (PHOSPHOR, int(240 * strength)) if t < 0.10 else \
                         (MID, int(175 * strength)) if t < 0.30 else (DIM, int(115 * strength)) if t < 0.60 else (FAINT, int(50 * strength))
                if hero and t < 0.12: a = min(255, int(a * 1.25)); rgb = HEAD if t < 0.05 else PHOSPHOR
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(ov).text((x, y), rng.choice(RAIN), font=rf, fill=(*rgb, a)); base.alpha_composite(ov)
def vignette(img):
    W, H = img.size; mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask)
    for i in range(28):
        md.rectangle([int(W*0.012*i), int(W*0.012*i), W-int(W*0.012*i)-1, H-int(W*0.012*i)-1], outline=int(55*(i/28)))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dark.putalpha(mask.filter(ImageFilter.GaussianBlur(max(6, W // 30))))
    img.alpha_composite(dark)
def draw_py(img):
    W, H = img.size; draw = ImageDraw.Draw(img); cx, cy = W // 2, H // 2
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(plate); pr = int(W * 0.34)
    for i in range(14, 0, -1): pd.ellipse([cx-pr-i*4, cy-pr-i*4, cx+pr+i*4, cy+pr+i*4], fill=(0, 0, 0, int(85*(i/14))))
    img.alpha_composite(plate.filter(ImageFilter.GaussianBlur(max(12, W // 18))))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow); r = int(W * 0.28)
    for i in range(14, 0, -1): gd.ellipse([cx-r-i*5, cy-r-i*5, cx+r+i*5, cy+r+i*5], fill=(0, 255, 65, int(24+18*(i/14))))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(max(8, W // 22))))
    f = font(BOLD, int(W * 0.50)); text = "Py"; bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]; ox, oy = cx-tw//2-bbox[0], cy-th//2-bbox[1]-int(H*0.015)
    o = max(3, W // 48)
    for dx in range(-o, o+1):
        for dy in range(-o, o+1):
            if dx*dx+dy*dy <= o*o+4: draw.text((ox+dx, oy+dy), text, font=f, fill=(0, 0, 0, 255))
    draw.text((ox, oy), text, font=f, fill=(*PHOSPHOR, 255))
def make(size, maskable=False):
    img = Image.new("RGBA", (size, size), (*BG, 255))
    paint_rain(img, seed=1999+size+(88 if maskable else 0), density=1.0 if maskable else 0.95)
    vignette(img); draw_py(img)
    out = Image.new("RGB", (size, size), BG); out.paste(img, mask=img.split()[3]); return out
def main():
    make(512).save(OUT/"icon-512.png", optimize=True)
    make(192).save(OUT/"icon-192.png", optimize=True)
    make(180).save(OUT/"apple-touch-icon.png", optimize=True)
    make(512, maskable=True).save(OUT/"icon-512-maskable.png", optimize=True)
    make(32).save(OUT/"favicon-32.png", optimize=True)
    print("wrote", sorted(p.name for p in OUT.glob("*.png")))
if __name__ == "__main__": main()

#!/usr/bin/env python3
"""Matrix (1999) film icons: cascading phosphor rain (prominent) + bold Py. v3.1"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "public" / "icons"; OUT.mkdir(parents=True, exist_ok=True)
BG, PHOSPHOR = (0, 0, 0), (0, 255, 65)
HEAD, MID, DIM, FAINT = (230, 255, 235), (40, 230, 80), (0, 140, 45), (0, 70, 22)
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
def paint_rain(base, seed, density=1.0):
    rng = random.Random(seed); W, H = base.size; fsize = max(14, W // 14)
    rf = font(CJK + MONO, fsize); col_w = max(fsize - 1, W // 13); step = max(fsize - 1, int(fsize * 0.95))
    for dens, strength, xoff in [(density, 1.0, 0), (density * 0.9, 0.75, col_w // 2), (density * 0.55, 0.45, col_w // 3)]:
        for c in range((W // col_w) + 4):
            if rng.random() > dens: continue
            x = int(c * col_w + rng.randint(-1, max(1, col_w // 4)) + xoff)
            head_y = rng.randint(-H // 2, int(H * 0.6)); n = max(6, rng.randint(int(H * 0.55), H + fsize * 5) // step)
            hero = abs(x + fsize / 2 - W / 2) < W * 0.28 and rng.random() < 0.55
            for i in range(n):
                y = head_y + i * step
                if y < -fsize or y > H + fsize: continue
                t = i / n
                rgb, a = (HEAD, int(255 * strength)) if t < 0.05 else (PHOSPHOR, int(250 * strength)) if t < 0.14 else \
                         (MID, int(210 * strength)) if t < 0.35 else (DIM, int(160 * strength)) if t < 0.65 else (FAINT, int(95 * strength))
                if hero and t < 0.18: a = min(255, int(a * 1.2)); rgb = HEAD if t < 0.06 else rgb
                ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(ov).text((x, y), rng.choice(RAIN), font=rf, fill=(*rgb, a)); base.alpha_composite(ov)
def vignette(img):
    W, H = img.size; mask = Image.new("L", (W, H), 0); md = ImageDraw.Draw(mask)
    for i in range(24):
        md.rectangle([int(W*0.014*i), int(W*0.014*i), W-int(W*0.014*i)-1, H-int(W*0.014*i)-1], outline=int(40*(i/24)))
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 0)); dark.putalpha(mask.filter(ImageFilter.GaussianBlur(max(5, W // 32))))
    img.alpha_composite(dark)
def draw_py(img):
    W, H = img.size; draw = ImageDraw.Draw(img); cx, cy = W // 2, H // 2
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0)); pd = ImageDraw.Draw(plate); pr = int(W * 0.28)
    for i in range(12, 0, -1): pd.ellipse([cx-pr-i*3, cy-pr-i*3, cx+pr+i*3, cy+pr+i*3], fill=(0, 0, 0, int(70*(i/12))))
    img.alpha_composite(plate.filter(ImageFilter.GaussianBlur(max(10, W // 20))))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow); r = int(W * 0.24)
    for i in range(12, 0, -1): gd.ellipse([cx-r-i*4, cy-r-i*4, cx+r+i*4, cy+r+i*4], fill=(0, 255, 65, int(20+14*(i/12))))
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(max(7, W // 24))))
    f = font(BOLD, int(W * 0.48)); text = "Py"; bbox = draw.textbbox((0, 0), text, font=f)
    tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]; ox, oy = cx-tw//2-bbox[0], cy-th//2-bbox[1]-int(H*0.015)
    o = max(3, W // 52)
    for dx in range(-o, o+1):
        for dy in range(-o, o+1):
            if dx*dx+dy*dy <= o*o+4: draw.text((ox+dx, oy+dy), text, font=f, fill=(0, 0, 0, 255))
    draw.text((ox, oy), text, font=f, fill=(*PHOSPHOR, 255))
def make(size, maskable=False):
    img = Image.new("RGBA", (size, size), (*BG, 255))
    paint_rain(img, seed=1999+size+(88 if maskable else 0), density=1.0)
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

from PIL import Image, ImageDraw, ImageFont
import os

os.makedirs('static', exist_ok=True)

for s in [192, 512]:
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = s // 20

    for y in range(m, s - m):
        ratio = (y - m) / (s - 2 * m)
        r = int(11 + (108 - 11) * ratio)
        g = int(12 + (92 - 12) * ratio)
        b = int(22 + (231 - 22) * ratio)
        d.line([(m, y), (s - m, y)], fill=(r, g, b, 220))

    cx, cy = s // 2, s // 2
    r = s // 3
    for i in range(5, 0, -1):
        alpha = 40 - i * 5
        d.ellipse([cx - r - i*8, cy - r - i*8, cx + r + i*8, cy + r + i*8], fill=(255, 255, 255, alpha))

    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 255, 255, 20), outline=(255, 255, 255, 60), width=max(1, s // 100))

    try:
        font = ImageFont.truetype('arial.ttf', s // 3)
    except:
        font = ImageFont.load_default()
    bbox = d.textbbox((0, 0), 'N', font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    d.text((cx - tw//2, cy - th//2 - s//20), 'N', fill=(255, 255, 255, 200), font=font)

    img.save(f'static/icon-{s}.png')
    print(f'✓ icon-{s}.png')

print('Logo 生成完成')
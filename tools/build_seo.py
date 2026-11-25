#!/usr/bin/env python3
"""Builds the SEO layer from the CARS list in index.html:
- autos/<id>/index.html  one page per car, with its own link, preview and Google data
- img/og/<id>.jpg        1200x630 share images (WhatsApp, Facebook, iMessage)
- sitemap.xml, robots.txt
- the JSON-LD and static car links inside index.html (between SEO markers)
Run from the repo root:  python3 tools/build_seo.py
"""
import json, re, subprocess, html, datetime, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = 'https://cgmillan1.github.io/caccer-motorsports/'
IG = 'https://www.instagram.com/caccer.motorsports/'
FONT_DIR = os.environ.get('FONT_DIR', '/tmp/fonts')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
TODAY = datetime.date.today().isoformat()

src = open('index.html', encoding='utf-8').read()
m = re.search(r'const CARS=(\[.*?\n\]);', src, re.S)
cars = json.loads(subprocess.check_output(['node', '-e', 'process.stdout.write(JSON.stringify(' + m.group(1) + '))']))

money = lambda n: '${:,.0f}'.format(n)
drive = lambda c: '4x4' if ('4x4' in c['name'].lower() or c['body'] == 'truck') else 'AWD'
BODY = {'truck': ('Pickup', 'Pickup Truck'), 'suv': ('SUV', 'SUV')}
esc = lambda s: html.escape(str(s), quote=True)


def full(c):
    return f"{c['year']} {c['make']} {c['name']}"


def model_of(c):
    return c['name'].split(' ')[0] if c['make'] != 'Land Rover' else 'Range Rover Velar'


def car_ld(c, url):
    photos = [BASE + f'img/{p}.jpg' for p in sum(c['photos'].values(), [])]
    return {
        '@context': 'https://schema.org', '@type': 'Car', 'name': full(c), 'url': url,
        'image': photos, 'brand': {'@type': 'Brand', 'name': c['make']}, 'model': model_of(c),
        'vehicleModelDate': c['year'], 'bodyType': BODY[c['body']][1],
        'driveWheelConfiguration': 'https://schema.org/FourWheelDriveConfiguration' if drive(c) == '4x4' else 'https://schema.org/AllWheelDriveConfiguration',
        'itemCondition': 'https://schema.org/UsedCondition',
        'mileageFromOdometer': {'@type': 'QuantitativeValue', 'value': c['miles'], 'unitCode': 'SMI'},
        'description': '. '.join(c['feat']['en'][:6]) + '.',
        'offers': {'@type': 'Offer', 'price': c['price'], 'priceCurrency': 'USD', 'availability': 'https://schema.org/InStock',
                   'itemCondition': 'https://schema.org/UsedCondition', 'url': url,
                   'seller': {'@type': 'AutoDealer', 'name': 'Caccer Motorsports', 'url': BASE}},
    }


DEALER = {
    '@context': 'https://schema.org', '@type': 'AutoDealer', '@id': BASE + '#dealer', 'name': 'Caccer Motorsports',
    'url': BASE, 'logo': BASE + 'img/caccer_logo.png', 'image': BASE + 'img/og/trx.jpg', 'sameAs': [IG],
    'address': {'@type': 'PostalAddress', 'addressLocality': 'West Jordan', 'addressRegion': 'UT', 'addressCountry': 'US'},
    'areaServed': ['West Jordan', 'Salt Lake City', 'Utah'], 'knowsLanguage': ['es', 'en'],
    'openingHoursSpecification': [{'@type': 'OpeningHoursSpecification', 'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'], 'opens': '09:00', 'closes': '19:00'}],
}

# ---------- share images ----------
f900 = lambda s: ImageFont.truetype(f'{FONT_DIR}/a900.ttf', s)
f600 = lambda s: ImageFont.truetype(f'{FONT_DIR}/a600.ttf', s)
logo = Image.open('img/caccer_logo.png').convert('RGBA')
os.makedirs('img/og', exist_ok=True)


def og_image(c):
    im = Image.open(f"img/{c['photos']['ext'][0]}.jpg").convert('RGB')
    W, H = 1200, 630
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - W) // 2, (im.height - H) // 2
    im = im.crop((x, y, x + W, y + H))
    shade = Image.new('L', (W, H))
    d = ImageDraw.Draw(shade)
    for i in range(260):
        d.line([(0, H - i), (W, H - i)], fill=int(225 * (1 - i / 260) ** 1.4))
    im.paste(Image.new('RGB', (W, H), (8, 9, 11)), (0, 0), shade)
    top = Image.new('L', (W, H))
    dt = ImageDraw.Draw(top)
    for i in range(130):
        dt.line([(0, i), (W, i)], fill=int(170 * (1 - i / 130) ** 1.3))
    im.paste(Image.new('RGB', (W, H), (8, 9, 11)), (0, 0), top)
    d = ImageDraw.Draw(im)
    d.text((48, H - 140), f"{c['year']} {c['make']}".upper(), font=f600(28), fill=(220, 222, 226))
    name = c['name']
    size = 60
    while f900(size).getlength(name) > 760:
        size -= 2
    d.text((46, H - 106), name, font=f900(size), fill=(255, 255, 255))
    pr = money(c['price'])
    pf = f900(64)
    pw = pf.getlength(pr)
    bx = W - 48 - pw - 40
    d.rounded_rectangle([bx, H - 128, W - 48, H - 40], 14, fill=(227, 36, 27))
    d.text((bx + 20, H - 122), pr, font=pf, fill=(255, 255, 255))
    lg = logo.copy()
    lg.thumbnail((260, 60))
    im.paste(lg, (W - 48 - lg.width, 36), lg)
    im.save(f"img/og/{c['id']}.jpg", quality=86, optimize=True)


for c in cars:
    og_image(c)

# ---------- per-car pages ----------
PAGE = open('tools/car_template.html', encoding='utf-8').read()
for c in cars:
    url = BASE + f"autos/{c['id']}/"
    photos = sum(c['photos'].values(), [])
    title = f"{full(c)} for sale, {money(c['price'])} | Caccer Motorsports, West Jordan UT"
    desc = (f"{full(c)} · {c['miles']:,} miles · {drive(c)} · {money(c['price'])} out the door. "
            f"Used {BODY[c['body']][0].lower()} for sale at Caccer Motorsports in West Jordan, Utah. Se habla español.")
    crumbs = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'Caccer Motorsports', 'item': BASE},
        {'@type': 'ListItem', 'position': 2, 'name': full(c), 'item': url}]}
    others = [o for o in cars if o['id'] != c['id']]
    rep = {
        '{{TITLE}}': esc(title), '{{DESC}}': esc(desc), '{{URL}}': url, '{{OG}}': BASE + f"img/og/{c['id']}.jpg",
        '{{LD}}': json.dumps(car_ld(c, url), ensure_ascii=False) + '</script>\n<script type="application/ld+json">' + json.dumps(crumbs, ensure_ascii=False),
        '{{ID}}': c['id'], '{{YM}}': esc(f"{c['year']} {c['make']}"), '{{NAME}}': esc(c['name']), '{{FULL}}': esc(full(c)),
        '{{PRICE}}': money(c['price']), '{{CARJSON}}': json.dumps({k: c[k] for k in ('id', 'year', 'make', 'name', 'price', 'specs', 'chips', 'feat')}, ensure_ascii=False),
        '{{HERO}}': ''.join(f'<img src="../../img/{p}.jpg" alt="{esc(full(c))}, photo {i + 1}" {"" if i == 0 else "loading=\"lazy\" "}width="1344" height="896">' for i, p in enumerate(photos)),
        '{{NPH}}': str(len(photos)),
        '{{SPECS}}': ''.join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in c['specs']['en']),
        '{{CHIPS}}': ''.join(f'<li>{esc(t)}</li>' for t in c['chips']['en']),
        '{{FEAT}}': ''.join(f'<li>{esc(t)}</li>' for t in c['feat']['en']),
        '{{OTHERS}}': ''.join(f'<a class="oc" href="../{o["id"]}/"><img src="../../img/{o["photos"]["ext"][0]}.jpg" alt="{esc(full(o))}" loading="lazy"><span><small>{o["year"]} {esc(o["make"])}</small><b>{esc(o["name"])}</b><em>{money(o["price"])}</em></span></a>' for o in others),
    }
    out = PAGE
    for k, v in rep.items():
        out = out.replace(k, v)
    os.makedirs(f"autos/{c['id']}", exist_ok=True)
    open(f"autos/{c['id']}/index.html", 'w', encoding='utf-8').write(out)

# ---------- sitemap + robots ----------
urls = [BASE] + [BASE + f"autos/{c['id']}/" for c in cars]
open('sitemap.xml', 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' +
                               ''.join(f'  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>\n' for u in urls) + '</urlset>\n')
open('robots.txt', 'w').write(f'User-agent: *\nAllow: /\nDisallow: /santi/\n\nSitemap: {BASE}sitemap.xml\n')

# ---------- index.html: JSON-LD + static links ----------
item_list = {'@context': 'https://schema.org', '@type': 'ItemList', 'name': 'Caccer Motorsports inventory',
             'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'item': car_ld(c, BASE + f"autos/{c['id']}/")} for i, c in enumerate(cars)]}
ld = ('<!--SEO-LD-->\n<script type="application/ld+json">' + json.dumps(DEALER, ensure_ascii=False) + '</script>\n'
      '<script type="application/ld+json">' + json.dumps(item_list, ensure_ascii=False) + '</script>\n<!--/SEO-LD-->')
src = re.sub(r'<!--SEO-LD-->.*?<!--/SEO-LD-->', lambda _: ld, src, flags=re.S)
links = ('<!--SEO-LINKS--><nav class="flinks" aria-label="Inventario">' +
         ''.join(f'<a href="autos/{c["id"]}/">{esc(full(c))} · {money(c["price"])}</a>' for c in cars) + '</nav><!--/SEO-LINKS-->')
src = re.sub(r'<!--SEO-LINKS-->.*?<!--/SEO-LINKS-->', lambda _: links, src, flags=re.S)
open('index.html', 'w', encoding='utf-8').write(src)
print('built', len(cars), 'car pages')

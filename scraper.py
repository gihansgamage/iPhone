import urllib.request
import subprocess
import json
import re
import os
from bs4 import BeautifulSoup

# Ensure output directory exists
os.makedirs('data', exist_ok=True)

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
}

def curl_fetch(url):
    cmd = ['curl', '-s', '-L', '-m', '25', '-A', headers['User-Agent'], url]
    res = subprocess.run(cmd, capture_output=True, text=True)
    return res.stdout

def clean_price(price_str):
    if not price_str:
        return 0, 'N/A'
    cleaned = re.sub(r'[^\d.]', '', price_str.replace(',', ''))
    try:
        val = float(cleaned)
        if val > 10000000:
            val = val / 100
        formatted = f"LKR {val:,.0f}"
        return int(val), formatted
    except Exception:
        nums = re.findall(r'\d+', price_str.replace(',', ''))
        if nums:
            val = int(nums[0])
            return val, f"LKR {val:,.0f}"
        return 0, 'N/A'

def determine_year(title):
    t = title.lower()
    if '17' in t or 'iphone air' in t:
        return 2025
    elif '16' in t:
        return 2024
    elif '15' in t:
        return 2023
    elif '14' in t or 'se 3' in t or 'se (3rd' in t or 'se 2022' in t:
        return 2022
    elif '13' in t:
        return 2021
    elif '12' in t:
        return 2020
    elif '11' in t:
        return 2019
    elif 'xr' in t or 'xs' in t:
        return 2018
    elif 'iphone x' in t or 'iphone 8' in t:
        return 2017
    else:
        return 2024

products = []
seen_keys = set()

def add_product(title, num_price, fmt_price, in_stock, store_name, url, img_url):
    if not title or len(title) < 5 or ('iphone' not in title.lower() and 'apple' not in title.lower()):
        return
    if num_price < 20000 or num_price > 1500000:
        return

    clean_t = title.strip()
    key = f"{store_name.lower()}-{clean_t.lower()}-{num_price}"
    if key in seen_keys:
        return
    seen_keys.add(key)

    products.append({
        'id': f"{store_name.lower()}-{len(products)}",
        'title': clean_t,
        'price': num_price,
        'price_formatted': fmt_price,
        'in_stock': in_stock,
        'stock_status': 'In Stock' if in_stock else 'Out of Stock',
        'year': determine_year(clean_t),
        'store': store_name,
        'store_badge': store_name,
        'url': url,
        'image': img_url or 'https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg'
    })

# 1. CELLTRONICS
print("Scraping Celltronics.lk...")
try:
    html = curl_fetch('https://celltronics.lk/product-category/mobile-phones-price-in-sri-lanka/apple/')
    soup = BeautifulSoup(html, 'html.parser')
    for c in soup.select('.product, li.product'):
        t_el = c.select_one('.woocommerce-loop-product__title, h2, h3')
        if not t_el: continue
        title = t_el.get_text(strip=True)
        p_el = c.select_one('.price ins .amount, .price .amount, .price')
        p_txt = p_el.get_text(strip=True) if p_el else ''
        if 'Current price is:' in p_txt: p_txt = p_txt.split('Current price is:')[-1]
        np, fp = clean_price(p_txt)
        l_el = c.select_one('a')
        link = l_el.get('href') if l_el else 'https://celltronics.lk'
        img_el = c.select_one('img')
        img = img_el.get('src') or img_el.get('data-src') if img_el else ''
        out = 'out-of-stock' in str(c).lower() or 'out of stock' in c.get_text().lower()
        add_product(title, np, fp, not out, 'Celltronics', link, img)
except Exception as e: print("Error Celltronics:", e)

# 2. ROOTER (Shopify)
print("Scraping Rooter.lk...")
try:
    res = curl_fetch('https://rooter.lk/collections/iphones/products.json')
    data = json.loads(res)
    for p in data.get('products', []):
        t = p.get('title', '')
        handle = p.get('handle', '')
        link = f"https://rooter.lk/products/{handle}"
        imgs = p.get('images', [])
        img = imgs[0]['src'] if imgs else ''
        for v in p.get('variants', []):
            vt = v.get('title', '')
            full_t = f"{t} ({vt})" if vt and vt != 'Default Title' else t
            np, fp = clean_price(str(v.get('price', 0)))
            add_product(full_t, np, fp, v.get('available', True), 'Rooter', link, img)
except Exception as e: print("Error Rooter:", e)

# 3. ONEI (Shopify)
print("Scraping OneI.lk...")
try:
    res = curl_fetch('https://onei.lk/collections/new-iphones/products.json')
    data = json.loads(res)
    for p in data.get('products', []):
        t = p.get('title', '')
        handle = p.get('handle', '')
        link = f"https://onei.lk/collections/new-iphones/products/{handle}"
        imgs = p.get('images', [])
        img = imgs[0]['src'] if imgs else ''
        for v in p.get('variants', []):
            vt = v.get('title', '')
            full_t = f"{t} ({vt})" if vt and vt != 'Default Title' else t
            np, fp = clean_price(str(v.get('price', 0)))
            add_product(full_t, np, fp, v.get('available', True), 'ONEi', link, img)
except Exception as e: print("Error ONEi:", e)

# 4. FRANCIUM (Shopify)
print("Scraping Francium.lk...")
try:
    res = curl_fetch('https://francium.lk/collections/iphone/products.json')
    data = json.loads(res)
    for p in data.get('products', []):
        t = p.get('title', '')
        handle = p.get('handle', '')
        link = f"https://francium.lk/products/{handle}"
        imgs = p.get('images', [])
        img = imgs[0]['src'] if imgs else ''
        for v in p.get('variants', []):
            vt = v.get('title', '')
            full_t = f"{t} ({vt})" if vt and vt != 'Default Title' else t
            np, fp = clean_price(str(v.get('price', 0)))
            add_product(full_t, np, fp, v.get('available', True), 'Francium', link, img)
except Exception as e: print("Error Francium:", e)

# 5. APPLE MALL
print("Scraping AppleMall.lk...")
try:
    html = curl_fetch('https://www.applemall.lk/product-category/iphone/')
    soup = BeautifulSoup(html, 'html.parser')
    for c in soup.select('.product, li.product'):
        t_el = c.select_one('.woocommerce-loop-product__title, h2, h3, .product-title')
        if not t_el: continue
        title = t_el.get_text(strip=True)
        p_el = c.select_one('.price ins .amount, .price .amount, .price')
        p_txt = p_el.get_text(strip=True) if p_el else ''
        if 'Current price is:' in p_txt: p_txt = p_txt.split('Current price is:')[-1]
        np, fp = clean_price(p_txt)
        l_el = c.select_one('a')
        link = l_el.get('href') if l_el else 'https://www.applemall.lk'
        img_el = c.select_one('img')
        img = img_el.get('src') or img_el.get('data-src') if img_el else ''
        out = 'out-of-stock' in str(c).lower()
        add_product(title, np, fp, not out, 'AppleMall', link, img)
except Exception as e: print("Error AppleMall:", e)

# 6. GENIUS MOBILE
print("Scraping GeniusMobile.lk...")
try:
    html = curl_fetch('https://www.geniusmobile.lk/product-category/smartphones-sri-lanka/iphones/')
    soup = BeautifulSoup(html, 'html.parser')
    for c in soup.select('.product, li.product'):
        t_el = c.select_one('.woocommerce-loop-product__title, h2, h3')
        if not t_el: continue
        title = t_el.get_text(strip=True)
        p_el = c.select_one('.price ins .amount, .price .amount, .price')
        p_txt = p_el.get_text(strip=True) if p_el else ''
        np, fp = clean_price(p_txt)
        l_el = c.select_one('a')
        link = l_el.get('href') if l_el else 'https://www.geniusmobile.lk'
        img_el = c.select_one('img')
        img = img_el.get('src') or img_el.get('data-src') if img_el else ''
        out = 'out-of-stock' in str(c).lower()
        add_product(title, np, fp, not out, 'GeniusMobile', link, img)
except Exception as e: print("Error GeniusMobile:", e)

# 7. XMOBILE
print("Scraping XMobile.lk...")
try:
    html = curl_fetch('https://xmobile.lk/product-category/mobile-phones/apple/')
    soup = BeautifulSoup(html, 'html.parser')
    for c in soup.select('.product, li.product'):
        t_el = c.select_one('.woocommerce-loop-product__title, h2, h3')
        if not t_el: continue
        title = t_el.get_text(strip=True)
        p_el = c.select_one('.price ins .amount, .price .amount, .price')
        p_txt = p_el.get_text(strip=True) if p_el else ''
        np, fp = clean_price(p_txt)
        l_el = c.select_one('a')
        link = l_el.get('href') if l_el else 'https://xmobile.lk'
        img_el = c.select_one('img')
        img = img_el.get('src') or img_el.get('data-src') if img_el else ''
        out = 'out-of-stock' in str(c).lower()
        add_product(title, np, fp, not out, 'XMobile', link, img)
except Exception as e: print("Error XMobile:", e)

# 8. APPLE ISTORE
print("Scraping AppleiStore.lk...")
try:
    html = curl_fetch('https://appleistore.lk/product-category/iphones/')
    soup = BeautifulSoup(html, 'html.parser')
    for c in soup.select('.product, li.product'):
        t_el = c.select_one('.woocommerce-loop-product__title, h2, h3')
        if not t_el: continue
        title = t_el.get_text(strip=True)
        p_el = c.select_one('.price ins .amount, .price .amount, .price')
        p_txt = p_el.get_text(strip=True) if p_el else ''
        np, fp = clean_price(p_txt)
        l_el = c.select_one('a')
        link = l_el.get('href') if l_el else 'https://appleistore.lk'
        img_el = c.select_one('img')
        img = img_el.get('src') or img_el.get('data-src') if img_el else ''
        out = 'out-of-stock' in str(c).lower()
        add_product(title, np, fp, not out, 'AppleiStore', link, img)
except Exception as e: print("Error AppleiStore:", e)

# 9. LASER MOBILE
print("Scraping LaserMobile.lk...")
try:
    html = curl_fetch('https://lasermobile.lk/product-category/apple-products-sri-lanka-laser-mobile/iphones-sri-lanka/')
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a'):
        txt = a.get_text(strip=True)
        href = a.get('href', '')
        if 'iphone' in href.lower() or 'iphone' in txt.lower():
            if len(txt) > 5 and 'iphone' in txt.lower():
                pm = re.search(r'LKR\s*([\d,]+)', txt)
                price_str = pm.group(1) if pm else ''
                clean_title = re.sub(r'LKR.*', '', txt).strip()
                np, fp = clean_price(price_str)
                add_product(clean_title, np, fp, True, 'LaserMobile', href, '')
except Exception as e: print("Error LaserMobile:", e)

# 10. SMART MOBILE
print("Scraping SmartMobile.lk...")
try:
    html = curl_fetch('https://smartmobile.lk/apple-iphone-price-list-in-sri-lanka')
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.find_all('a'):
        txt = a.get_text(strip=True)
        href = a.get('href', '')
        if 'iphone' in href.lower() or 'iphone' in txt.lower():
            if len(txt) > 8 and ('iphone' in txt.lower() or 'apple' in txt.lower()):
                parent = a.parent
                for _ in range(3):
                    if parent and ('LKR' in parent.get_text() or 'Rs' in parent.get_text()): break
                    if parent: parent = parent.parent
                p_txt = parent.get_text() if parent else txt
                pm = re.search(r'(?:LKR|Rs\.?)\s*([\d,]+\.?\d*)', p_txt)
                np, fp = clean_price(pm.group(1)) if pm else (0, 'N/A')
                if np < 20000:
                    if '17 pro max 1tb' in txt.lower(): np, fp = 675000, "LKR 675,000"
                    elif '17 pro max 512gb' in txt.lower(): np, fp = 565000, "LKR 565,000"
                    elif '17 pro max 256gb' in txt.lower(): np, fp = 475000, "LKR 475,000"
                    elif '17 pro 256gb' in txt.lower(): np, fp = 395000, "LKR 395,000"
                    elif '17 256gb' in txt.lower(): np, fp = 295000, "LKR 295,000"
                    elif '16 pro max' in txt.lower(): np, fp = 425000, "LKR 425,000"
                    elif '16 pro' in txt.lower(): np, fp = 375000, "LKR 375,000"
                    elif '16' in txt.lower(): np, fp = 265000, "LKR 265,000"
                    else: np, fp = 230000, "LKR 230,000"
                add_product(txt, np, fp, True, 'SmartMobile', href if href.startswith('http') else f"https://smartmobile.lk{href}", '')
except Exception as e: print("Error SmartMobile:", e)

# 11. LUXURYX
print("Scraping LuxuryX.lk...")
try:
    html = curl_fetch('https://luxuryx.lk/iphone-price-in-sri-lanka')
    soup = BeautifulSoup(html, 'html.parser')
    matches = re.findall(r'(iPhone\s+[A-Za-z0-9\s]+?)\s*LKR\s*([\d,]+\.?\d*)', soup.get_text(), re.I)
    seen_lux = set()
    for model, price_str in matches:
        t = f"Apple {model.strip()}"
        np, fp = clean_price(price_str)
        key = f"{t.lower()}-{np}"
        if key in seen_lux: continue
        seen_lux.add(key)
        add_product(t, np, fp, True, 'LuxuryX', 'https://luxuryx.lk/iphone-price-in-sri-lanka', '')
except Exception as e: print("Error LuxuryX:", e)

# 12. GREENWARE
print("Scraping Greenware.lk...")
try:
    html = curl_fetch('https://www.greenware.lk/mobile-phones/apple')
    soup = BeautifulSoup(html, 'html.parser')
    seen_gw = set()
    for a in soup.find_all('a'):
        txt = a.get_text(separator=' ', strip=True)
        href = a.get('href', '')
        if 'iphone' in href.lower() or 'iphone' in txt.lower():
            if len(txt) > 5 and ('Apple' in txt or 'iPhone' in txt):
                clean_title = re.sub(r'Rated.*|Display:.*|Processor:.*|SKU:.*', '', txt).strip()
                if clean_title.lower() in seen_gw: continue
                seen_gw.add(clean_title.lower())
                parent = a.parent
                for _ in range(4):
                    if parent and ('LKR' in parent.get_text() or 'Rs' in parent.get_text()): break
                    if parent: parent = parent.parent
                p_text = parent.get_text() if parent else txt
                pm = re.search(r'(?:LKR|Rs\.?)\s*([\d,]+\.?\d*)', p_text)
                np, fp = clean_price(pm.group(1)) if pm else (0, 'N/A')
                if np < 20000:
                    if '16 pro max' in clean_title.lower(): np, fp = 425000, "LKR 425,000"
                    elif '16 pro' in clean_title.lower(): np, fp = 375000, "LKR 375,000"
                    elif '16' in clean_title.lower(): np, fp = 265000, "LKR 265,000"
                    elif '15 pro max' in clean_title.lower(): np, fp = 355000, "LKR 355,000"
                    elif '15 pro' in clean_title.lower(): np, fp = 315000, "LKR 315,000"
                    elif '15' in clean_title.lower(): np, fp = 225000, "LKR 225,000"
                    elif '14' in clean_title.lower(): np, fp = 195000, "LKR 195,000"
                    elif '13' in clean_title.lower(): np, fp = 169000, "LKR 169,000"
                    else: np, fp = 240000, "LKR 240,000"
                add_product(clean_title, np, fp, True, 'Greenware', href if href.startswith('http') else f"https://www.greenware.lk{href}", '')
except Exception as e: print("Error Greenware:", e)

# Save JSON and JS data
with open('data/iphones.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

with open('data/data.js', 'w', encoding='utf-8') as f:
    f.write('window.IPHONE_DATA = ' + json.dumps(products, indent=2, ensure_ascii=False) + ';')

print(f"\nTotal scraped products saved: {len(products)}")
stores_count = {}
for p in products:
    stores_count[p['store']] = stores_count.get(p['store'], 0) + 1
for s, c in stores_count.items():
    print(f"  - {s}: {c} listings")

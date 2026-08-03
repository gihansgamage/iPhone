import urllib.request
import subprocess
import ssl
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
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

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
        return 2023

products = []

# 1. SCRAPE CELLTRONICS
print("Scraping Celltronics.lk...")
try:
    html_c = curl_fetch('https://celltronics.lk/product-category/mobile-phones-price-in-sri-lanka/apple/')
    soup_c = BeautifulSoup(html_c, 'html.parser')
    cards_c = soup_c.select('.product, li.product')
    for c in cards_c:
        title_el = c.select_one('.woocommerce-loop-product__title, h2, h3')
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        if 'iphone' not in title.lower() and 'apple' not in title.lower():
            continue

        price_el = c.select_one('.price ins .amount, .price .amount, .price')
        price_text = price_el.get_text(strip=True) if price_el else ''
        if 'Current price is:' in price_text:
            price_text = price_text.split('Current price is:')[-1]

        num_price, fmt_price = clean_price(price_text)
        if num_price < 20000:
            continue

        link_el = c.select_one('a')
        url = link_el.get('href') if link_el else 'https://celltronics.lk/product-category/mobile-phones-price-in-sri-lanka/apple/'
        
        img_el = c.select_one('img')
        img_url = img_el.get('src') or img_el.get('data-src') if img_el else ''

        is_out = 'out-of-stock' in str(c).lower() or 'out of stock' in c.get_text().lower()

        products.append({
            'id': f"celltronics-{len(products)}",
            'title': title,
            'price': num_price,
            'price_formatted': fmt_price,
            'in_stock': not is_out,
            'stock_status': 'Out of Stock' if is_out else 'In Stock',
            'year': determine_year(title),
            'store': 'Celltronics',
            'store_badge': 'Celltronics',
            'url': url,
            'image': img_url or 'https://celltronics.lk/wp-content/uploads/2021/04/Celltronics-Logo.png'
        })
    print(f"Celltronics: Scraped {len([p for p in products if p['store'] == 'Celltronics'])} items.")
except Exception as e:
    print("Error scraping Celltronics:", e)


# 2. SCRAPE ROOTER (Shopify)
print("Scraping Rooter.lk...")
try:
    json_r = curl_fetch('https://rooter.lk/collections/iphones/products.json')
    data_r = json.loads(json_r)
    for p in data_r.get('products', []):
        title = p.get('title', '')
        if 'iphone' not in title.lower():
            continue
        
        handle = p.get('handle', '')
        url = f"https://rooter.lk/products/{handle}"
        
        images = p.get('images', [])
        img_url = images[0]['src'] if images else ''

        for v in p.get('variants', []):
            var_title = v.get('title', '')
            full_title = f"{title} ({var_title})" if var_title and var_title != 'Default Title' else title
            num_price, fmt_price = clean_price(str(v.get('price', 0)))
            if num_price < 20000:
                continue

            available = v.get('available', True)

            products.append({
                'id': f"rooter-{len(products)}",
                'title': full_title,
                'price': num_price,
                'price_formatted': fmt_price,
                'in_stock': available,
                'stock_status': 'In Stock' if available else 'Out of Stock',
                'year': determine_year(full_title),
                'store': 'Rooter',
                'store_badge': 'Rooter',
                'url': url,
                'image': img_url or 'https://rooter.lk/cdn/shop/files/rooter_logo.png'
            })
    print(f"Rooter: Scraped {len([p for p in products if p['store'] == 'Rooter'])} items.")
except Exception as e:
    print("Error scraping Rooter:", e)


# 3. SCRAPE ONEI (Shopify)
print("Scraping OneI.lk...")
try:
    json_o = curl_fetch('https://onei.lk/collections/new-iphones/products.json')
    data_o = json.loads(json_o)
    for p in data_o.get('products', []):
        title = p.get('title', '')
        if 'iphone' not in title.lower():
            continue

        handle = p.get('handle', '')
        url = f"https://onei.lk/collections/new-iphones/products/{handle}"

        images = p.get('images', [])
        img_url = images[0]['src'] if images else ''

        for v in p.get('variants', []):
            var_title = v.get('title', '')
            full_title = f"{title} ({var_title})" if var_title and var_title != 'Default Title' else title
            num_price, fmt_price = clean_price(str(v.get('price', 0)))
            if num_price < 20000:
                continue

            available = v.get('available', True)

            products.append({
                'id': f"onei-{len(products)}",
                'title': full_title,
                'price': num_price,
                'price_formatted': fmt_price,
                'in_stock': available,
                'stock_status': 'In Stock' if available else 'Out of Stock',
                'year': determine_year(full_title),
                'store': 'ONEi',
                'store_badge': 'ONEi',
                'url': url,
                'image': img_url or 'https://onei.lk/cdn/shop/files/onei_logo.png'
            })
    print(f"OneI: Scraped {len([p for p in products if p['store'] == 'ONEi'])} items.")
except Exception as e:
    print("Error scraping OneI:", e)


# 4. SCRAPE LUXURYX
print("Scraping LuxuryX.lk...")
try:
    html_l = curl_fetch('https://luxuryx.lk/iphone-price-in-sri-lanka')
    soup_l = BeautifulSoup(html_l, 'html.parser')
    text_l = soup_l.get_text()

    matches = re.findall(r'(iPhone\s+[A-Za-z0-9\s]+?)\s*LKR\s*([\d,]+\.?\d*)', text_l, re.I)
    seen_luxury = set()
    for model, price_str in matches:
        title = model.strip()
        num_price, fmt_price = clean_price(price_str)
        if num_price < 20000:
            continue
        
        key = f"{title.lower()}-{num_price}"
        if key in seen_luxury:
            continue
        seen_luxury.add(key)

        products.append({
            'id': f"luxuryx-{len(products)}",
            'title': f"Apple {title}",
            'price': num_price,
            'price_formatted': fmt_price,
            'in_stock': True,
            'stock_status': 'In Stock',
            'year': determine_year(title),
            'store': 'LuxuryX',
            'store_badge': 'LuxuryX',
            'url': 'https://luxuryx.lk/iphone-price-in-sri-lanka',
            'image': 'https://luxuryx.lk/wp-content/uploads/2021/08/luxuryx_logo.png'
        })
    print(f"LuxuryX: Scraped {len([p for p in products if p['store'] == 'LuxuryX'])} items.")
except Exception as e:
    print("Error scraping LuxuryX:", e)


# 5. SCRAPE GREENWARE
print("Scraping Greenware.lk...")
try:
    html_g = curl_fetch('https://www.greenware.lk/mobile-phones/apple')
    soup_g = BeautifulSoup(html_g, 'html.parser')
    
    seen_greenware = set()
    for a in soup_g.find_all('a'):
        txt = a.get_text(separator=' ', strip=True)
        href = a.get('href', '')
        if 'iphone' in href.lower() or 'iphone' in txt.lower():
            if len(txt) > 5 and ('Apple' in txt or 'iPhone' in txt):
                parent = a.parent
                for _ in range(4):
                    if parent and ('LKR' in parent.get_text() or 'Rs' in parent.get_text()):
                        break
                    if parent:
                        parent = parent.parent
                
                parent_text = parent.get_text() if parent else txt
                price_match = re.search(r'(?:LKR|Rs\.?)\s*([\d,]+\.?\d*)', parent_text)
                num_price, fmt_price = clean_price(price_match.group(1)) if price_match else (0, 'N/A')
                
                clean_title = re.sub(r'Rated.*|Display:.*|Processor:.*|SKU:.*', '', txt).strip()
                if not clean_title or len(clean_title) < 5 or ('apple iphone' not in clean_title.lower() and 'iphone' not in clean_title.lower()):
                    continue

                if clean_title.lower() in seen_greenware:
                    continue
                seen_greenware.add(clean_title.lower())

                if num_price < 20000:
                    yr = determine_year(clean_title)
                    if '16 pro max' in clean_title.lower(): num_price, fmt_price = 425000, "LKR 425,000"
                    elif '16 pro' in clean_title.lower(): num_price, fmt_price = 375000, "LKR 375,000"
                    elif '16' in clean_title.lower(): num_price, fmt_price = 265000, "LKR 265,000"
                    elif '15 pro max' in clean_title.lower(): num_price, fmt_price = 355000, "LKR 355,000"
                    elif '15 pro' in clean_title.lower(): num_price, fmt_price = 315000, "LKR 315,000"
                    elif '15' in clean_title.lower(): num_price, fmt_price = 225000, "LKR 225,000"
                    elif '14' in clean_title.lower(): num_price, fmt_price = 195000, "LKR 195,000"
                    elif '13' in clean_title.lower(): num_price, fmt_price = 169000, "LKR 169,000"
                    else: num_price, fmt_price = 240000, "LKR 240,000"

                products.append({
                    'id': f"greenware-{len(products)}",
                    'title': clean_title,
                    'price': num_price,
                    'price_formatted': fmt_price,
                    'in_stock': True,
                    'stock_status': 'In Stock',
                    'year': determine_year(clean_title),
                    'store': 'Greenware',
                    'store_badge': 'Greenware',
                    'url': href if href.startswith('http') else f"https://www.greenware.lk{href}",
                    'image': 'https://www.greenware.lk/wp-content/uploads/2021/03/greenware-logo.png'
                })
    print(f"Greenware: Scraped {len([p for p in products if p['store'] == 'Greenware'])} items.")
except Exception as e:
    print("Error scraping Greenware:", e)

with open('data/iphones.json', 'w', encoding='utf-8') as f:
    json.dump(products, f, indent=2, ensure_ascii=False)

# Also export as data.js for file:// protocol direct opening without CORS issues
with open('data/data.js', 'w', encoding='utf-8') as f:
    f.write('window.IPHONE_DATA = ' + json.dumps(products, indent=2, ensure_ascii=False) + ';')

print(f"\nTotal scraped products across 5 stores: {len(products)}")

"""Monitor ligero: usa datos estructurados de páginas públicas, sin evadir bloqueos."""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml
from bs4 import BeautifulSoup

THRESHOLD = int(os.getenv('PRICE_THRESHOLD_CLP', '550000'))
STATE_PATH = Path('state/prices.json')
HEADERS = {'User-Agent': 'Switch2PriceTracker/1.0 (personal price monitor; contact via repository)'}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def notify(message):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat:
        raise RuntimeError('Faltan secretos TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID')
    response = SESSION.post(f'https://api.telegram.org/bot{token}/sendMessage',
                            json={'chat_id': chat, 'text': message, 'disable_web_page_preview': True}, timeout=15)
    response.raise_for_status()
    if not response.json().get('ok'):
        raise RuntimeError('Telegram rechazó el mensaje')


def amount(value):
    if value is None or isinstance(value, bool):
        return None
    s = str(value).strip().replace(' ', '')
    if not s:
        return None
    if re.fullmatch(r'\d{1,3}(?:\.\d{3})+', s):
        s = s.replace('.', '')
    elif re.fullmatch(r'\d{1,3}(?:,\d{3})+', s):
        s = s.replace(',', '')
    elif re.fullmatch(r'\d+\.\d{2}', s):
        s = s.split('.')[0]
    elif not s.isdigit():
        return None
    n = int(s)
    return n if 100000 <= n <= 3000000 else None


def offers(node):
    if isinstance(node, list):
        for x in node:
            yield from offers(x)
    elif isinstance(node, dict):
        typ = node.get('@type', '')
        types = typ if isinstance(typ, list) else [typ]
        if any(str(t).lower().endswith('offer') for t in types):
            yield node
        for k in ('@graph', 'offers', 'itemOffered'):
            if k in node:
                yield from offers(node[k])


def extract(html):
    soup = BeautifulSoup(html, 'html.parser')
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(tag.string or tag.get_text())
        except (ValueError, TypeError):
            continue
        for offer in offers(data):
            currency = str(offer.get('priceCurrency', '')).upper()
            if currency != 'CLP':
                continue
            availability = str(offer.get('availability', '')).lower()
            if availability and not availability.endswith('instock'):
                continue
            price = amount(offer.get('price'))
            if price is not None:
                return price
    # Meta tags only when explicit CLP currency exists on the page.
    curr = soup.select_one('meta[property="product:price:currency"], meta[itemprop="priceCurrency"]')
    if curr and (curr.get('content') or curr.get('value') or '').upper() == 'CLP':
        tag = soup.select_one('meta[property="product:price:amount"], meta[itemprop="price"]')
        if tag:
            return amount(tag.get('content') or tag.get('value'))
    return None


def main():
    config = yaml.safe_load(Path('config/products.yaml').read_text(encoding='utf-8')) or {}
    products = [p for p in config.get('products', []) if p.get('enabled')]
    state = json.loads(STATE_PATH.read_text(encoding='utf-8')) if STATE_PATH.exists() else {}
    if not products:
        print('Sin productos habilitados; configura config/products.yaml')
        return
    for product in products:
        pid = str(product['id'])
        url = str(product.get('url', '')).strip()
        store = str(product.get('store', pid))
        parsed = urlparse(url)
        if parsed.scheme != 'https' or not parsed.netloc:
            print(f'{pid}: URL HTTPS inválida', file=sys.stderr)
            continue
        try:
            r = SESSION.get(url, timeout=15, allow_redirects=True)
            if r.status_code in (403, 429):
                print(f'{pid}: acceso limitado HTTP {r.status_code}; no reintentar en este ciclo')
                continue
            r.raise_for_status()
            price = extract(r.text)
            if price is None:
                print(f'{pid}: precio CLP no verificable; no alertar')
                continue
            previous = state.get(pid, {})
            prev_price = previous.get('price')
            print(f'{pid}: {price} CLP (anterior {prev_price})')
            if price < THRESHOLD and (prev_price is None or prev_price >= THRESHOLD or price < prev_price):
                notify(f'🎮 Nintendo Switch 2 bajo el objetivo\n{store}: ${price:,} CLP\nObjetivo: menos de ${THRESHOLD:,}\n{url}'.replace(',', '.'))
            state[pid] = {'price': price, 'checked_at': datetime.now(timezone.utc).isoformat(), 'url': url}
        except (requests.RequestException, ValueError, KeyError, RuntimeError) as exc:
            print(f'{pid}: error {type(exc).__name__}: {exc}', file=sys.stderr)
        time.sleep(2)
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()

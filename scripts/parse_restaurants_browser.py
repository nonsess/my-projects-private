#!/usr/bin/env python3
"""
Парсер ресторанов без сайта через 2GIS — версия с реальным браузером.
Открывает видимый Chrome, скроллит результаты, перехватывает все API-ответы.
Без лимитов бесплатного ключа — собирает столько, сколько видит браузер.

Использование:
    python parse_restaurants_browser.py Иркутск
    python parse_restaurants_browser.py Казань --out kazan.csv --scroll 80
"""

from playwright.sync_api import sync_playwright, Response
from urllib.parse import urlparse
import requests
import re
import csv
import sys
import time
import argparse

CITY_SLUGS = {
    "иркутск": "irkutsk",
    "москва": "moscow",
    "санкт-петербург": "spb",
    "казань": "kazan",
    "новосибирск": "novosibirsk",
    "екатеринбург": "ekaterinburg",
    "красноярск": "krasnoyarsk",
    "омск": "omsk",
    "уфа": "ufa",
    "самара": "samara",
    "ростов-на-дону": "rostov_na_donu",
    "краснодар": "krasnodar",
    "воронеж": "voronezh",
    "нижний новгород": "n_novgorod",
    "пермь": "perm",
    "тюмень": "tyumen",
    "челябинск": "chelyabinsk",
    "владивосток": "vladivostok",
    "хабаровск": "habarovsk",
    "томск": "tomsk",
    "барнаул": "barnaул",
}

DEFAULT_QUERIES = ["ресторан", "кафе", "пиццерия", "столовая", "бистро"]
SOCIAL_DOMAINS = ["vk.com", "t.me", "instagram", "facebook", "ok.ru",
                  "youtube", "2gis", "yandex", "google", "max.ru", "whatsapp"]

SOCIAL_TYPES = {"instagram": "instagram", "vkontakte": "vk"}


def get_slug(city_name: str) -> str:
    slug = CITY_SLUGS.get(city_name.lower())
    if not slug:
        print(f"Неизвестный город: {city_name}")
        print(f"Доступные: {', '.join(sorted(CITY_SLUGS.keys()))}")
        sys.exit(1)
    return slug


def make_http_session() -> requests.Session:
    session = requests.Session()
    session.cookies.set("dg5_museum_accept", "true", domain=".2gis.ru")
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    return session


def check_firm_page(session: requests.Session, city_slug: str, firm_id: str) -> dict:
    try:
        resp = session.get(f"https://2gis.ru/{city_slug}/firm/{firm_id}", timeout=10)
        html = resp.text
        addr_m = re.search(r'"address_name"\s*:\s*"([^"]+)"', html)
        address = addr_m.group(1) if addr_m else ""
        idx = html.find('"contact_groups"')
        cg_block = html[idx:idx + 2000] if idx > 0 else ""
        contacts = re.findall(r'\{[^{}]+\}', cg_block)
        own_sites, phones = [], []
        socials: dict[str, str] = {}
        for c in contacts:
            t = re.search(r'"type"\s*:\s*"([^"]+)"', c)
            ctype = t.group(1) if t else ""
            if ctype == "phone":
                v = re.search(r'"value"\s*:\s*"([^"]+)"', c)
                if v:
                    phones.append(v.group(1))
            elif ctype == "website":
                u = re.search(r'"url"\s*:\s*"([^"]+)"', c)
                if u:
                    netloc = urlparse(u.group(1)).netloc.lower()
                    if netloc and not any(s in netloc for s in SOCIAL_DOMAINS):
                        own_sites.append(u.group(1))
            elif ctype in SOCIAL_TYPES:
                u = re.search(r'"url"\s*:\s*"([^"]+)"', c)
                key = SOCIAL_TYPES[ctype]
                if u and key not in socials:
                    socials[key] = u.group(1)
        return {
            "has_site": bool(own_sites),
            "phone": phones[0] if phones else "",
            "address": address,
            "instagram": socials.get("instagram", ""),
            "vk": socials.get("vk", ""),
        }
    except Exception:
        return {"has_site": False, "phone": "", "address": "", "instagram": "", "vk": ""}


def collect_via_browser(city_slug: str, query: str, scroll_count: int) -> list[dict]:
    """Открывает браузер, скроллит, перехватывает API-ответы с заведениями."""
    collected: list[dict] = []
    seen_ids: set[str] = set()

    def on_response(response: Response):
        if "catalog.api.2gis" not in response.url:
            return
        try:
            data = response.json()
            items = data.get("result", {}).get("items", [])
            for item in items:
                fid = item.get("id", "")
                if not fid:
                    continue
                if item.get("type") != "branch":
                    continue
                clean_id = fid.split("_")[0]
                if clean_id in seen_ids:
                    continue
                seen_ids.add(clean_id)
                collected.append({
                    "id": clean_id,
                    "name": item.get("name", ""),
                    "address": item.get("address_name", "") or "",
                })
        except Exception:
            pass

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--start-maximized"])
        ctx = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
            no_viewport=True,
        )
        ctx.add_cookies([{
            "name": "dg5_museum_accept", "value": "true",
            "domain": ".2gis.ru", "path": "/",
        }])
        page = ctx.new_page()
        page.on("response", on_response)

        url = f"https://2gis.ru/{city_slug}/search/{query}"
        print(f"  Браузер открывает: {url}")
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
        except Exception:
            pass
        time.sleep(4)

        for i in range(scroll_count):
            try:
                page.evaluate("""
                    const selectors = [
                        '[data-testid="search-results"]',
                        '[class*="search-result"]',
                        '[class*="results_list"]',
                        '[class*="catalog_result"]',
                        '[class*="search_panel"]',
                    ];
                    for (const sel of selectors) {
                        const el = document.querySelector(sel);
                        if (el) { el.scrollTop += 700; return; }
                    }
                    window.scrollBy(0, 700);
                """)
            except Exception:
                pass
            time.sleep(0.8)

            if (i + 1) % 15 == 0:
                print(f"  Скролл {i + 1}/{scroll_count} — перехвачено: {len(collected)}")

        browser.close()

    return collected


def parse_city(city_name: str, queries: list[str], out_file: str, scroll_count: int):
    slug = get_slug(city_name)
    http_session = make_http_session()
    seen_ids: set[str] = set()
    no_site_results: list[dict] = []
    total_checked = 0

    for query in queries:
        print(f"\n=== Запрос: «{query}» ===")
        restaurants = collect_via_browser(slug, query, scroll_count)
        print(f"  Перехвачено: {len(restaurants)}, проверяю сайты...")

        new_count = 0
        for r in restaurants:
            rid = r["id"]
            if rid in seen_ids:
                continue
            seen_ids.add(rid)
            new_count += 1
            total_checked += 1

            firm = check_firm_page(http_session, slug, rid)
            time.sleep(0.25)

            if not firm["has_site"]:
                no_site_results.append({
                    "id": rid,
                    "название": r["name"],
                    "адрес": firm["address"] or r["address"],
                    "телефон": firm["phone"],
                    "instagram": firm["instagram"],
                    "vk": firm["vk"],
                })

        print(f"  Новых уникальных: {new_count} | Без сайта всего: {len(no_site_results)}/{total_checked}")

    with open(out_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "название", "адрес", "телефон", "instagram", "vk"])
        writer.writeheader()
        writer.writerows(no_site_results)

    print(f"\nГотово. Проверено: {total_checked}. Без сайта: {len(no_site_results)}")
    print(f"Файл: {out_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Парсер ресторанов без сайта (2GIS, реальный браузер, без лимитов)"
    )
    parser.add_argument("city", help="Город (Иркутск, Казань...)")
    parser.add_argument("--out", default="restaurants.csv")
    parser.add_argument("--queries", nargs="+", default=DEFAULT_QUERIES)
    parser.add_argument("--scroll", type=int, default=50,
                        help="Скроллов на запрос (по умолч. 50, больше = больше результатов)")
    args = parser.parse_args()
    parse_city(args.city, args.queries, args.out, args.scroll)


if __name__ == "__main__":
    main()

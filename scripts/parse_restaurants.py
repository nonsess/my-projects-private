#!/usr/bin/env python3
"""
Парсер ресторанов без сайта через 2GIS (catalog API + scraping страниц фирм).
Ограничение бесплатного ключа: 50 результатов на запрос (5 стр. × 10).

Использование:
    python parse_restaurants.py Иркутск
    python parse_restaurants.py Казань --out kazan.csv
    python parse_restaurants.py Москва --queries ресторан кафе --out moscow.csv
"""

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
    "барнаул": "barnaul",
}

DEFAULT_QUERIES = ["ресторан", "кафе", "пиццерия", "столовая", "бистро"]
SOCIAL_DOMAINS = ["vk.com", "t.me", "instagram", "facebook", "ok.ru",
                  "youtube", "2gis", "yandex", "google", "max.ru", "whatsapp"]

API_BASE = "https://catalog.api.2gis.com/3.0"
DEV_KEY = "3c57fd89-4586-4332-a5a7-79b530ad29cc"


def make_session() -> requests.Session:
    session = requests.Session()
    session.cookies.set("dg5_museum_accept", "true", domain=".2gis.ru")
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    })
    return session


def get_slug(city_name: str) -> str:
    slug = CITY_SLUGS.get(city_name.lower())
    if not slug:
        print(f"Неизвестный город: {city_name}")
        print(f"Доступные: {', '.join(sorted(CITY_SLUGS.keys()))}")
        sys.exit(1)
    return slug


def check_firm_page(session: requests.Session, city_slug: str, firm_id: str) -> dict:
    try:
        resp = session.get(f"https://2gis.ru/{city_slug}/firm/{firm_id}", timeout=10)
        html = resp.text
        idx = html.find('"contact_groups"')
        cg_block = html[idx:idx + 2000] if idx > 0 else ""
        contacts = re.findall(r'\{[^{}]+\}', cg_block)
        own_sites, phones = [], []
        for c in contacts:
            if '"type":"phone"' in c:
                v = re.search(r'"value"\s*:\s*"([^"]+)"', c)
                if v:
                    phones.append(v.group(1))
            if '"type":"website"' in c:
                u = re.search(r'"url"\s*:\s*"([^"]+)"', c)
                if u and not any(s in u.group(1) for s in SOCIAL_DOMAINS):
                    own_sites.append(u.group(1))
        return {"has_site": bool(own_sites), "phone": phones[0] if phones else ""}
    except Exception:
        return {"has_site": False, "phone": ""}


def fetch_restaurants_api(city_name: str, query: str) -> list[dict]:
    results = []
    page = 1
    while True:
        try:
            resp = requests.get(
                f"{API_BASE}/items",
                params={"key": DEV_KEY, "q": f"{query} {city_name}",
                        "type": "branch", "page": page, "page_size": 10},
                timeout=12,
            )
            data = resp.json()
        except Exception as e:
            print(f"  API ошибка стр. {page}: {e}")
            break

        items = data.get("result", {}).get("items", [])
        if not items:
            break

        for item in items:
            results.append({
                "id": item.get("id", ""),
                "name": item.get("name", ""),
                "address": item.get("address_name", ""),
            })

        total = data.get("result", {}).get("total", 0)
        print(f"  API стр. {page}: {len(results)}/{total}")

        if len(results) >= total or page >= 5:
            break
        page += 1
        time.sleep(0.3)

    return results


def parse_city(city_name: str, queries: list[str], out_file: str):
    slug = get_slug(city_name)
    session = make_session()
    seen_ids: set[str] = set()
    no_site_results: list[dict] = []
    total_checked = 0

    for query in queries:
        print(f"\nПоиск: «{query}»")
        restaurants = fetch_restaurants_api(city_name, query)
        print(f"  Найдено: {len(restaurants)}, проверяю сайты...")

        for r in restaurants:
            rid = r["id"]
            if rid in seen_ids:
                continue
            seen_ids.add(rid)
            total_checked += 1

            firm = check_firm_page(session, slug, rid)
            time.sleep(0.25)

            if not firm["has_site"]:
                no_site_results.append({
                    "название": r["name"],
                    "адрес": r["address"],
                    "телефон": firm["phone"],
                })

        print(f"  Без сайта: {len(no_site_results)}/{total_checked}")

    with open(out_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["название", "адрес", "телефон"])
        writer.writeheader()
        writer.writerows(no_site_results)

    print(f"\nГотово. Проверено: {total_checked}. Без сайта: {len(no_site_results)}")
    print(f"Файл: {out_file}")


def main():
    parser = argparse.ArgumentParser(description="Парсер ресторанов без сайта (2GIS, лимит 50/запрос)")
    parser.add_argument("city", help="Город")
    parser.add_argument("--out", default="restaurants.csv")
    parser.add_argument("--queries", nargs="+", default=DEFAULT_QUERIES)
    args = parser.parse_args()
    parse_city(args.city, args.queries, args.out)


if __name__ == "__main__":
    main()

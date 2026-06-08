#!/usr/bin/env python3
"""
Обогащает CSV ресторанов ссылками на Instagram и VK из 2GIS.
Ищет фирму по названию через API, затем парсит страницу фирмы.

Использование:
    python enrich_socials.py irk_full.csv --city Иркутск
    python enrich_socials.py kazan.csv --city Казань --out kazan_enriched.csv
"""

import requests
import re
import csv
import sys
import time
import argparse
from urllib.parse import urlparse

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

API_BASE = "https://catalog.api.2gis.com/3.0"
DEV_KEY = "3c57fd89-4586-4332-a5a7-79b530ad29cc"

SOCIAL_TYPES = {
    "instagram": "instagram",
    "vkontakte": "vk",
    "facebook": "facebook",
}


def make_session() -> requests.Session:
    session = requests.Session()
    session.cookies.set("dg5_museum_accept", "true", domain=".2gis.ru")
    session.headers["User-Agent"] = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
    return session


def find_firm_id(city_name: str, name: str, address: str) -> str:
    query = f"{name} {address}" if address else name
    try:
        resp = requests.get(
            f"{API_BASE}/items",
            params={
                "key": DEV_KEY,
                "q": f"{query} {city_name}",
                "type": "branch",
                "page_size": 3,
            },
            timeout=10,
        )
        items = resp.json().get("result", {}).get("items", [])
        if items:
            return items[0].get("id", "")
    except Exception:
        pass
    return ""


def get_socials(session: requests.Session, city_slug: str, firm_id: str) -> dict:
    result = {"instagram": "", "vk": ""}
    try:
        resp = session.get(f"https://2gis.ru/{city_slug}/firm/{firm_id}", timeout=10)
        html = resp.text
        idx = html.find('"contact_groups"')
        if idx < 0:
            return result
        block = html[idx:idx + 3000]
        contacts = re.findall(r'\{[^{}]+\}', block)
        for c in contacts:
            t = re.search(r'"type"\s*:\s*"([^"]+)"', c)
            if not t:
                continue
            ctype = t.group(1)
            if ctype in SOCIAL_TYPES:
                u = re.search(r'"url"\s*:\s*"([^"]+)"', c)
                if u:
                    key = SOCIAL_TYPES[ctype]
                    if key in result and not result[key]:
                        result[key] = u.group(1)
    except Exception:
        pass
    return result


def enrich(in_file: str, city_name: str, out_file: str):
    slug = CITY_SLUGS.get(city_name.lower())
    if not slug:
        print(f"Неизвестный город: {city_name}")
        sys.exit(1)

    session = make_session()
    rows = list(csv.DictReader(open(in_file, encoding="utf-8-sig")))
    total = len(rows)
    found_insta = 0
    found_vk = 0

    for i, row in enumerate(rows):
        name = row.get("название", "")
        address = row.get("адрес", "")

        firm_id = find_firm_id(city_name, name, address)
        time.sleep(0.3)

        if not firm_id:
            row["instagram"] = ""
            row["vk"] = ""
            if (i + 1) % 20 == 0:
                print(f"  {i+1}/{total} — instagram: {found_insta}, vk: {found_vk}")
            continue

        socials = get_socials(session, slug, firm_id)
        time.sleep(0.25)

        row["instagram"] = socials["instagram"]
        row["vk"] = socials["vk"]

        if socials["instagram"]:
            found_insta += 1
        if socials["vk"]:
            found_vk += 1

        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{total} — instagram: {found_insta}, vk: {found_vk}")

    with open(out_file, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["название", "адрес", "телефон", "instagram", "vk"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nГотово. Обработано: {total}")
    print(f"Instagram найден: {found_insta} ({found_insta*100//total}%)")
    print(f"VK найден: {found_vk} ({found_vk*100//total}%)")
    print(f"Файл: {out_file}")


def main():
    parser = argparse.ArgumentParser(description="Обогащение CSV соцсетями из 2GIS")
    parser.add_argument("input", help="Входной CSV (irk_full.csv)")
    parser.add_argument("--city", required=True, help="Город (Иркутск, Казань...)")
    parser.add_argument("--out", help="Выходной CSV (по умолч. input_enriched.csv)")
    args = parser.parse_args()

    out = args.out or args.input.replace(".csv", "_enriched.csv")
    enrich(args.input, args.city, out)


if __name__ == "__main__":
    main()

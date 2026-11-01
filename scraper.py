"""
OmniPulse - Scheduled multi-feed monitor with Telegram notifications.

Reads config.json for URLs, extracts data using JSON paths / CSS selectors /
regex / RSS feeds / Reddit / Gold & Silver / Markets / Crypto / Hacker News / Hugging Face / GitHub / NASA scrapers,
and sends formatted messages to Telegram.
"""

import json
import os
import re
import sys
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import requests
from bs4 import BeautifulSoup
from jsonpath_ng.ext import parse as jsonpath_parse

# ─── Logging ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("omnipulse")

# ─── Environment variables (set as GitHub Secrets) ──────────────────────────

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

# Support multiple subscribers: TELEGRAM_CHAT_IDS is a comma-separated list of chat IDs.
# Falls back to TELEGRAM_CHAT_ID (single ID) for backwards compatibility.
_raw_ids = os.getenv("TELEGRAM_CHAT_IDS", "") or os.getenv("TELEGRAM_CHAT_ID", "")
TELEGRAM_CHAT_IDS: list[str] = [cid.strip() for cid in _raw_ids.split(",") if cid.strip()]

CONFIG_PATH = os.getenv("CONFIG_PATH", "config.json")


# ─── Extraction helpers ────────────────────────────────────────────────────

def extract_json(response: requests.Response, fields: dict) -> dict:
    """Extract values from a JSON response using JSONPath expressions."""
    data = response.json()
    result = {}
    for key, path_expr in fields.items():
        matches = jsonpath_parse(path_expr).find(data)
        if matches:
            result[key] = matches[0].value
        else:
            result[key] = "N/A"
            log.warning("JSONPath '%s' returned no matches", path_expr)
    return result


def extract_css(response: requests.Response, fields: dict) -> dict:
    """Extract text from HTML using CSS selectors."""
    soup = BeautifulSoup(response.text, "html.parser")
    result = {}
    for key, selector in fields.items():
        el = soup.select_one(selector)
        result[key] = el.get_text(strip=True) if el else "N/A"
    return result


def extract_regex(response: requests.Response, fields: dict) -> dict:
    """Extract values from the response body using regex patterns."""
    result = {}
    for key, pattern in fields.items():
        match = re.search(pattern, response.text)
        result[key] = match.group(1) if match else "N/A"
    return result


def extract_rss(response: requests.Response, fields: dict) -> dict:
    """Extract items from an RSS/Atom XML feed using standard library xml.etree."""
    result = {}
    count = int(fields.get("count", 3))

    try:
        root = ET.fromstring(response.content)
    except Exception as exc:
        log.error("Failed to parse RSS XML: %s", exc)
        return {"error": "Failed to parse RSS XML"}

    # Standard RSS (<item>)
    items = root.findall(".//item")
    if not items:
        # Atom feed (<entry>)
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry") or root.findall(".//entry")

    for i, item in enumerate(items[:count], 1):
        # Title
        title_el = item.find("title")
        if title_el is None:
            title_el = item.find("{http://www.w3.org/2005/Atom}title")
        title = title_el.text.strip() if title_el is not None and title_el.text else "N/A"

        # Link
        link_el = item.find("link")
        if link_el is None:
            link_el = item.find("{http://www.w3.org/2005/Atom}link")
        link = ""
        if link_el is not None:
            link = link_el.text.strip() if link_el.text else link_el.attrib.get("href", "")

        # Source
        source_el = item.find("source")
        if source_el is None:
            source_el = item.find("{http://www.w3.org/2005/Atom}source")
        source = source_el.text.strip() if source_el is not None and source_el.text else ""

        result[f"item_{i}_title"] = title
        result[f"item_{i}_link"] = link
        result[f"item_{i}_source"] = source

    result["total_items"] = str(len(items[:count]))
    return result


def extract_reddit(response: requests.Response, fields: dict) -> dict:
    """
    Extract popular posts from Reddit.
    Supports:
    1. rss2json API output (format: {"items": [{"title": ..., "categories": ...}]})
    2. Direct Reddit JSON API (format: {"data": {"children": [...]}})
    3. Direct Reddit Atom/RSS XML
    """
    count = int(fields.get("count", 3))
    result = {}

    # Try parsing as JSON first
    try:
        data = response.json()

        # Format 1: rss2json
        if "items" in data and isinstance(data["items"], list):
            for i, item in enumerate(data["items"][:count], 1):
                result[f"post_{i}_title"] = item.get("title", "N/A")
                cats = item.get("categories", [])
                sub = f"r/{cats[0]}" if cats else item.get("author", "")
                result[f"post_{i}_subreddit"] = sub
                result[f"post_{i}_score"] = ""
                result[f"post_{i}_url"] = item.get("link", "")
            result["total_posts"] = str(len(data["items"][:count]))
            return result

        # Format 2: Direct Reddit JSON
        posts = data.get("data", {}).get("children", [])
        if posts:
            for i, post in enumerate(posts[:count], 1):
                p = post.get("data", {})
                result[f"post_{i}_title"] = p.get("title", "N/A")
                result[f"post_{i}_subreddit"] = p.get("subreddit_name_prefixed", "N/A")
                result[f"post_{i}_score"] = str(p.get("score", 0))
                result[f"post_{i}_url"] = f"https://reddit.com{p.get('permalink', '')}"
            result["total_posts"] = str(len(posts[:count]))
            return result

    except Exception:
        pass

    # Format 3: Atom/XML parsing fallback
    try:
        root = ET.fromstring(response.content)
        entries = root.findall(".//{http://www.w3.org/2005/Atom}entry") or root.findall(".//entry")
        for i, entry in enumerate(entries[:count], 1):
            title_el = entry.find("{http://www.w3.org/2005/Atom}title") or entry.find("title")
            cat_el = entry.find("{http://www.w3.org/2005/Atom}category") or entry.find("category")
            link_el = entry.find("{http://www.w3.org/2005/Atom}link") or entry.find("link")

            title = title_el.text.strip() if title_el is not None and title_el.text else "N/A"
            sub = cat_el.attrib.get("label", cat_el.attrib.get("term", "r/popular")) if cat_el is not None else "r/popular"
            link = link_el.attrib.get("href", "") if link_el is not None else ""

            result[f"post_{i}_title"] = title
            result[f"post_{i}_subreddit"] = sub
            result[f"post_{i}_score"] = ""
            result[f"post_{i}_url"] = link
        result["total_posts"] = str(len(entries[:count]))
        return result
    except Exception as exc:
        log.error("Could not parse Reddit data: %s", exc)

    return {"error": "Failed to parse Reddit posts"}


def extract_gold_silver(response: requests.Response, fields: dict) -> dict:
    """
    Extract gold (specifically 10 grams prices) and silver prices for Hyderabad from GoodReturns.in.
    """
    soup = BeautifulSoup(response.text, "html.parser")
    result = {}

    # 1. Parse Gold Table from GoodReturns Hyderabad page
    # GoodReturns Table 0 has headers: ['Gram', '24K', '22K', '18K']
    # And rows: '1', '8', '10', '100'
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue
        header = [c.get_text(strip=True).lower() for c in rows[0].find_all(["td", "th"])]

        if any("24k" in h for h in header) and any("22k" in h for h in header):
            idx_24k = next((i for i, h in enumerate(header) if "24k" in h), 1)
            idx_22k = next((i for i, h in enumerate(header) if "22k" in h), 2)
            idx_18k = next((i for i, h in enumerate(header) if "18k" in h), 3)

            for row in rows[1:]:
                cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                if cells and cells[0] == "10":  # 10 Grams row!
                    if len(cells) > idx_24k:
                        result["gold_24k_10g"] = cells[idx_24k]
                    if len(cells) > idx_22k:
                        result["gold_22k_10g"] = cells[idx_22k]
                    if len(cells) > idx_18k:
                        result["gold_18k_10g"] = cells[idx_18k]
                    break

        if "gold_24k_10g" in result:
            break

    # Fallback regex for 10g gold if table structure changes
    if not result.get("gold_22k_10g") and not result.get("gold_24k_10g"):
        text = soup.get_text()
        gold_24_match = re.search(r'24\s*(?:Carat|Karat|[CK]t?).*?(?:₹|Rs\.?)\s*([\d,]+)', text, re.IGNORECASE)
        gold_22_match = re.search(r'22\s*(?:Carat|Karat|[CK]t?).*?(?:₹|Rs\.?)\s*([\d,]+)', text, re.IGNORECASE)
        if gold_24_match:
            result["gold_24k_10g"] = f"₹{gold_24_match.group(1)}"
        if gold_22_match:
            result["gold_22k_10g"] = f"₹{gold_22_match.group(1)}"

    # 2. Fetch Hyderabad Silver Rate
    try:
        silver_url = fields.get("silver_url", "https://www.goodreturns.in/silver-rates/hyderabad.html")
        s_resp = requests.get(
            silver_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            timeout=20,
        )
        if s_resp.status_code == 200:
            s_soup = BeautifulSoup(s_resp.text, "html.parser")
            for table in s_soup.find_all("table"):
                for row in table.find_all("tr"):
                    cells = [c.get_text(strip=True) for c in row.find_all(["td", "th"])]
                    if len(cells) >= 2 and cells[0] == "10":
                        result["silver_10g"] = cells[1]
                    elif len(cells) >= 2 and ("kg" in cells[0].lower() or cells[0] == "1000"):
                        result["silver_1kg"] = cells[1]
    except Exception as exc:
        log.warning("Could not fetch silver rate: %s", exc)

    result.setdefault("gold_24k_10g", "N/A")
    result.setdefault("gold_22k_10g", "N/A")
    result.setdefault("gold_18k_10g", "N/A")
    result.setdefault("silver_10g", "N/A")
    result.setdefault("silver_1kg", "N/A")

    return result


def extract_gold_silver_api(response: requests.Response, fields: dict) -> dict:
    """Extract gold and silver prices from a generic JSON API."""
    try:
        data = response.json()
    except Exception:
        log.error("Failed to parse JSON for gold/silver API")
        return {"gold_price": "N/A", "silver_price": "N/A"}

    result = {}
    if isinstance(data, list):
        for item in data:
            name = str(item.get("name", item.get("metal", ""))).lower()
            price = item.get("price", item.get("rate", "N/A"))
            if "gold" in name:
                purity = item.get("purity", "")
                key = f"gold_{purity}" if purity else "gold_price"
                result[key] = str(price)
            elif "silver" in name:
                result["silver_price"] = str(price)
    elif isinstance(data, dict):
        for key, val in data.items():
            key_lower = key.lower()
            if "gold" in key_lower or key_lower in ("xau",):
                result["gold_price"] = str(val) if not isinstance(val, dict) else str(val.get("price", val))
            if "silver" in key_lower or key_lower in ("xag",):
                result["silver_price"] = str(val) if not isinstance(val, dict) else str(val.get("price", val))

    result.setdefault("gold_price", "N/A")
    result.setdefault("silver_price", "N/A")
    return result


def extract_markets(response: requests.Response, fields: dict) -> dict:
    """
    Extract Indian market indices (NIFTY 50, SENSEX) and USD/INR exchange rate.
    """
    result = {}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # 1. USD / INR
    try:
        r_usd = requests.get("https://open.er-api.com/v6/latest/USD", headers=headers, timeout=15)
        if r_usd.status_code == 200:
            inr = r_usd.json().get("rates", {}).get("INR")
            if inr:
                result["usd_inr"] = f"₹{inr:.2f}"
    except Exception as exc:
        log.warning("Could not fetch USD/INR: %s", exc)

    # 2. Yahoo Finance for Nifty & Sensex
    tickers = [
        ("%5ENSEI", "nifty_50", "NIFTY 50"),
        ("%5EBSESN", "sensex", "SENSEX"),
    ]
    for symbol, key, label in tickers:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=1d"
            r_yf = requests.get(url, headers=headers, timeout=15)
            if r_yf.status_code == 200:
                meta = r_yf.json()["chart"]["result"][0]["meta"]
                price = meta.get("regularMarketPrice")
                prev = meta.get("previousClose") or meta.get("chartPreviousClose")
                if price is not None:
                    pct = ((price - prev) / prev) * 100 if prev else 0
                    sign = "+" if pct >= 0 else ""
                    result[f"{key}_price"] = f"{price:,.2f}"
                    result[f"{key}_change"] = f"{sign}{pct:.2f}%"
        except Exception as exc:
            log.warning("Could not fetch %s: %s", label, exc)

    result.setdefault("usd_inr", "N/A")
    result.setdefault("nifty_50_price", "N/A")
    result.setdefault("nifty_50_change", "")
    result.setdefault("sensex_price", "N/A")
    result.setdefault("sensex_change", "")
    return result


def extract_hackernews(response: requests.Response, fields: dict) -> dict:
    """Extract top tech & AI stories from Hacker News via Algolia API."""
    count = int(fields.get("count", 3))
    result = {}
    try:
        data = response.json()
        hits = data.get("hits", [])
        for i, hit in enumerate(hits[:count], 1):
            result[f"item_{i}_title"] = hit.get("title") or hit.get("story_title", "N/A")
            result[f"item_{i}_points"] = str(hit.get("points", 0))
            result[f"item_{i}_comments"] = str(hit.get("num_comments", 0))
            result[f"item_{i}_url"] = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
        result["total_items"] = str(len(hits[:count]))
    except Exception as exc:
        log.error("Could not parse Hacker News data: %s", exc)
    return result


def extract_huggingface(response: requests.Response, fields: dict) -> dict:
    """Extract trending AI models from Hugging Face API."""
    count = int(fields.get("count", 3))
    result = {}
    try:
        models = response.json()
        for i, m in enumerate(models[:count], 1):
            model_id = m.get("id", "N/A")
            likes = m.get("likes", 0)
            pipeline = m.get("pipeline_tag") or "AI Model"
            result[f"item_{i}_id"] = model_id
            result[f"item_{i}_likes"] = f"{likes:,}" if isinstance(likes, int) else str(likes)
            result[f"item_{i}_pipeline"] = pipeline.replace("-", " ").title()
            result[f"item_{i}_url"] = f"https://huggingface.co/{model_id}"
        result["total_items"] = str(len(models[:count]))
    except Exception as exc:
        log.error("Failed to parse Hugging Face data: %s", exc)
    return result


def extract_github_trending(response: requests.Response, fields: dict) -> dict:
    """
    Extract trending repositories.
    Supports both https://github.com/trending (HTML) and GitHub Search API (JSON).
    """
    count = int(fields.get("count", 3))
    result = {}

    # 1. Try parsing HTML (from https://github.com/trending)
    content_type = response.headers.get("Content-Type", "")
    if "text/html" in content_type or response.text.strip().startswith("<!DOCTYPE") or "<html" in response.text[:200]:
        try:
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.find_all("article", class_="Box-row")
            for i, a in enumerate(articles[:count], 1):
                h2 = a.find("h2")
                name = "".join(h2.get_text().split()) if h2 else "N/A"
                p = a.find("p")
                desc = p.get_text(strip=True) if p else "No description"
                if len(desc) > 85:
                    desc = desc[:82] + "..."
                clean_desc = desc.replace("*", "").replace("[", "(").replace("]", ")")
                star_link = a.find("a", href=lambda x: x and x.endswith("/stargazers"))
                stars = star_link.get_text(strip=True) if star_link else "N/A"
                result[f"item_{i}_name"] = name
                result[f"item_{i}_stars"] = stars
                result[f"item_{i}_desc"] = clean_desc
                result[f"item_{i}_url"] = f"https://github.com/{name}"
            result["total_items"] = str(len(articles[:count]))
            if result.get("total_items") != "0":
                return result
        except Exception as exc:
            log.warning("Could not parse HTML trending page: %s", exc)

    # 2. Try parsing JSON (from GitHub Search API)
    try:
        items = response.json().get("items", [])
        for i, repo in enumerate(items[:count], 1):
            full_name = repo.get("full_name", "N/A")
            stars = repo.get("stargazers_count", 0)
            desc = repo.get("description") or "No description"
            if len(desc) > 85:
                desc = desc[:82] + "..."
            clean_desc = desc.replace("*", "").replace("[", "(").replace("]", ")")
            result[f"item_{i}_name"] = full_name
            result[f"item_{i}_stars"] = f"{stars:,}" if isinstance(stars, int) else str(stars)
            result[f"item_{i}_desc"] = clean_desc
            result[f"item_{i}_url"] = repo.get("html_url") or f"https://github.com/{full_name}"
        result["total_items"] = str(len(items[:count]))
        return result
    except Exception as exc:
        log.error("Failed to parse GitHub trending data: %s", exc)

    return result


def extract_crypto(response: requests.Response, fields: dict) -> dict:
    """Extract cryptocurrency prices and 24h change from CoinGecko."""
    result = {}
    try:
        data = response.json()
        coins = [
            ("bitcoin", "BTC", "Bitcoin"),
            ("ethereum", "ETH", "Ethereum"),
            ("solana", "SOL", "Solana"),
        ]
        for coin_id, symbol, label in coins:
            coin_data = data.get(coin_id, {})
            inr = coin_data.get("inr")
            usd = coin_data.get("usd")
            chg = coin_data.get("usd_24h_change", 0.0)
            sign = "+" if chg >= 0 else ""
            ind = "🟢" if chg >= 0 else "🔴"

            result[f"{coin_id}_label"] = f"{label} ({symbol})"
            result[f"{coin_id}_price"] = f"₹{inr:,.0f} (${usd:,.2f})" if inr and usd else "N/A"
            result[f"{coin_id}_chg"] = f"{ind} {sign}{chg:.2f}%"
            result[f"{coin_id}_url"] = f"https://www.coingecko.com/en/coins/{coin_id}"
    except Exception as exc:
        log.error("Failed to parse Crypto data: %s", exc)
    return result


def extract_nasa_apod(response: requests.Response, fields: dict) -> dict:
    """Extract NASA Astronomy Picture of the Day from APOD RSS feed."""
    result = {}
    try:
        root = ET.fromstring(response.content)
        item = root.find(".//item")
        if item is not None:
            title_el = item.find("title")
            link_el = item.find("link")
            desc_el = item.find("description")
            title = title_el.text.strip() if title_el is not None and title_el.text else "Astronomy Picture"
            link = link_el.text.strip() if link_el is not None and link_el.text else ""
            desc = desc_el.text.strip() if desc_el is not None and desc_el.text else ""
            if len(desc) > 160:
                desc = desc[:157] + "..."
            clean_desc = desc.replace("*", "").replace("[", "(").replace("]", ")")
            result["title"] = title.replace("*", "").replace("[", "(").replace("]", ")")
            result["link"] = link
            result["desc"] = clean_desc
    except Exception as exc:
        log.error("Failed to parse NASA APOD RSS: %s", exc)
    return result


EXTRACTORS = {
    "json": extract_json,
    "css": extract_css,
    "regex": extract_regex,
    "rss": extract_rss,
    "reddit": extract_reddit,
    "gold_silver": extract_gold_silver,
    "gold_silver_api": extract_gold_silver_api,
    "markets": extract_markets,
    "hackernews": extract_hackernews,
    "huggingface": extract_huggingface,
    "github_trending": extract_github_trending,
    "crypto": extract_crypto,
    "nasa_apod": extract_nasa_apod,
}


# ─── Notification helpers ──────────────────────────────────────────────────

def send_telegram(message: str) -> bool:
    """Send a message via Telegram Bot API to ALL subscribed chat IDs."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_IDS:
        log.warning("Telegram credentials not configured – skipping.")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    all_ok = True

    for chat_id in TELEGRAM_CHAT_IDS:
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        try:
            resp = requests.post(url, json=payload, timeout=30)
            resp.raise_for_status()
            log.info("Telegram message sent to %s ✓", chat_id)
        except requests.RequestException as exc:
            log.warning("Telegram Markdown send failed for %s: %s. Retrying as plain text...", chat_id, exc)
            try:
                plain_payload = dict(payload)
                plain_payload.pop("parse_mode", None)
                resp = requests.post(url, json=plain_payload, timeout=30)
                resp.raise_for_status()
                log.info("Telegram message sent to %s (plain-text fallback) ✓", chat_id)
            except requests.RequestException as retry_exc:
                log.error("Telegram send failed completely for %s: %s", chat_id, retry_exc)
                all_ok = False

    return all_ok


NOTIFIERS = {
    "telegram": send_telegram,
}


# ─── Message formatters for special extractors ─────────────────────────────

def format_rss_message(name: str, extracted: dict, template: str) -> str:
    """Format RSS items into a readable message with link icons and spaced items."""
    if template and "{" in template:
        try:
            return template.format(**extracted)
        except KeyError:
            pass

    items = []
    i = 1
    while f"item_{i}_title" in extracted:
        title = extracted[f"item_{i}_title"]
        source = extracted.get(f"item_{i}_source", "").strip()
        link = extracted.get(f"item_{i}_link", "").strip()
        clean_title = title.replace("*", "").replace("[", "(").replace("]", ")").strip()

        # Remove duplicate source suffix from title (e.g. "... - The Hindu")
        if source:
            for sep in [" - ", " | ", " — "]:
                suffix = f"{sep}{source}"
                if clean_title.lower().endswith(suffix.lower()):
                    clean_title = clean_title[:-len(suffix)].strip()
                    break
        if " - " in clean_title:
            parts = clean_title.rsplit(" - ", 1)
            if len(parts) == 2 and (not source or source.lower() in parts[1].lower() or parts[1].lower() in source.lower()):
                clean_title = parts[0].strip()
                if not source:
                    source = parts[1].strip()

        source_str = f" _({source})_" if source else ""
        link_icon = f" [🔗]({link})" if link else ""
        items.append(f"{i}. {clean_title}{source_str}{link_icon}")
        i += 1
    return f"📰 *{name}*\n\n" + "\n\n".join(items)


def format_reddit_message(name: str, extracted: dict, template: str) -> str:
    """Format Reddit posts into a readable message with link icons and spaced items."""
    if template and "{" in template:
        try:
            return template.format(**extracted)
        except KeyError:
            pass

    items = []
    i = 1
    while f"post_{i}_title" in extracted:
        title = extracted[f"post_{i}_title"]
        sub = extracted.get(f"post_{i}_subreddit", "")
        score = extracted.get(f"post_{i}_score", "")
        url = extracted.get(f"post_{i}_url", "")
        clean_title = title.replace("*", "").replace("[", "(").replace("]", ")")
        sub_str = f"↳ {sub}" if sub and sub != "N/A" else ""
        score_str = f" • ⬆️ {score}" if score and score != "0" else ""
        link_icon = f" [🔗]({url})" if url else ""
        extra = f"\n   {sub_str}{score_str}" if (sub_str or score_str) else ""
        items.append(f"{i}. *{clean_title}*{link_icon}{extra}")
        i += 1
    return f"🔥 *{name}*\n\n" + "\n\n".join(items)


def format_gold_silver_message(name: str, extracted: dict, template: str) -> str:
    """Format gold (per 10g) & silver prices into a clean readable Telegram message."""
    if template and "{" in template:
        try:
            return template.format(**extracted)
        except KeyError:
            pass

    gold_lines = []
    if extracted.get("gold_24k_10g") and extracted["gold_24k_10g"] != "N/A":
        gold_lines.append(f"🥇 *Gold 24K (10g):* {extracted['gold_24k_10g']}")
    elif extracted.get("gold_24k") and extracted["gold_24k"] != "N/A":
        gold_lines.append(f"🥇 *Gold 24K (10g):* {extracted['gold_24k']}")

    if extracted.get("gold_22k_10g") and extracted["gold_22k_10g"] != "N/A":
        gold_lines.append(f"🥇 *Gold 22K (10g):* {extracted['gold_22k_10g']}")
    elif extracted.get("gold_22k") and extracted["gold_22k"] != "N/A":
        gold_lines.append(f"🥇 *Gold 22K (10g):* {extracted['gold_22k']}")

    if extracted.get("gold_18k_10g") and extracted["gold_18k_10g"] != "N/A":
        gold_lines.append(f"🥇 *Gold 18K (10g):* {extracted['gold_18k_10g']}")

    silver_lines = []
    if extracted.get("silver_10g") and extracted["silver_10g"] != "N/A":
        silver_lines.append(f"🥈 *Silver (10g):* {extracted['silver_10g']}")
    if extracted.get("silver_1kg") and extracted["silver_1kg"] != "N/A":
        silver_lines.append(f"🥈 *Silver (1 Kg):* {extracted['silver_1kg']}")
    elif extracted.get("silver") and extracted["silver"] != "N/A":
        silver_lines.append(f"🥈 *Silver:* {extracted['silver']}")

    sections = []
    if gold_lines:
        sections.append("\n".join(gold_lines))
    if silver_lines:
        sections.append("\n".join(silver_lines))

    return f"🪙 *{name}*\n\n" + "\n\n".join(sections)


def format_markets_message(name: str, extracted: dict, template: str) -> str:
    """Format market snapshot into a readable message with clean line breaks."""
    if template and "{" in template:
        try:
            return template.format(**extracted)
        except KeyError:
            pass

    items = []
    if extracted.get("nifty_50_price") and extracted["nifty_50_price"] != "N/A":
        chg = f" ({extracted.get('nifty_50_change')})" if extracted.get("nifty_50_change") else ""
        items.append(f"• *NIFTY 50:* {extracted['nifty_50_price']}{chg}")
    if extracted.get("sensex_price") and extracted["sensex_price"] != "N/A":
        chg = f" ({extracted.get('sensex_change')})" if extracted.get("sensex_change") else ""
        items.append(f"• *SENSEX:* {extracted['sensex_price']}{chg}")
    if extracted.get("usd_inr") and extracted["usd_inr"] != "N/A":
        items.append(f"• *USD / INR:* {extracted['usd_inr']}")

    return f"📊 *{name}*\n\n" + "\n\n".join(items)


def format_hackernews_message(name: str, extracted: dict, template: str) -> str:
    """Format Hacker News stories into a readable message with blank lines between items."""
    if template and "{" in template:
        try:
            return template.format(**extracted)
        except KeyError:
            pass

    items = []
    i = 1
    while f"item_{i}_title" in extracted:
        title = extracted[f"item_{i}_title"]
        points = extracted.get(f"item_{i}_points", "0")
        comments = extracted.get(f"item_{i}_comments", "0")
        url = extracted.get(f"item_{i}_url", "")

        clean_title = title.replace("*", "").replace("[", "(").replace("]", ")")
        link_icon = f" [🔗]({url})" if url else ""
        items.append(f"{i}. *{clean_title}*{link_icon}\n   ↳ {points} pts • {comments} comments")
        i += 1
    return f"⚡ *{name}*\n\n" + "\n\n".join(items)


def format_huggingface_message(name: str, extracted: dict, template: str) -> str:
    """Format trending Hugging Face AI models with blank lines between items."""
    items = []
    i = 1
    while f"item_{i}_id" in extracted:
        model_id = extracted[f"item_{i}_id"]
        likes = extracted.get(f"item_{i}_likes", "0")
        pipeline = extracted.get(f"item_{i}_pipeline", "")
        url = extracted.get(f"item_{i}_url", "")
        link_icon = f" [🔗]({url})" if url else ""
        items.append(f"{i}. *{model_id}*{link_icon}\n   ↳ ❤️ {likes} likes • {pipeline}")
        i += 1
    return f"🤖 *{name}*\n\n" + "\n\n".join(items)


def format_github_trending_message(name: str, extracted: dict, template: str) -> str:
    """Format trending GitHub repositories with blank lines between items."""
    items = []
    i = 1
    while f"item_{i}_name" in extracted:
        name_str = extracted[f"item_{i}_name"]
        stars = extracted.get(f"item_{i}_stars", "0")
        desc = extracted.get(f"item_{i}_desc", "")
        url = extracted.get(f"item_{i}_url", "")
        link_icon = f" [🔗]({url})" if url else ""
        items.append(f"{i}. *{name_str}*{link_icon}\n   ↳ 🌟 {stars} stars • {desc}")
        i += 1
    return f"⭐ *{name}*\n\n" + "\n\n".join(items)


def format_crypto_message(name: str, extracted: dict, template: str) -> str:
    """Format crypto prices into a readable message with clean line breaks."""
    coin_icons = {
        "bitcoin": "🟠",
        "ethereum": "🔹",
        "solana": "🟣",
    }
    items = []
    for coin_id in ["bitcoin", "ethereum", "solana"]:
        if f"{coin_id}_price" in extracted and extracted[f"{coin_id}_price"] != "N/A":
            label = extracted[f"{coin_id}_label"]
            price = extracted[f"{coin_id}_price"]
            chg = extracted.get(f"{coin_id}_chg", "")
            url = extracted.get(f"{coin_id}_url", "")
            icon = coin_icons.get(coin_id, "•")
            link_icon = f" [🔗]({url})" if url else ""
            items.append(f"• {icon} *{label}:* {price} • {chg}{link_icon}")
    return f"₿ *{name}*\n\n" + "\n\n".join(items)


def format_nasa_apod_message(name: str, extracted: dict, template: str) -> str:
    """Format NASA Astronomy Picture of the Day into a readable message."""
    lines = [f"🌌 *{name}*\n"]
    title = extracted.get("title", "Today's Cosmic Wonder")
    link = extracted.get("link", "")
    desc = extracted.get("desc", "")
    link_icon = f" [🔗]({link})" if link else ""
    lines.append(f"🔭 *{title}*{link_icon}")
    if desc:
        lines.append(f"_{desc}_")
    return "\n".join(lines)


SPECIAL_FORMATTERS = {
    "rss": format_rss_message,
    "reddit": format_reddit_message,
    "gold_silver": format_gold_silver_message,
    "gold_silver_api": format_gold_silver_message,
    "markets": format_markets_message,
    "hackernews": format_hackernews_message,
    "huggingface": format_huggingface_message,
    "github_trending": format_github_trending_message,
    "crypto": format_crypto_message,
    "nasa_apod": format_nasa_apod_message,
}


# ─── Main runner ────────────────────────────────────────────────────────────

def run_job(job: dict) -> None:
    """Execute a single monitoring job."""
    name = job["name"]
    log.info("── Running job: %s ──", name)

    # 1. Fetch the URL
    method = job.get("method", "GET").upper()
    headers = job.get("headers", {})
    if "User-Agent" not in headers:
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    # Auto-inject GitHub token if available and querying GitHub API
    if "api.github.com" in job["url"] and GITHUB_TOKEN and "Authorization" not in headers:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    try:
        resp = requests.request(method, job["url"], headers=headers, timeout=60)
        resp.raise_for_status()
    except requests.RequestException as exc:
        # If GitHub API fails (e.g. rate limit exceeded), fall back to public trending page
        if job.get("extract", {}).get("type") == "github_trending":
            log.warning("GitHub API throttled (%s). Falling back to https://github.com/trending ...", exc)
            try:
                resp = requests.get(
                    "https://github.com/trending",
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    timeout=20,
                )
                resp.raise_for_status()
            except Exception as fb_exc:
                error_msg = f"❌ *Job Failed: {name}*\n\nCould not fetch URL:\n`{fb_exc}`"
                for channel in job.get("notify", []):
                    NOTIFIERS.get(channel, lambda _: None)(error_msg)
                log.error("Fetch fallback failed for %s: %s", name, fb_exc)
                return
        else:
            error_msg = f"❌ *Job Failed: {name}*\n\nCould not fetch URL:\n`{exc}`"
            for channel in job.get("notify", []):
                NOTIFIERS.get(channel, lambda _: None)(error_msg)
            log.error("Fetch failed for %s: %s", name, exc)
            return

    # 2. Extract data
    extract_cfg = job["extract"]
    extract_type = extract_cfg["type"]
    extractor = EXTRACTORS.get(extract_type)
    if not extractor:
        log.error("Unknown extraction type: %s", extract_type)
        return

    extracted = extractor(resp, extract_cfg.get("fields", {}))
    # Log extracted values safely (avoiding encoding errors on Windows console)
    log.info("Extracted successfully: %s keys found", len(extracted))

    # 3. Format message
    template = job.get("message_template", "")
    formatter = SPECIAL_FORMATTERS.get(extract_type)

    if formatter:
        message = formatter(name, extracted, template)
    elif template:
        try:
            message = template.format(**extracted)
        except KeyError as exc:
            log.error("Template key missing: %s", exc)
            message = f"*{name}*\n\n{json.dumps(extracted, indent=2)}"
    else:
        message = f"*{name}*\n\n{json.dumps(extracted, indent=2)}"

    # Print the exact content being pushed
    channels_str = ", ".join(job.get("notify", []))
    print("\n" + "=" * 60)
    print(f"📢 [PUSHING TO {channels_str.upper() or 'NONE'}] Job: {name}")
    print("-" * 60)
    try:
        print(message)
    except UnicodeEncodeError:
        print(message.encode("ascii", "replace").decode())
    print("=" * 60 + "\n")

    # 4. Send notifications
    for channel in job.get("notify", []):
        notifier = NOTIFIERS.get(channel)
        if notifier:
            notifier(message)
        else:
            log.warning("Unknown notification channel: %s", channel)


def main() -> None:
    """Load config and run all jobs."""
    config_file = Path(CONFIG_PATH)
    if not config_file.exists():
        log.error("Config file not found: %s", config_file)
        sys.exit(1)

    config = json.loads(config_file.read_text(encoding="utf-8"))
    jobs = config.get("jobs", [])

    if not jobs:
        log.warning("No jobs configured in %s", config_file)
        return

    log.info("Loaded %d job(s) from %s", len(jobs), config_file)

    errors = 0
    for job in jobs:
        try:
            run_job(job)
        except Exception as exc:
            log.exception("Unhandled error in job '%s': %s", job.get("name", "?"), exc)
            errors += 1

    if errors:
        log.error("%d job(s) had errors", errors)
        sys.exit(1)

    log.info("All jobs completed ✓")

    # Send closing divider to all notified channels
    divider_message = (
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🏁 *OmniPulse • 6-Hour Update Complete*\n"
        "⏰ _Next briefing in 6 hours_\n"
        "━━━━━━━━━━━━━━━━━━━━━━━"
    )

    print("\n" + "=" * 60)
    print("🏁 [ALL PUSHES COMPLETED] OmniPulse 6-Hour Cycle Finished")
    print("=" * 60 + "\n")

    # Send closing divider to each unique configured channel
    all_channels = {ch for job in jobs for ch in job.get("notify", [])}
    for channel in all_channels:
        notifier = NOTIFIERS.get(channel)
        if notifier:
            notifier(divider_message)


if __name__ == "__main__":
    main()

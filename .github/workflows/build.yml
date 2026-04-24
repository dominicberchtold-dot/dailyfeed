#!/usr/bin/env python3
"""
Daily Feed Builder — 100% free, no API keys needed.
Fetches RSS feeds, weather, sports data and builds a static HTML file.
Run via GitHub Actions every morning at 7:00 AM Vienna time.
"""

import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import html
import re
import sys

VIENNA = ZoneInfo("Europe/Vienna")
NOW = datetime.now(VIENNA)

# ── HELPERS ──────────────────────────────────────────────────────────────────

def fetch(url, timeout=10):
    """Fetch URL, return text or None."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; DailyFeedBot/1.0)",
            "Accept": "application/rss+xml, application/xml, text/xml, */*"
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ✗ fetch({url[:60]}): {e}", file=sys.stderr)
        return None

def parse_rss(xml_text, max_items=5):
    """Parse RSS/Atom feed, return list of {title, desc, link, date}."""
    if not xml_text:
        return []
    try:
        # Strip namespace prefixes for easier parsing
        xml_text = re.sub(r'<(/?)([a-zA-Z0-9_]+):([a-zA-Z0-9_]+)', r'<\1\3', xml_text)
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        print(f"  ✗ XML parse error: {e}", file=sys.stderr)
        return []

    items = []
    # RSS 2.0
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        desc  = (item.findtext("description") or item.findtext("summary") or "").strip()
        link  = (item.findtext("link") or "").strip()
        date  = (item.findtext("pubDate") or item.findtext("published") or "").strip()
        if title:
            # Strip HTML from description
            desc = re.sub(r"<[^>]+>", " ", desc)
            desc = re.sub(r"\s+", " ", html.unescape(desc)).strip()
            desc = desc[:200] + "…" if len(desc) > 200 else desc
            title = html.unescape(re.sub(r"<[^>]+>", "", title)).strip()
            items.append({"title": title, "desc": desc, "link": link, "date": date})
        if len(items) >= max_items:
            break
    # Atom fallback
    if not items:
        for entry in root.iter("entry"):
            title = (entry.findtext("title") or "").strip()
            desc  = (entry.findtext("summary") or entry.findtext("content") or "").strip()
            link_el = entry.find("link")
            link = link_el.get("href", "") if link_el is not None else ""
            date = (entry.findtext("updated") or entry.findtext("published") or "").strip()
            if title:
                desc = re.sub(r"<[^>]+>", " ", desc)
                desc = re.sub(r"\s+", " ", html.unescape(desc)).strip()
                desc = desc[:200] + "…" if len(desc) > 200 else desc
                title = html.unescape(re.sub(r"<[^>]+>", "", title)).strip()
                items.append({"title": title, "desc": desc, "link": link, "date": date})
            if len(items) >= max_items:
                break
    return items

def fmt_date(date_str):
    """Return 'vor Xh' or date string."""
    if not date_str:
        return ""
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        diff = NOW - dt.astimezone(VIENNA)
        h = diff.total_seconds() / 3600
        if h < 1: return f"vor {int(diff.total_seconds()/60)} min"
        if h < 24: return f"vor {int(h)}h"
        if h < 48: return "gestern"
        return dt.strftime("%d. %b")
    except:
        return ""

# ── DATA FETCHERS ─────────────────────────────────────────────────────────────

def get_weather():
    print("→ Weather (Open-Meteo)…")
    url = (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=48.2082&longitude=16.3738"
        "&current=temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m"
        "&hourly=precipitation_probability,temperature_2m"
        "&daily=weather_code,temperature_2m_max,temperature_2m_min,"
        "precipitation_probability_max,precipitation_sum,sunrise,sunset"
        "&timezone=Europe%2FVienna&forecast_days=5"
    )
    raw = fetch(url)
    if not raw:
        return None
    d = json.loads(raw)
    cur = d["current"]
    daily = d["daily"]
    hourly = d["hourly"]

    rain_max = daily["precipitation_probability_max"][0] or 0
    precip_sum = daily["precipitation_sum"][0] or 0

    if rain_max >= 60 or precip_sum > 3:
        gear = "☂ Schirm + Regenjacke mitnehmen — wird nass."
        gear_type = "wet"
    elif rain_max >= 30:
        gear = "🌂 Kleiner Schirm empfohlen — Schauer möglich."
        gear_type = "damp"
    else:
        gear = "☀ Kein Regen erwartet — Jacke + Schirm daheim lassen."
        gear_type = "dry"

    code_icons = {0:"☀️",1:"🌤",2:"⛅",3:"☁️",45:"🌫",48:"🌫",
                  51:"🌦",53:"🌦",55:"🌧",61:"🌧",63:"🌧",65:"🌧",
                  71:"❄️",73:"❄️",75:"❄️",80:"🌦",81:"🌦",82:"⛈",
                  95:"⛈",96:"⛈",99:"⛈"}
    code_names = {0:"Klar",1:"Überwiegend klar",2:"Teils bewölkt",3:"Bedeckt",
                  45:"Neblig",51:"Nieselregen",61:"Regen",63:"Regen",
                  65:"Starker Regen",71:"Schneefall",80:"Schauer",82:"Heftige Schauer",95:"Gewitter"}

    # Next 8 hours
    now_str = NOW.strftime("%Y-%m-%dT%H")
    hi = next((i for i, t in enumerate(hourly["time"]) if t.startswith(now_str)), 0)
    hours = []
    for i in range(8):
        idx = hi + i
        if idx >= len(hourly["time"]): break
        h_val = int(hourly["time"][idx][11:13])
        hours.append({"h": h_val, "p": hourly["precipitation_probability"][idx] or 0})

    day_names = ["So","Mo","Di","Mi","Do","Fr","Sa"]
    forecast = []
    for i in range(1, 5):
        dt = datetime.strptime(daily["time"][i], "%Y-%m-%d")
        forecast.append({
            "day": day_names[dt.weekday() if dt.weekday() < 6 else 6],  # Mo-So
            "icon": code_icons.get(daily["weather_code"][i], "🌡"),
            "high": round(daily["temperature_2m_max"][i]),
            "low": round(daily["temperature_2m_min"][i]),
            "rain": daily["precipitation_probability_max"][i] or 0,
        })
    # Fix weekday names (Python: Mon=0, Sun=6)
    py_days = ["Mo","Di","Mi","Do","Fr","Sa","So"]
    for i in range(1, 5):
        dt = datetime.strptime(daily["time"][i], "%Y-%m-%d")
        forecast[i-1]["day"] = py_days[dt.weekday()]

    return {
        "temp": round(cur["temperature_2m"]),
        "icon": code_icons.get(cur["weather_code"], "🌡"),
        "condition": code_names.get(cur["weather_code"], "Wechselhaft"),
        "high": round(daily["temperature_2m_max"][0]),
        "low": round(daily["temperature_2m_min"][0]),
        "wind": round(cur["wind_speed_10m"]),
        "humidity": cur["relative_humidity_2m"],
        "gear": gear,
        "gear_type": gear_type,
        "hours": hours,
        "forecast": forecast,
    }

def get_top_news():
    print("→ Top News (BBC World)…")
    feeds = [
        ("https://feeds.bbci.co.uk/news/world/rss.xml", "BBC World"),
        ("https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "NYT World"),
        ("https://www.theguardian.com/world/rss", "The Guardian"),
    ]
    for url, source in feeds:
        items = parse_rss(fetch(url), 5)
        if items:
            for item in items:
                item["source"] = source
            print(f"  ✓ {source}: {len(items)} items")
            return items
    return []

def get_good_news():
    print("→ Good News (Positive.news)…")
    feeds = [
        "https://www.positive.news/feed/",
        "https://www.goodnewsnetwork.org/feed/",
    ]
    for url in feeds:
        items = parse_rss(fetch(url), 3)
        if items:
            print(f"  ✓ {url[:40]}: {len(items)} items")
            return items
    return []

def get_arsenal():
    print("→ Arsenal (football-data.org)…")
    # Arsenal team ID = 57 on football-data.org (free tier, no key for basic)
    # Free tier allows 10 req/min without key, but requires key for some endpoints
    # Fallback: use RSS
    rss_url = "https://feeds.bbci.co.uk/sport/football/teams/arsenal/rss.xml"
    items = parse_rss(fetch(rss_url), 6)
    if items:
        print(f"  ✓ Arsenal RSS: {len(items)} items")
        return items
    return []

def get_arsenal_news():
    print("→ Arsenal News (arseblog)…")
    feeds = [
        ("https://arseblog.com/feed/", "arseblog"),
        ("https://feeds.bbci.co.uk/sport/football/teams/arsenal/rss.xml", "BBC Sport"),
    ]
    all_items = []
    for url, source in feeds:
        items = parse_rss(fetch(url), 3)
        for item in items:
            item["source"] = source
        all_items.extend(items)
        if len(all_items) >= 4:
            break
    print(f"  ✓ Arsenal news: {len(all_items[:4])} items")
    return all_items[:4]

def get_sinner():
    print("→ Sinner (Google News RSS)…")
    url = "https://news.google.com/rss/search?q=Jannik+Sinner+tennis&hl=en-US&gl=US&ceid=US:en"
    items = parse_rss(fetch(url), 4)
    if items:
        print(f"  ✓ Sinner: {len(items)} items")
        for item in items:
            item["source"] = "Google News"
        return items
    return []

def get_tennis():
    print("→ Tennis (ATP / Google News)…")
    url = "https://news.google.com/rss/search?q=ATP+tennis+Masters+2026&hl=en-US&gl=US&ceid=US:en"
    items = parse_rss(fetch(url), 3)
    if items:
        print(f"  ✓ Tennis: {len(items)} items")
        for item in items:
            item["source"] = "Google News"
        return items
    return []

def get_fact():
    print("→ Fact of the day…")
    raw = fetch("https://uselessfacts.jsph.pl/api/v2/facts/random?language=en")
    if raw:
        try:
            data = json.loads(raw)
            return data.get("text", "")
        except:
            pass
    # Date-based fallback
    raw = fetch(f"https://numbersapi.com/{NOW.month}/{NOW.day}/date?json")
    if raw:
        try:
            return json.loads(raw).get("text", "")
        except:
            pass
    facts = [
        "Octopuses have three hearts and blue blood — and when they swim, their main heart stops beating. That's why they prefer crawling.",
        "Honey never expires. Archaeologists found 3,000-year-old honey in Egyptian tombs — still perfectly edible.",
        "The Eiffel Tower grows about 15 cm taller in summer because heat expands the iron.",
        "Bananas are botanically berries. Strawberries are not.",
        "There are more possible chess games than atoms in the observable universe.",
        "A group of flamingos is called a 'flamboyance.' Naturally.",
    ]
    import random
    return random.choice(facts)

# ── HTML BUILDER ──────────────────────────────────────────────────────────────

def e(s):
    """HTML-escape a string."""
    return html.escape(str(s)) if s else ""

def news_list_html(items, max_items=5):
    if not items:
        return '<div class="empty">Keine Daten verfügbar</div>'
    out = []
    for i, item in enumerate(items[:max_items]):
        num = str(i + 1).zfill(2)
        age = fmt_date(item.get("date", ""))
        link = item.get("link", "#")
        out.append(f'''
      <a class="news-item" href="{e(link)}" target="_blank" rel="noopener">
        <div class="news-num">{num}</div>
        <div>
          <div class="news-title">{e(item["title"])}</div>
          <div class="news-meta">
            <span class="news-source">{e(item.get("source",""))}</span>
            {"<span>" + e(age) + "</span>" if age else ""}
          </div>
          {"<div class='news-desc'>" + e(item.get("desc","")) + "</div>" if item.get("desc") else ""}
        </div>
      </a>''')
    return "".join(out)

def arsenal_matches_html(items):
    """Show first 3 arsenal items as match-style cards."""
    if not items:
        return '<div class="empty">Keine Spieldaten verfügbar</div>'
    out = []
    for item in items[:3]:
        out.append(f'''
      <div class="match-block">
        <div class="match-comp">{e(item.get("source","Arsenal"))}</div>
        <div class="news-title" style="padding:0;font-size:14px">{e(item["title"])}</div>
        {"<div class='match-note'>" + e(item.get("desc","")[:120]) + "</div>" if item.get("desc") else ""}
      </div>''')
    return "".join(out)

def weather_html(w):
    if not w:
        return '<div class="empty">Wetter nicht verfügbar</div>'
    gear_color = {"wet":"#2563eb","damp":"#0891b2","dry":"#2d6a4f"}.get(w["gear_type"], "#2d6a4f")

    # Rain bars
    bars = ""
    for h in w["hours"]:
        col = "#2563eb" if h["p"] >= 60 else "#93c5fd" if h["p"] >= 30 else "#e2e8f0"
        height = max(4, h["p"])
        bars += f'<div class="rain-bar-wrap"><div class="rain-bar" style="height:{height}%;background:{col}"></div><div class="rain-bar-label">{h["h"]}h</div></div>'

    # Forecast
    fc = ""
    for f in w["forecast"]:
        fc += f'<div class="fday"><div class="fday-name">{f["day"]}</div><div class="fday-icon">{f["icon"]}</div><div class="fday-temp">{f["high"]}°</div><div class="fday-rain">{f["rain"]}%</div></div>'

    return f'''
      <div class="weather-row">
        <div>
          <div class="temp-hero">{w["temp"]}°</div>
          <div class="weather-cond">{e(w["condition"])}</div>
          <div class="weather-hilo">↑{w["high"]}° ↓{w["low"]}° · {w["wind"]} km/h · {w["humidity"]}%</div>
        </div>
        <div class="weather-icon">{w["icon"]}</div>
      </div>
      <div class="gear-box" style="border-color:{gear_color}">{e(w["gear"])}</div>
      <div class="rain-label">Regen · nächste 8h</div>
      <div class="rain-bars">{bars}</div>
      <div class="forecast-row">{fc}</div>'''

def build_tldr(top_news, arsenal, sinner, weather, good_news):
    items = []
    if weather:
        items.append(f'<strong>Wien {weather["temp"]}°</strong> {weather["condition"]} — {weather["gear"].replace("☀ ","").replace("🌂 ","").replace("☂ ","")}')
    if top_news:
        items.append(f'<strong>Welt:</strong> {top_news[0]["title"][:80]}')
    if top_news and len(top_news) > 1:
        items.append(f'<strong>+</strong> {top_news[1]["title"][:80]}')
    if arsenal:
        items.append(f'<strong>Arsenal:</strong> {arsenal[0]["title"][:80]}')
    if sinner:
        items.append(f'<strong>Sinner:</strong> {sinner[0]["title"][:80]}')
    if good_news:
        items.append(f'<strong>Good News:</strong> {good_news[0]["title"][:80]}')
    if top_news and len(top_news) > 2:
        items.append(f'<strong>+</strong> {top_news[2]["title"][:80]}')
    if good_news and len(good_news) > 1:
        items.append(f'<strong>+</strong> {good_news[1]["title"][:80]}')
    return items[:8]

def build_html(weather, top_news, good_news, arsenal, arsenal_news, sinner, tennis, fact):
    date_str = NOW.strftime("%-d. %B %Y")
    weekday = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"][NOW.weekday()]
    time_str = NOW.strftime("%H:%M")
    gen = f"{weekday}, {date_str} · {time_str} Uhr"

    tldr = build_tldr(top_news, arsenal, sinner, weather, good_news)
    tldr_left  = "".join(f'<div class="tldr-item">{t}</div>' for t in tldr[:4])
    tldr_right = "".join(f'<div class="tldr-item">{t}</div>' for t in tldr[4:8])

    good_html = ""
    if good_news:
        emojis = ["🌿","⚡","🚀","💚","🌍","🏆"]
        for i, item in enumerate(good_news[:3]):
            link = item.get("link","#")
            good_html += f'''<a class="good-item" href="{e(link)}" target="_blank" rel="noopener">
        <div class="good-title">{emojis[i%len(emojis)]} {e(item["title"])}</div>
        {"<div class='good-desc'>" + e(item.get("desc","")[:160]) + "</div>" if item.get("desc") else ""}
      </a>'''
    else:
        good_html = '<div class="empty">Keine Daten verfügbar</div>'

    sinner_html = ""
    if sinner:
        for item in sinner[:4]:
            sinner_html += f'''<a class="news-item" href="{e(item.get("link","#"))}" target="_blank" rel="noopener">
          <div class="news-num">→</div>
          <div>
            <div class="news-title" style="font-size:13px">{e(item["title"])}</div>
            <div class="news-meta"><span class="news-source">{e(item.get("source",""))}</span> <span>{fmt_date(item.get("date",""))}</span></div>
          </div>
        </a>'''
    else:
        sinner_html = '<div class="empty">Keine Daten verfügbar</div>'

    tennis_html = ""
    if tennis:
        for item in tennis[:3]:
            tennis_html += f'''<a class="good-item" href="{e(item.get("link","#"))}" target="_blank" rel="noopener">
          <div class="good-title" style="font-size:13px">{e(item["title"])}</div>
          <div class="good-desc">{fmt_date(item.get("date",""))}</div>
        </a>'''
    else:
        tennis_html = '<div class="empty">Keine Daten</div>'

    return f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Daily Feed · Dominic</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;1,400&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--ink:#111;--bg:#f5f4ef;--white:#fefefe;--muted:#888;--line:#dddbd4;--red:#c0392b;--arsenal:#EF0107;--good:#2d6a4f;--tennis:#1a6634}}
body{{background:var(--bg);color:var(--ink);font-family:'DM Sans',sans-serif;font-weight:400;min-height:100vh}}
.masthead{{background:var(--white);border-bottom:2px solid var(--ink);padding:0 32px;display:flex;justify-content:space-between;align-items:stretch}}
.logo{{font-family:'Playfair Display',serif;font-size:28px;font-weight:700;letter-spacing:-.02em;padding:14px 0;display:flex;align-items:center;gap:10px}}
.logo-dot{{color:var(--red)}}
.nav{{display:flex;align-items:stretch}}
.nav-item{{padding:0 16px;display:flex;align-items:center;font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);border-left:1px solid var(--line)}}
.masthead-right{{display:flex;align-items:center;padding:0 0 0 24px;border-left:1px solid var(--line)}}
.date-display{{text-align:right;font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);line-height:1.6}}
.date-display strong{{display:block;color:var(--ink);font-size:12px}}
.tldr-bar{{background:#1a1a1a;color:#fff;padding:14px 32px;display:grid;grid-template-columns:auto 1fr 1fr;gap:0 32px;align-items:start;border-bottom:1px solid #333}}
.tldr-label{{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.2em;text-transform:uppercase;color:var(--red);padding-top:2px;white-space:nowrap;line-height:1.8}}
.tldr-grid{{display:grid;grid-template-rows:repeat(2,auto);gap:6px}}
.tldr-item{{font-size:12px;line-height:1.4;color:#ccc;padding-left:10px;border-left:1px solid #333}}
.tldr-item strong{{color:#fff;font-weight:500}}
.main{{max-width:1280px;margin:0 auto;padding:28px 32px 60px;display:grid;grid-template-columns:1fr 1fr 340px;gap:24px;align-items:start}}
.card{{background:var(--white);border:1px solid var(--line)}}
.card-header{{display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-bottom:1px solid var(--line)}}
.card-label{{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted)}}
.card-label.red{{color:var(--red)}}.card-label.arsenal{{color:var(--arsenal)}}.card-label.good{{color:var(--good)}}.card-label.tennis{{color:var(--tennis)}}
.card-more{{font-family:'DM Mono',monospace;font-size:9px;color:var(--muted)}}
.news-item{{display:grid;grid-template-columns:28px 1fr;gap:0 10px;padding:11px 14px;border-bottom:1px solid var(--line);align-items:start;text-decoration:none;color:inherit;transition:background .12s}}
.news-item:last-child{{border-bottom:none}}
.news-item:hover{{background:var(--bg)}}
.news-num{{font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);padding-top:3px;text-align:right}}
.news-title{{font-family:'Playfair Display',serif;font-size:15px;line-height:1.35;font-weight:400;margin-bottom:3px}}
.news-meta{{font-size:11px;color:var(--muted);display:flex;gap:8px}}
.news-source{{font-weight:500;color:#666}}
.news-desc{{font-size:12px;color:#666;line-height:1.4;margin-top:3px}}
.good-item{{display:block;padding:12px 14px;border-bottom:1px solid var(--line);text-decoration:none;color:inherit;transition:background .12s}}
.good-item:last-child{{border-bottom:none}}
.good-item:hover{{background:var(--bg)}}
.good-title{{font-family:'Playfair Display',serif;font-size:14px;line-height:1.3;margin-bottom:3px}}
.good-desc{{font-size:12px;color:#666;line-height:1.4}}
.weather-body{{padding:16px 14px 12px}}
.weather-row{{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px}}
.temp-hero{{font-family:'Playfair Display',serif;font-size:56px;font-weight:400;line-height:1;letter-spacing:-.03em}}
.weather-icon{{font-size:42px;line-height:1}}
.weather-cond{{font-size:13px;color:var(--muted);margin-top:4px}}
.weather-hilo{{font-family:'DM Mono',monospace;font-size:11px;color:var(--muted);margin-top:2px}}
.gear-box{{margin:10px 0;padding:10px 12px;border-left:3px solid;background:var(--bg);font-size:13px;font-style:italic;line-height:1.4}}
.rain-label{{font-family:'DM Mono',monospace;font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.1em;margin-top:6px}}
.rain-bars{{display:grid;grid-template-columns:repeat(8,1fr);gap:3px;height:52px;align-items:flex-end;margin:8px 0 4px}}
.rain-bar-wrap{{display:flex;flex-direction:column;align-items:center;height:100%;justify-content:flex-end;gap:3px}}
.rain-bar{{width:100%;border-radius:1px;min-height:2px}}
.rain-bar-label{{font-family:'DM Mono',monospace;font-size:8px;color:var(--muted)}}
.forecast-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:10px}}
.fday{{text-align:center;padding:8px 4px;border:1px solid var(--line);border-radius:2px}}
.fday-name{{font-family:'DM Mono',monospace;font-size:9px;color:var(--muted);text-transform:uppercase;margin-bottom:4px}}
.fday-icon{{font-size:18px}}
.fday-temp{{font-size:14px;font-weight:500;margin-top:2px}}
.fday-rain{{font-family:'DM Mono',monospace;font-size:9px;color:#60a5fa}}
.match-block{{padding:12px 14px;border-bottom:1px solid var(--line)}}
.match-block:last-child{{border-bottom:none}}
.match-comp{{font-family:'DM Mono',monospace;font-size:9px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px}}
.match-note{{font-size:12px;color:#666;margin-top:4px;font-style:italic}}
.fact-body{{padding:16px 14px;background:#1a1a1a}}
.fact-eyebrow{{font-family:'DM Mono',monospace;font-size:9px;letter-spacing:.2em;text-transform:uppercase;color:var(--red);margin-bottom:10px}}
.fact-text{{font-family:'Playfair Display',serif;font-size:15px;font-style:italic;line-height:1.5;color:#eee}}
.col-left,.col-mid,.col-right{{display:flex;flex-direction:column;gap:20px}}
.empty{{padding:12px 14px;font-size:12px;color:var(--muted);font-style:italic}}
.refresh-note{{grid-column:1/-1;display:flex;align-items:center;justify-content:space-between;padding:12px 0 0;border-top:1px solid var(--line);font-family:'DM Mono',monospace;font-size:10px;color:var(--muted);gap:20px}}
@media(max-width:1024px){{.main{{grid-template-columns:1fr 1fr}}.col-right{{grid-column:1/-1;display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px}}.tldr-bar{{grid-template-columns:auto 1fr}}}}
@media(max-width:680px){{.main{{grid-template-columns:1fr;padding:16px}}.masthead{{padding:0 16px}}.tldr-bar{{display:none}}.col-right{{grid-template-columns:1fr}}.nav{{display:none}}}}
</style>
</head>
<body>
<header class="masthead">
  <div class="logo"><span class="logo-dot">●</span> Daily Feed</div>
  <nav class="nav">
    <span class="nav-item">TL;DR</span>
    <span class="nav-item">Wetter</span>
    <span class="nav-item">Arsenal</span>
    <span class="nav-item">Tennis</span>
    <span class="nav-item">Good News</span>
  </nav>
  <div class="masthead-right">
    <div class="date-display">
      <strong>{weekday}, {date_str}</strong>
      Wien · Stand {time_str}
    </div>
  </div>
</header>

<div class="tldr-bar">
  <div class="tldr-label">TL;DR —<br>Auf einen<br>Blick</div>
  <div class="tldr-grid">{tldr_left}</div>
  <div class="tldr-grid">{tldr_right}</div>
</div>

<main class="main">
  <div class="col-left">
    <div class="card">
      <div class="card-header">
        <span class="card-label red">Top News · Welt · Heute</span>
        <span class="card-more">BBC · Guardian · NYT</span>
      </div>
      {news_list_html(top_news, 5)}
    </div>
    <div class="card">
      <div class="card-header">
        <span class="card-label good">Good News · Diese Woche</span>
        <span class="card-more">positive.news</span>
      </div>
      {good_html}
    </div>
  </div>

  <div class="col-mid">
    <div class="card">
      <div class="card-header">
        <span class="card-label arsenal">⚽ Arsenal London</span>
        <span class="card-more">BBC Sport</span>
      </div>
      {arsenal_matches_html(arsenal)}
    </div>
    <div class="card">
      <div class="card-header">
        <span class="card-label arsenal">Arsenal News</span>
        <span class="card-more">arseblog · BBC Sport</span>
      </div>
      {news_list_html(arsenal_news, 4)}
    </div>
  </div>

  <div class="col-right">
    <div class="card">
      <div class="card-header">
        <span class="card-label">🌤 Wetter · Wien</span>
        <span class="card-more">Open-Meteo · ECMWF</span>
      </div>
      <div class="weather-body">{weather_html(weather)}</div>
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-label tennis">🎾 Jannik Sinner</span>
        <span class="card-more">Google News</span>
      </div>
      {sinner_html}
      <div class="card-header" style="border-top:1px solid var(--line);border-bottom:none;margin-top:4px">
        <span class="card-label tennis">ATP · Turniere</span>
      </div>
      {tennis_html}
    </div>

    <div class="card">
      <div class="card-header">
        <span class="card-label red">◆ Fact des Tages</span>
      </div>
      <div class="fact-body">
        <div class="fact-eyebrow">Did you know</div>
        <div class="fact-text">{e(fact)}</div>
      </div>
    </div>
  </div>

  <div class="refresh-note">
    <span>Generiert: {gen} · Open-Meteo, BBC, Guardian, arseblog, ATP, Positive.news</span>
    <span>Aktualisiert täglich automatisch um 7:00 Uhr</span>
  </div>
</main>
</body>
</html>"""

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"Building Daily Feed — {NOW.strftime('%A, %d %B %Y %H:%M')} Vienna")

    weather      = get_weather()
    top_news     = get_top_news()
    good_news    = get_good_news()
    arsenal      = get_arsenal()
    arsenal_news = get_arsenal_news()
    sinner       = get_sinner()
    tennis       = get_tennis()
    fact         = get_fact()

    html_out = build_html(weather, top_news, good_news, arsenal, arsenal_news, sinner, tennis, fact)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_out)

    print(f"✓ index.html written ({len(html_out)//1024} KB)")

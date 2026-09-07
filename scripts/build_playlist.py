import os
import re
import time
import urllib.request

XTREAM_URL = os.environ["XTREAM_URL"]
AR_URL = "https://iptv-org.github.io/iptv/countries/ar.m3u"
OUTPUT_FILE = "lista.m3u"

def strip_accents(s):
    table = str.maketrans("áéíóúüñəšžøł", "aeiouuneszol")
    return s.translate(table)

ADULT_KEYWORDS = [
    "adulto", "adult", "xxx", "+18", "18+", "porn",
    "erotic", "erotico", "playboy", "brazzers",
    "milf", "fetish", "hustler"
]

EXCLUDE_KEYWORDS = [strip_accents(k) for k in [
    "chile deporte", "chile regionales", "chile",
    "deporte ecuador", "ecuador",
    "radios chile", "radios argentina", "radio peru", "radios peru",
    "colombia", "radios colombia", "radios mexico",
    "puerto rico", "nicaragua", "brasil", "uruguay",
    "deportes uruguay", "deporte uruguay", "portugal",
    "usa childish", "panama", "mls exclusivo", "lmp liga arco",
    "republica dominicana", "peru", "futbol chile", "deporte colombia",
    "italia", "nba exclusivo", "futbol paraguay",
    "usa entertainment", "usa movies", "usa news", "usa fox", "tv usa",
    "bolivia", "costa rica", "deporte costa rica",
    "telemundo", "univision", "galavision", "unimas",
    "paraguay", "venezuela", "deporte bolivia", "canada", "guatemala",
    "deportes pe",
    "telenovelas top",
    "serie", "pelicula", "saga", "cine", "dorama", "estreno",
]]

def fetch(url, retries=8, base_delay=5, max_delay=60):
    last_error = None
    delay = base_delay
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            last_error = e
            print(f"Intento {attempt}/{retries} fallo para {url}: {e}")
            if attempt < retries:
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
    raise last_error

def get_group(extinf_line):
    m = re.search(r'group-title="([^"]*)"', extinf_line)
    if not m:
        return ""
    g = re.sub(r'^[^a-zA-Z0-9]+', '', m.group(1))
    return strip_accents(g.strip().lower())

def is_excluded(extinf_line):
    group = get_group(extinf_line)
    name = strip_accents(extinf_line.rsplit(",", 1)[-1].strip().lower())
    text = group + " " + name
    if any(k in text for k in ADULT_KEYWORDS):
        return True
    if any(k in text for k in EXCLUDE_KEYWORDS):
        return True
    return False

def parse_and_filter(content):
    lines = content.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#EXTM3U"):
            i += 1
            continue
        if line.startswith("#EXTINF"):
            entry = [line]
            i += 1
            while i < len(lines) and not lines[i].startswith("#EXTINF"):
                entry.append(lines[i])
                i += 1
            if not is_excluded(line):
                out.extend(entry)
        else:
            i += 1
    return out

def main():
    xtream_content = fetch(XTREAM_URL)
    ar_content = fetch(AR_URL)

    merged = ["#EXTM3U"]
    merged.extend(parse_and_filter(ar_content))
    merged.extend(parse_and_filter(xtream_content))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(merged) + "\n")

    print(f"Listo: {len(merged)} lineas escritas en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

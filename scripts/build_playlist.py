import os
import re
import time
import urllib.request

XTREAM_URL = os.environ["XTREAM_URL"]
AR_URL = "https://iptv-org.github.io/iptv/countries/ar.m3u"
OUTPUT_FILE = "lista.m3u"

def strip_accents(s):
    table = str.maketrans("áéíóúüñə", "aeiouune")
    return s.translate(table)

def normalize(s):
    return strip_accents(s.strip().lower())

ADULT_KEYWORDS = [
    "adulto", "adult", "xxx", "+18", "18+", "porn",
    "erotic", "erotico", "playboy", "brazzers",
    "milf", "fetish", "hustler"
]

# Unicas categorias de tu Xtream que se muestran; el resto queda oculto
KEEP_GROUPS = [normalize(g) for g in [
    "telenovelas", "radios argentina", "deporte vip", "cultura",
    "infantiles", "deporte argentina", "canales", "argentina regionales",
    "tv religiosos", "cine premium", "argentina", "mexico", "general",
    "news", "entertainment",
    "culture;documentary;entertainment;general;movies;music",
    "movies", "music", "undefined", "religious", "business;news",
    "sports", "education", "culture;news", "outdoor", "comedy",
    "movies;news", "animation;kids", "entertainment;news", "cooking",
    "culture", "series", "animation;classic;entertainment", "kids",
    "culture;family;general", "classic movies", "classic;movies",
]]

def get_group(extinf_line):
    m = re.search(r'group-title="([^"]*)"', extinf_line)
    if not m:
        return ""
    g = re.sub(r'^[^a-zA-Z0-9]+', '', m.group(1))
    return normalize(g)

def is_adult(extinf_line):
    group = get_group(extinf_line)
    name = normalize(extinf_line.rsplit(",", 1)[-1])
    text = group + " " + name
    return any(k in text for k in ADULT_KEYWORDS)

def keep_xtream_entry(extinf_line):
    if is_adult(extinf_line):
        return False
    return get_group(extinf_line) in KEEP_GROUPS

def keep_ar_entry(extinf_line):
    return not is_adult(extinf_line)

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

def parse(content, keep_fn):
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
            if keep_fn(line):
                out.extend(entry)
        else:
            i += 1
    return out

def main():
    xtream_content = fetch(XTREAM_URL)
    ar_content = fetch(AR_URL)

    merged = ["#EXTM3U"]
    merged.extend(parse(ar_content, keep_ar_entry))
    merged.extend(parse(xtream_content, keep_xtream_entry))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(merged) + "\n")

    print(f"Listo: {len(merged)} lineas escritas en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

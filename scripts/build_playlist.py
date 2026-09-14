import os
import re
import time
import urllib.request

XTREAM_URL = os.environ["XTREAM_URL"]
AR_URL = "https://iptv-org.github.io/iptv/countries/ar.m3u"
OUTPUT_FILE = "lista.m3u"
EPG_URL = "https://epgshare01.online/epgshare01/epg_ripper_AR1.xml.gz"

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

# Canales con EPG confirmado en epgshare01 AR1: (patron a buscar en el nombre, tvg-id correcto)
EPG_MAP = [
    (re.compile(r'\btelefe\b', re.IGNORECASE), "Telefe.ar"),
    (re.compile(r'\bc5n\b', re.IGNORECASE), "C5N.ar"),
    (re.compile(r'\ba24\b', re.IGNORECASE), "A24.ar"),
    (re.compile(r'trece', re.IGNORECASE), "ElTrece.ar"),
    (re.compile(r'\btn\b', re.IGNORECASE), "TodoNoticias.ar"),
    (re.compile(r't[vy]\s*p.blica', re.IGNORECASE), "TVPublica.ar"),
    (re.compile(r'net\s*tv', re.IGNORECASE), "NETTV.ar"),
    (re.compile(r'el\s*nueve', re.IGNORECASE), "ElNueve.ar"),
    (re.compile(r'canal\s*26', re.IGNORECASE), "Canal26.ar"),
    (re.compile(r'cronica', re.IGNORECASE), "CronicaTV.ar"),
]

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

def apply_epg_id(line):
    name = line.rsplit(",", 1)[-1]
    for pattern, tvg_id in EPG_MAP:
        if pattern.search(name):
            if 'tvg-id="' in line:
                return re.sub(r'tvg-id="[^"]*"', f'tvg-id="{tvg_id}"', line, count=1)
            else:
                return re.sub(r'^(#EXTINF:[-\d]+)', rf'\1 tvg-id="{tvg_id}"', line, count=1)
    return line

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
                entry[0] = apply_epg_id(entry[0])
                out.extend(entry)
        else:
            i += 1
    return out

def main():
    xtream_content = fetch(XTREAM_URL)
    ar_content = fetch(AR_URL)

    merged = [f'#EXTM3U x-tvg-url="{EPG_URL}"']
    merged.extend(parse(ar_content, keep_ar_entry))
    merged.extend(parse(xtream_content, keep_xtream_entry))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(merged) + "\n")

    print(f"Listo: {len(merged)} lineas escritas en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

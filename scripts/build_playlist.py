import re
import time
import urllib.request

OUTPUT_FILE = "lista.m3u"
EPG_URL = "https://raw.githubusercontent.com/alxbxgmr-ops/Mi-Iptv/main/epg.xml"
MIN_CHANNELS = 50

# (url, es_solo_argentina)
SOURCES = [
    ("https://iptv-org.github.io/iptv/countries/ar.m3u", True),
    ("https://www.m3u.cl/lista/AR.m3u", True),
    ("https://telechancho.github.io/infinity.m3u", False),
    ("https://iptv-org.github.io/iptv/index.m3u", False),
]

ADULT_KEYWORDS = [
    "adulto", "adult", "xxx", "+18", "18+", "porn", "erotic", "erotik",
    "erotico", "playboy", "brazzers", "milf", "fetish", "hustler", "hentai",
    "onlyfans", "hardcore", "dorcel", "bangbros", "sexy", "sexo",
    "penthouse", "redlight", "red light", "venus",
]

EPG_MAP = [
    (re.compile(r'\btelefe\b', re.I), "Telefe.ar"),
    (re.compile(r'\bc5n\b', re.I), "C5N.ar"),
    (re.compile(r'\ba24\b', re.I), "A24.ar"),
    (re.compile(r'trece', re.I), "Canal 13.ar"),
    (re.compile(r'\btn\b', re.I), "TN.ar"),
    (re.compile(r't[vy]\s*p.blica', re.I), "TV Pública.ar"),
    (re.compile(r'net\s*tv', re.I), "Net TV.ar"),
    (re.compile(r'el\s*nueve', re.I), "Canal 9.ar"),
    (re.compile(r'canal\s*26', re.I), "Canal 26.ar"),
    (re.compile(r'cronica', re.I), "Cronica.ar"),
    (re.compile(r'la\s*nacion\s*\+?', re.I), "LN+.ar"),
    (re.compile(r'(?<!latin )\bamerica\b', re.I), "América TV.ar"),
    (re.compile(r'\bvolver\b', re.I), "Volver.ar"),
    (re.compile(r'gourmet', re.I), "El Gourmet.ar"),
    (re.compile(r'ciudad\s*magazine', re.I), "Ciudad Magazine.ar"),
]


def normalize(s):
    s = s.strip().lower()
    return s.translate(str.maketrans("áéíóúüñ", "aeiouun"))


def attr(line, name):
    m = re.search(name + r'="([^"]*)"', line)
    return m.group(1) if m else ""


def display_name(line):
    return line.rsplit(",", 1)[-1].strip()


def is_adult(line):
    text = normalize(attr(line, "group-title") + " " + display_name(line))
    return any(k in text for k in ADULT_KEYWORDS)


def is_argentina(line):
    tvg_id = attr(line, "tvg-id")
    group = normalize(attr(line, "group-title"))
    name = normalize(display_name(line))
    if re.search(r'\.ar(@|$)', tvg_id, re.I):
        return True
    if "argentin" in group or "argentin" in name:
        return True
    return bool(re.match(r'(ar|arg)\s*[|:\-]', name))


def epg_id_for(line):
    name = display_name(line)
    for pattern, tvg_id in EPG_MAP:
        if pattern.search(name):
            return tvg_id
    return None


def set_tvg_id(line, tvg_id):
    if 'tvg-id="' in line:
        return re.sub(r'tvg-id="[^"]*"', 'tvg-id="%s"' % tvg_id, line, count=1)
    return re.sub(r'^(#EXTINF:\s*[-\d.]+)', r'\1 tvg-id="%s"' % tvg_id,
                  line, count=1)


def fetch(url, retries=3, base_delay=5, timeout=60):
    delay = base_delay
    for attempt in range(1, retries + 1):
        print(f"Descargando {url} (intento {attempt}/{retries})")
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read().decode("utf-8", errors="ignore")
            print(f"OK: {len(data)} caracteres")
            return data
        except Exception as e:
            print(f"Fallo: {e}")
            if attempt < retries:
                time.sleep(delay)
                delay *= 2
    return None


def process(content, only_ar, seen):
    lines = content.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        i += 1
        if not line.startswith("#EXTINF"):
            continue
        entry = [line]
        while i < len(lines) and not lines[i].startswith("#EXTINF"):
            entry.append(lines[i])
            i += 1
        urls = [l.strip() for l in entry[1:]
                if l.strip() and not l.startswith("#")]
        if not urls or urls[0] in seen:
            continue
        if is_adult(line):
            continue
        seen.add(urls[0])
        if only_ar or is_argentina(line):
            tvg_id = epg_id_for(line)
            if tvg_id:
                entry[0] = set_tvg_id(line, tvg_id)
        out.extend(entry)
    return out


def count_channels(lines):
    return sum(1 for l in lines if l.startswith("#EXTINF"))


def main():
    seen = set()
    merged = ['#EXTM3U x-tvg-url="%s"' % EPG_URL]
    for url, only_ar in SOURCES:
        content = fetch(url)
        if content is None:
            print(f"FUENTE OMITIDA: {url}")
            continue
        lines = process(content, only_ar, seen)
        print(f"{url}: {count_channels(lines)} canales agregados")
        merged.extend(lines)

    total = count_channels(merged)
    if total < MIN_CHANNELS:
        raise SystemExit(
            f"Solo {total} canales; no se guarda para no pisar la anterior")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(merged) + "\n")
    print(f"Listo: {total} canales en {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

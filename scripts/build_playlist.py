import os
import re
import time
import urllib.request

XTREAM_URL = os.environ["XTREAM_URL"]
AR_URL = "https://iptv-org.github.io/iptv/countries/ar.m3u"
OUTPUT_FILE = "lista.m3u"
EPG_URL = "https://epgshare01.online/epgshare01/epg_ripper_AR1.xml.gz"
EPG_URL_2 = "https://iptv-org.github.io/epg/guides/tv/argentina.epg.xml"
EPG_URL_3 = "https://www.open-epg.com/files/argentina4.xml.txt"
EPG_URL_4 = "https://www.open-epg.com/files/argentina3.xml.txt"

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

# Canales confirmados manualmente (maxima prioridad)
EPG_MAP = [
    (re.compile(r'\btelefe\b', re.IGNORECASE), "Telefe.ar"),
    (re.compile(r'\bc5n\b', re.IGNORECASE), "C5N.ar"),
    (re.compile(r'\ba24\b', re.IGNORECASE), "A24.ar"),
    (re.compile(r'trece', re.IGNORECASE), "ElTrece.ar"),
    (re.compile(r'\btn\b', re.IGNORECASE), "TN.ar"),
    (re.compile(r't[vy]\s*p.blica', re.IGNORECASE), "TVPublica.ar"),
    (re.compile(r'net\s*tv', re.IGNORECASE), "NETTV.ar"),
    (re.compile(r'el\s*nueve', re.IGNORECASE), "ElNueve.ar"),
    (re.compile(r'canal\s*26', re.IGNORECASE), "Canal26.ar"),
    (re.compile(r'cronica', re.IGNORECASE), "CronicaTV.ar"),
    (re.compile(r'la\s*nacion\s*\+?', re.IGNORECASE), "LA NACION +.ar"),
    (re.compile(r'(?<!latin )\bamerica\b', re.IGNORECASE), "América TV.ar"),
    (re.compile(r'\bvolver\b', re.IGNORECASE), "Volver.ar"),
    (re.compile(r'gourmet\s*south', re.IGNORECASE), "El Gourmet.ar"),
    (re.compile(r'ciudad\s*magazine', re.IGNORECASE), "Ciudad Magazine.ar"),
]

# Tabla de respaldo (fuente: open-epg.com argentina4), solo actua si nada de arriba matcheo
OPENEPG_CHANNELS = {
    "24/7 CANAL DE NOTICIAS": "24/7 Canal de Noticias.ar",
    "A&E": "A&E.ar", "AMC": "AMC.ar",
    "ANIMAL PLANET": "Animal Planet.ar",
    "AXN": "AXN.ar", "BABYTV": "BabyTV.ar", "BLOOMBERG": "Bloomberg.ar",
    "CANAL 9": "Canal 9.ar", "CANAL 10": "Canal 10.ar", "CANAL 12": "Canal 12.ar",
    "CANAL 13": "Canal 13.ar", "CANAL 20": "Canal 20.ar",
    "CANAL DE LA CIUDAD": "Canal de la Ciudad.ar", "CANAL RURAL": "Canal Rural.ar",
    "CARTOON NETWORK": "Cartoon Network.ar", "CARTOONITO": "Cartoonito.ar",
    "CINE AR": "CineAr.ar", "CINECANAL": "Cinecanal.ar", "CINELATINO": "Cinelatino.ar",
    "CIUDAD MAGAZINE": "Ciudad Magazine.ar", "CN23": "CN23.ar",
    "COMEDY CENTRAL": "Comedy Central.ar",
    "DEPORTV": "DeporTV.ar",
    "DISCOVERY CHANNEL": "Discovery Channel.ar",
    "DISCOVERY HOME": "Discovery Home & Health.ar",
    "DISCOVERY KIDS": "Discovery Kids.ar", "DISCOVERY SCIENCE": "Discovery Science.ar",
    "DISCOVERY THEATER": "Discovery Theater.ar", "DISCOVERY TURBO": "Discovery Turbo.ar",
    "DISCOVERY WORLD": "Discovery World.ar",
    "DISNEY JUNIOR": "Disney Junior.ar", "DISNEY XD": "Disney XD.ar",
    "DISNEY CHANNEL": "Disney Channel.ar",
    "EL GARAGE": "El Garage Tv.ar",
    "ESPN EXTRA": "ESPN Extra.ar", "ESPN": "ESPN.ar",
    "FOX SPORTS CONO SUR": "FOX Sports Cono Sur.ar",
    "FOX SPORTS PREMIUM": "FOX Sports Premium.ar", "FOX SPORTS": "FOX Sports.ar",
    "FX MOVIES": "FX Movies.ar", "FX": "FX.ar",
    "GLITZ": "Glitz.ar", "GOLDEN EDGE": "Golden Edge.ar", "GOLDEN": "Golden.ar",
    "GOLF CHANNEL": "Golf Channel.ar",
    "HBO 2": "HBO 2.ar", "HBO FAMILY": "HBO Family.ar", "HBO MUNDI": "HBO Mundi.ar",
    "HBO POP": "HBO Pop.ar", "HBO SIGNATURE": "HBO Signature.ar",
    "HBO XTREME": "HBO Xtreme.ar", "HBO PLUS": "HBO Plus Este.ar", "HBO": "HBO.ar",
    "HGTV": "HGTV.ar", "HISTORY 2": "History 2.ar", "HISTORY": "History.ar",
    "INVESTIGATION DISCOVERY": "Investigation Discovery.ar",
    "LAS ESTRELLAS": "Las Estrellas.ar", "LIFETIME": "Lifetime.ar",
    "MTV HITS": "MTV Hits.ar", "MUCHMUSIC": "MuchMusic.ar",
    "NAT GEO KIDS": "Nat Geo Kids.ar", "NATIONAL GEOGRAPHIC WILD": "National Geographic Wild.ar",
    "NATIONAL GEOGRAPHIC": "National Geographic.ar", "NBA TV": "NBA TV.ar",
    "NICK JR": "Nick Jr.ar", "NICKTOONS": "NickToons.ar", "NICK": "Nick.ar",
    "PAKAPAKA": "Pakapaka.ar", "PARAMOUNT NETWORK": "Paramount Network.ar",
    "PARAMOUNT CHANEL": "Paramount Network.ar", "PARAMOUNT CHANNEL": "Paramount Network.ar",
    "PASIONES": "Pasiones.ar", "RAI ITALIA": "Rai Italia.ar",
    "SMITHSONIAN": "Smithsonian Channel.ar",
    "SONY": "Sony.ar", "SPACE": "Space.ar",
    "STAR ACTION": "Star Action.ar", "STAR CHANNEL": "Star Channel.ar",
    "STAR CINEMA": "Star Cinema.ar", "STAR CLASSICS": "Star Classics.ar",
    "STAR COMEDY": "Star Comedy.ar", "STAR FUN": "Star Fun.ar",
    "STAR HITS": "Star Hits.ar", "STAR LIFE": "Star Life.ar", "STAR SERIES": "Star Series.ar",
    "STUDIO UNIVERSAL": "Studio Universal.ar", "SYFY": "Syfy.ar",
    "TBS": "TBS.ar", "TCM": "TCM.ar",
    "TELEFE ROSARIO": "Telefe Rosario.ar", "TELEFE SANTA FE": "Telefe Santa Fe.ar",
    "TELEMUNDO INTERNACIONAL": "Telemundo Internacional.ar",
    "TLC": "TLC.ar", "TLNOVELAS": "TLNovelas.ar",
    "TNT SERIES": "TNT Series.ar", "TNT SPORTS": "TNT Sports.ar", "TNT": "TNT.ar",
    "TOONCAST": "Tooncast.ar", "TRUTV": "TruTV.ar",
    "UNIVERSAL TV": "Universal TV.ar",
    "VH1 MEGA HITS": "VH1 Mega Hits.ar", "VIAJAR": "Viajar.ar",
    "WARNER CHANNEL": "Warner Channel.ar", "ZOOMOO": "ZooMoo.ar",
}
OPENEPG_NAMES_SORTED = sorted(OPENEPG_CHANNELS.keys(), key=len, reverse=True)

def normalize_loose(s):
    s = strip_accents(s)
    s = re.sub(r'[^A-Za-z0-9&+ ]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip().upper()
    return s

def match_openepg(name):
    norm_name = normalize_loose(name)
    for candidate in OPENEPG_NAMES_SORTED:
        if candidate in norm_name:
            return OPENEPG_CHANNELS[candidate]
    return None

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
    tvg_id = None
    for pattern, candidate_id in EPG_MAP:
        if pattern.search(name):
            tvg_id = candidate_id
            break
    if tvg_id is None:
        tvg_id = match_openepg(name)
    if tvg_id is None:
        return line
    if 'tvg-id="' in line:
        return re.sub(r'tvg-id="[^"]*"', f'tvg-id="{tvg_id}"', line, count=1)
    return re.sub(r'^(#EXTINF:[-\d]+)', rf'\1 tvg-id="{tvg_id}"', line, count=1)

def keep_xtream_entry(extinf_line):
    if is_adult(extinf_line):
        return False
    return get_group(extinf_line) in KEEP_GROUPS

def keep_ar_entry(extinf_line):
    return not is_adult(extinf_line)

def fetch(url, retries=8, base_delay=5, max_delay=60, timeout=30):
    last_error = None
    delay = base_delay
    for attempt in range(1, retries + 1):
        print(f"Descargando {url[:50]}... (intento {attempt}/{retries})")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read().decode("utf-8", errors="ignore")
                print(f"Descarga OK ({len(data)} caracteres)")
                return data
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

    merged = [f'#EXTM3U x-tvg-url="{EPG_URL},{EPG_URL_2},{EPG_URL_3},{EPG_URL_4}"']
    merged.extend(parse(ar_content, keep_ar_entry))
    merged.extend(parse(xtream_content, keep_xtream_entry))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(merged) + "\n")

    print(f"Listo: {len(merged)} lineas escritas en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

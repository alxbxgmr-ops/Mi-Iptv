import os
import re
import time
import urllib.request

XTREAM_URL = os.environ["XTREAM_URL"]
AR_URL = "https://iptv-org.github.io/iptv/countries/ar.m3u"
OUTPUT_FILE = "lista.m3u"
EPG_URL = "https://epgshare01.online/epgshare01/epg_ripper_AR1.xml.gz"
EPG_URL_2 = "https://iptv-org.github.io/epg/guides/tv/argentina.epg.xml"
EPG_URL_3 = "https://www.open-epg.com/files/argentina4.xml"

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

# Canales confirmados manualmente (prioridad alta, se revisan primero)
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
    (re.compile(r'\bamerica\b', re.IGNORECASE), "AmericaTV.ar"),
    (re.compile(r'\bvolver\b', re.IGNORECASE), "Volver.ar"),
    (re.compile(r'gourmet\s*south', re.IGNORECASE), "EL GOURMET.ar"),
    (re.compile(r'ciudad\s*magazine', re.IGNORECASE), "CiudadMagazine.ar"),
]

# Tabla generica de open-epg.com (fallback si nada de arriba matcheo)
OPENEPG_CHANNELS = {
    "26 TV": "26 TV.ar", "A&E HD": "A&E HD.ar", "A&E": "A&E.ar",
    "ADRENALINA SPORTS HD": "ADRENALINA SPORTS HD.ar",
    "ADULT SWIM HD": "ADULT SWIM HD.ar", "ADULT SWIM": "ADULT SWIM.ar",
    "ALIENTOVISION": "ALIENTOVISION.ar", "ALLEGRO HD": "ALLEGRO HD.ar",
    "AMC": "AMC.ar", "AMERICA 2": "AMERICA 2.ar", "AMERICA 24": "AMERICA 24.ar",
    "AMERICA SPORTS": "AMERICA SPORTS.ar",
    "ANIMAL PLANET HD": "ANIMAL PLANET HD.ar", "ANIMAL PLANET": "ANIMAL PLANET.ar",
    "AREA PLUS": "AREA PLUS.ar", "ARGENTINISIMA": "ARGENTINISIMA.ar",
    "AXN HD": "AXN HD.ar", "AXN": "AXN.ar", "BOLIVIA TV": "BOLIVIA TV.ar",
    "CANAL 3 ROSARIO": "CANAL 3 ROSARIO.ar", "CANAL 4 SALTA": "CANAL 4 SALTA.ar",
    "CANAL 4 SGO": "CANAL 4 SGO.ar", "CANAL 7 SGO": "CANAL 7 SGO.ar",
    "CANAL A": "CANAL A.ar", "CANAL LUZ": "CANAL LUZ.ar",
    "CANAL RURAL": "CANAL RURAL.ar", "CANAL VASCO": "CANAL VASCO.ar",
    "CARTOON NETWORK HD": "CARTOON NETWORK HD.ar", "CARTOON NETWORK": "CARTOON NETWORK.ar",
    "CARTOONITO": "CARTOONITO.ar",
    "CINECANAL HD": "CINECANAL HD.ar", "CINECANAL": "CINECANAL.ar",
    "CINEMAX HD": "CINEMAX HD.ar", "CINEMAX": "CINEMAX.ar",
    "CM MUSICAL": "CM MUSICAL.ar", "CNN": "CNN.ar",
    "DEPORTV HD": "DEPORTV HD.ar", "DEPORTV": "DEPORTV.ar", "DHE HD": "DHE HD.ar",
    "DISCOVERY CHANNEL HD": "DISCOVERY CHANNEL HD.ar", "DISCOVERY CHANNEL": "DISCOVERY CHANNEL.ar",
    "DISCOVERY HOME AND HEALTH HD": "DISCOVERY HOME AND HEALTH HD.ar",
    "DISCOVERY HOME AND HEALTH": "DISCOVERY HOME AND HEALTH.ar",
    "DISCOVERY ID HD": "DISCOVERY ID HD.ar", "DISCOVERY ID": "DISCOVERY ID.ar",
    "DISCOVERY KIDS HD": "DISCOVERY KIDS HD.ar", "DISCOVERY KIDS": "DISCOVERY KIDS.ar",
    "DISCOVERY SCIENCE": "DISCOVERY SCIENCE.ar",
    "DISCOVERY THEATER HD": "DISCOVERY THEATER HD.ar",
    "DISCOVERY TURBO HD": "DISCOVERY TURBO HD.ar",
    "DISCOVERY WORLD HD": "DISCOVERY WORLD HD.ar",
    "DISNEY HD": "DISNEY HD.ar", "DISNEY JR": "DISNEY JR.ar", "DISNEY": "DISNEY.ar",
    "EL GARAGE HD": "EL GARAGE HD.ar", "EL GARAGE": "EL GARAGE.ar",
    "EL GOURMET HD": "EL GOURMET HD.ar",
    "ENCUENTRO": "ENCUENTRO.ar", "ENLACE TBN": "ENLACE TBN.ar",
    "ENTERTAINMENT TELEVISION HD": "ENTERTAINMENT TELEVISION HD.ar",
    "ENTERTAINMENT": "ENTERTAINMENT.ar",
    "ESPN 2 HD": "ESPN 2 HD.ar", "ESPN 2": "ESPN 2.ar",
    "ESPN 3 HD": "ESPN 3 HD.ar", "ESPN 3": "ESPN 3.ar",
    "ESPN 4 HD": "ESPN 4 HD.ar", "ESPN 6 HD": "ESPN 6 HD.ar",
    "ESPN HD": "ESPN HD.ar", "ESPN PREMIUM HD": "ESPN PREMIUM HD.ar",
    "ESPN PREMIUM": "ESPN PREMIUM.ar", "ESPN": "ESPN.ar",
    "EUROCHANNEL": "EUROCHANNEL.ar", "EUROPA EUROPA": "EUROPA EUROPA.ar",
    "EWTN": "EWTN.ar", "EXPRESS FAN": "EXPRESS FAN.ar",
    "FILM AND ARTS": "FILM AND ARTS.ar",
    "FOX SPORTS 2 HD": "FOX SPORTS 2 HD.ar", "FOX SPORTS 2": "FOX SPORTS 2.ar",
    "FOX SPORTS 3": "FOX SPORTS 3.ar", "FOX SPORTS HD": "FOX SPORTS HD.ar",
    "FOX SPORTS": "FOX SPORTS.ar", "FX": "FX.ar",
    "GALICIA TV": "GALICIA TV.ar", "GOLDEN": "GOLDEN.ar",
    "H2 HD": "H2 HD.ar", "H2": "H2.ar",
    "HBO 2 HD": "HBO 2 HD.ar", "HBO 2": "HBO 2.ar", "HBO FAMILY": "HBO FAMILY.ar",
    "HBO HD": "HBO HD.ar", "HBO MUNDI": "HBO MUNDI.ar",
    "HBO PLUS HD": "HBO PLUS HD.ar", "HBO PLUS": "HBO PLUS.ar",
    "HBO POP HD": "HBO POP HD.ar", "HBO SIGNATURE": "HBO SIGNATURE.ar",
    "HBO XTREME": "HBO XTREME.ar", "HBO": "HBO.ar",
    "HGTV": "HGTV.ar", "HISTORY HD": "HISTORY HD.ar", "HISTORY": "HISTORY.ar",
    "LAS ESTRELLAS": "LAS ESTRELLAS.ar",
    "LIFETIME HD": "LIFETIME HD.ar", "LIFETIME": "LIFETIME.ar",
    "LOVE NATURE HD": "LOVE NATURE HD.ar", "MAGAZINE": "MAGAZINE.ar",
    "MAS CHIC": "MAS CHIC.ar", "MTV 80S": "MTV 80S.ar", "MTV HITS": "MTV HITS.ar",
    "MTV00": "MTV00.ar", "MTV": "MTV.ar", "NAT GEO": "NAT GEO.ar",
    "NICK JR": "NICK JR.ar", "NICKELODEON": "NICKELODEON.ar",
    "NUEVO TIEMPO": "NUEVO TIEMPO.ar", "PAKAPAKA": "PAKAPAKA.ar",
    "QUIERO": "QUIERO.ar", "RADIO NACIONAL": "RADIO NACIONAL.ar", "RAI": "RAI.ar",
    "SBT BRASIL": "SBT BRASIL.ar", "SONY HD": "SONY HD.ar",
    "SONY MOVIES": "SONY MOVIES.ar", "SONY": "SONY.ar",
    "SPACE HD": "SPACE HD.ar", "SPACE": "SPACE.ar",
    "STAR CHANNEL HD": "STAR CHANNEL HD.ar", "STAR CHANNEL": "STAR CHANNEL.ar",
    "STUDIO UNIVERSAL HD": "STUDIO UNIVERSAL HD.ar", "STUDIO UNIVERSAL": "STUDIO UNIVERSAL.ar",
    "TCM": "TCM.ar", "TEC TV": "TEC TV.ar", "TELE 10": "TELE 10.ar",
    "TELEFE ROSARIO": "TELEFE ROSARIO.ar", "TELEFE SALTA": "TELEFE SALTA.ar",
    "TELEMAX": "TELEMAX.ar", "TELEMUNDO HD": "TELEMUNDO HD.ar",
    "TELEMUNDO": "TELEMUNDO.ar", "TELESUR": "TELESUR.ar", "TLC": "TLC.ar",
    "TLNOVELAS": "TLNOVELAS.ar", "TNT HD": "TNT HD.ar",# Canales con EPG confirmado en epgshare01 AR1: (patron a buscar en el nombre, tvg-id correcto)
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
    (re.compile(r'la\s*nacion\s*\+?', re.IGNORECASE), "LaNacionPlus.ar"),
    (re.compile(r'\bamerica\b', re.IGNORECASE), "AmericaTV.ar"),
    (re.compile(r'\bvolver\b', re.IGNORECASE), "Volver.ar"),
    (re.compile(r'gourmet', re.IGNORECASE), "ElGourmet.ar"),
    (re.compile(r'ciudad\s*magazine', re.IGNORECASE), "CiudadMagazine.ar"),
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

    merged = [f'#EXTM3U x-tvg-url="{EPG_URL},https://iptv-org.github.io/epg/guides/tv/argentina.epg.xml"']
    merged.extend(parse(ar_content, keep_ar_entry))
    merged.extend(parse(xtream_content, keep_xtream_entry))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(merged) + "\n")

    print(f"Listo: {len(merged)} lineas escritas en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

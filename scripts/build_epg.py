import time
import gzip
import urllib.request
import xml.etree.ElementTree as ET

# Orden de prioridad: la primera fuente que tenga un canal se queda con el
SOURCES = [
    ("https://www.open-epg.com/files/argentina4.xml", False),
    ("https://iptv-epg.org/files/epg-ar.xml", False),
    ("https://epgshare01.online/epgshare01/epg_ripper_AR1.xml.gz", True),
    ("https://iptv-org.github.io/epg/guides/tv/argentina.epg.xml", False),
]

OUTPUT_FILE = "epg.xml"

def fetch_bytes(url, retries=5, base_delay=5, max_delay=40, timeout=30):
    delay = base_delay
    for attempt in range(1, retries + 1):
        print(f"Descargando EPG {url[:60]}... (intento {attempt}/{retries})")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read()
        except Exception as e:
            print(f"Fallo: {e}")
            if attempt < retries:
                time.sleep(delay)
                delay = min(delay * 2, max_delay)
    print(f"Descartando fuente (no disponible): {url}")
    return None

def parse_source(url, gzipped):
    raw = fetch_bytes(url)
    if raw is None:
        return None
    if gzipped:
        try:
            raw = gzip.decompress(raw)
        except Exception as e:
            print(f"No se pudo descomprimir {url}: {e}")
            return None
    try:
        return ET.fromstring(raw)
    except Exception as e:
        print(f"XML invalido en {url}: {e}")
        return None

def main():
    seen_channels = set()
    out_channels = []
    out_programmes = []

    for url, gzipped in SOURCES:
        root = parse_source(url, gzipped)
        if root is None:
            continue

        local_new_ids = set()
        for ch in root.findall("channel"):
            cid = ch.get("id")
            if not cid or cid in seen_channels:
                continue
            local_new_ids.add(cid)
            out_channels.append(ch)

        for prog in root.findall("programme"):
            if prog.get("channel") in local_new_ids:
                out_programmes.append(prog)

        seen_channels.update(local_new_ids)
        print(f"Fuente {url}: {len(local_new_ids)} canales nuevos agregados")

    tv = ET.Element("tv")
    for ch in out_channels:
        tv.append(ch)
    for prog in out_programmes:
        tv.append(prog)

    tree = ET.ElementTree(tv)
    ET.indent(tree, space="  ")
    tree.write(OUTPUT_FILE, encoding="utf-8", xml_declaration=True)
    print(f"Listo: {len(out_channels)} canales, {len(out_programmes)} programas en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

import os
import re
import urllib.request

XTREAM_URL = os.environ["XTREAM_URL"]
AR_URL = "https://iptv-org.github.io/iptv/countries/ar.m3u"
OUTPUT_FILE = "lista.m3u"

ADULT_KEYWORDS = [
    "adulto", "adult", "xxx", "+18", "18+", "porn",
    "erotic", "erotico", "erótic", "playboy", "brazzers",
    "milf", "fetish", "hustler"
]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def is_adult(extinf_line):
    m = re.search(r'group-title="([^"]*)"', extinf_line)
    group = m.group(1).strip().lower() if m else ""
    name = extinf_line.rsplit(",", 1)[-1].strip().lower()
    text = group + " " + name
    return any(k in text for k in ADULT_KEYWORDS)

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
            if not is_adult(line):
                out.extend(entry)
        else:
            i += 1
    return out

def main():
    xtream_content = fetch(XTREAM_URL)
    ar_content = fetch(AR_URL)

    merged = ["#EXTM3U"]
    merged.extend(parse_and_filter(xtream_content))
    merged.extend(parse_and_filter(ar_content))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(merged) + "\n")

    print(f"Listo: {len(merged)} lineas escritas en {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

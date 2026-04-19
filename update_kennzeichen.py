#!/usr/bin/env python3
"""
update_kennzeichen.py
======================
Aktualisiert kennzeichen.json aus zwei unabhängigen Quellen:

  1. Wikidata      – SPARQL-Query auf Property P395 (Kfz-Unterscheidungszeichen)
  2. Wikipedia     – Artikel "Liste der Kfz-Kennzeichen in Deutschland" (wikitext)

Die Daten werden gemerged. Bei Konflikten gewinnt Wikipedia (wird aktiver
gepflegt, reaktivierte Kennzeichen wie RI erscheinen dort schneller).
Vor dem Schreiben werden Mindest-Anzahl und Regression gegen die vorherige
Datei geprüft, damit ein defekter Scrape nicht die App zerschießt.

Aufruf:
    python update_kennzeichen.py            # schreibt kennzeichen.json
    python update_kennzeichen.py --dry-run  # zeigt nur das Diff
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_FILE = os.path.join(BASE_DIR, "kennzeichen.json")

MIN_ENTRIES = 600              # Abbruch, wenn weniger
MAX_REGRESSION_RATIO = 0.05    # max. 5% weniger als vorher

BUNDESLAND_MAP = {
    "Baden-Württemberg":       "BW", "Baden-Wuerttemberg": "BW",
    "Bayern":                  "BY", "Berlin":             "BE",
    "Brandenburg":             "BB", "Bremen":             "HB",
    "Hamburg":                 "HH", "Hessen":             "HE",
    "Mecklenburg-Vorpommern":  "MV", "Niedersachsen":      "NI",
    "Nordrhein-Westfalen":     "NW", "Rheinland-Pfalz":    "RP",
    "Saarland":                "SL", "Sachsen":            "SN",
    "Sachsen-Anhalt":          "ST", "Schleswig-Holstein": "SH",
    "Thüringen":               "TH", "Thueringen":         "TH",
}
USER_AGENT = "kfz-kennzeichen-updater/1.0 (https://github.com/carstenri/kfz-kennzeichen)"


# ----------------------------------------------------------------- HTTP helper
def http_get(url: str, headers: dict | None = None, timeout: int = 60) -> str:
    req = urllib.request.Request(url)
    req.add_header("User-Agent", USER_AGENT)
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


# ----------------------------------------------------------------- Wikidata
SPARQL = r"""
SELECT DISTINCT ?code ?ortLabel ?blLabel WHERE {
  ?ort wdt:P395 ?code .
  ?ort wdt:P17 wd:Q183 .
  OPTIONAL {
    ?ort wdt:P131* ?bl .
    ?bl wdt:P31 wd:Q1221156 .
  }
  FILTER(REGEX(?code, "^[A-ZÄÖÜ]{1,3}$"))
  SERVICE wikibase:label { bd:serviceParam wikibase:language "de". }
}
ORDER BY ?code
"""

def fetch_wikidata() -> dict[str, dict]:
    url = "https://query.wikidata.org/sparql?format=json&query=" + urllib.parse.quote(SPARQL)
    raw = http_get(url, headers={"Accept": "application/sparql-results+json"})
    data = json.loads(raw)
    out: dict[str, dict] = {}
    for row in data.get("results", {}).get("bindings", []):
        code = (row.get("code") or {}).get("value", "").strip().upper()
        name = (row.get("ortLabel") or {}).get("value", "").strip()
        bl_full = (row.get("blLabel") or {}).get("value", "").strip()
        bl = BUNDESLAND_MAP.get(bl_full, "")
        if not code or len(code) > 3 or not name:
            continue
        # Erster Treffer pro Code gewinnt
        if code not in out:
            out[code] = {"name": name, "bundesland": bl or "—"}
    return out


# ---------------------------------------------------------------- Wikipedia
# Die deutsche Liste nutzt pro Buchstaben-Sektion eine Tabelle mit der
# Vorlage {{TabDKfz}}. Jede Zeile besteht aus 4 Zellen, die mehrzeilig
# (je | am Zeilenanfang) notiert sind:  Code · Region · Herleitung · Bundesland.
# rowspan="N" ist häufig (z. B. "A" deckt Stadt + Landkreis Augsburg ab).
WIKI_API = (
    "https://de.wikipedia.org/w/api.php?"
    "action=parse&page=Liste_der_Kfz-Kennzeichen_in_Deutschland"
    "&prop=wikitext&format=json&redirects=1"
)

_LINK_RE    = re.compile(r'\[\[(?:[^|\]]+\|)?([^\]]+)\]\]')
_BOLD_RE    = re.compile(r"'''([^']+)'''")
_ITALIC_RE  = re.compile(r"''([^']+)''")
_TAG_RE     = re.compile(r'<[^>]+>')
_ATTR_PREFIX_RE = re.compile(
    r'^\s*(?:rowspan|colspan|style|class|align|valign|width|bgcolor)\s*=\s*"[^"]*"\s*(?:\s+(?:rowspan|colspan|style|class|align|valign|width|bgcolor)\s*=\s*"[^"]*"\s*)*\|\s*',
    re.IGNORECASE
)

def _strip_formatting(s: str) -> str:
    s = _LINK_RE.sub(r'\1', s)
    s = _BOLD_RE.sub(r'\1', s)
    s = _ITALIC_RE.sub(r'\1', s)
    s = _TAG_RE.sub('', s)
    s = s.replace("&nbsp;", " ")
    return re.sub(r'\s+', ' ', s).strip()

def _cell_content(cell: str) -> str:
    """Entfernt Attribut-Präfixe wie `rowspan="2" |` vor dem Zellinhalt."""
    return _ATTR_PREFIX_RE.sub('', cell, count=1)

def _extract_code(cell: str) -> str | None:
    c = _strip_formatting(_cell_content(cell))
    m = re.match(r'^([A-ZÄÖÜ]{1,3})$', c)
    return m.group(1) if m else None

def _extract_region(cell: str) -> str:
    """Region ist meist der erste Wikilink (Stadt [[Augsburg]] → „Augsburg").
    Fällt auf die bereinigte Zelle zurück, wenn kein Link vorhanden ist."""
    c = _cell_content(cell)
    m = _LINK_RE.search(c)
    if m:
        return m.group(1).strip()
    return _strip_formatting(c)

# Pro Buchstabe eine TabDKfz-Tabelle
_TABLE_RE = re.compile(r'\{\|\s*\{\{TabDKfz[^}]*\}\}[^\n]*\n(.*?)\n\|\}', re.DOTALL)

def fetch_wikipedia() -> dict[str, dict]:
    raw = http_get(WIKI_API)
    data = json.loads(raw)
    wikitext_obj = (data.get("parse") or {}).get("wikitext")
    # format=json  → {"*": "..."};  formatversion=2 → String direkt.
    if isinstance(wikitext_obj, dict):
        wt = wikitext_obj.get("*", "")
    elif isinstance(wikitext_obj, str):
        wt = wikitext_obj
    else:
        wt = ""
    out: dict[str, dict] = {}

    for body in _TABLE_RE.findall(wt):
        # Tabelle in Zeilen-Blöcke splitten; |- trennt Zeilen
        blocks = re.split(r'(?m)^\|\-.*$', body)
        for block in blocks:
            # Zellen sammeln: Zeilen, die mit | beginnen (ohne |-, |}, |+).
            cells = []
            for raw_line in block.split('\n'):
                line = raw_line.rstrip()
                if not line.startswith('|'):
                    continue
                if line.startswith(('|-', '|}', '|+')):
                    continue
                cells.append(line[1:])

            if len(cells) < 4:
                # 1-Zellen-Blöcke sind rowspan-Folgezeilen (weitere Region für
                # denselben Code) – für unsere Zwecke ignorieren.
                continue

            code = _extract_code(cells[0])
            region = _extract_region(cells[1])
            bl_raw = _strip_formatting(_cell_content(cells[3]))
            bl = BUNDESLAND_MAP.get(bl_raw, "")
            if code and region and bl and code not in out:
                out[code] = {"name": region, "bundesland": bl}
    return out


# ----------------------------------------------------------------- Merge
def merge(wp: dict[str, dict], wd: dict[str, dict]):
    all_codes = set(wp) | set(wd)
    merged: dict[str, dict] = {}
    conflicts, only_wp, only_wd = [], [], []
    for code in sorted(all_codes):
        a, b = wp.get(code), wd.get(code)
        if a and b:
            if a.get("bundesland") and b.get("bundesland") and a["bundesland"] != b["bundesland"]:
                conflicts.append((code, a, b))
            merged[code] = a  # Wikipedia gewinnt
        elif a:
            only_wp.append(code); merged[code] = a
        else:
            only_wd.append(code); merged[code] = b
    return merged, conflicts, only_wp, only_wd


# ---------------------------------------------------------------- Diff
def load_previous():
    if not os.path.exists(OUT_FILE):
        return None
    with open(OUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def print_diff(new_data: dict, prev: dict | None):
    if not prev or "kennzeichen" not in prev:
        print(f"  (keine Vorgänger-Datei – {len(new_data)} Einträge neu)")
        return 0, 0, 0
    old = prev["kennzeichen"]
    added   = sorted(set(new_data) - set(old))
    removed = sorted(set(old) - set(new_data))
    changed = sorted(c for c in set(new_data) & set(old) if old[c] != new_data[c])
    if added:
        print(f"  ➕ NEU ({len(added)}): {', '.join(added)}")
    if removed:
        print(f"  ➖ ENTFERNT ({len(removed)}): {', '.join(removed)}")
    if changed:
        print(f"  🔄 GEÄNDERT ({len(changed)}):")
        for c in changed[:30]:
            print(f"     {c}: {old[c]}  →  {new_data[c]}")
        if len(changed) > 30:
            print(f"     … und {len(changed) - 30} weitere")
    if not (added or removed or changed):
        print("  (unverändert)")
    return len(added), len(removed), len(changed)


# ---------------------------------------------------------------- Main
def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dry-run", action="store_true", help="zeigt nur den Diff, schreibt nichts")
    args = p.parse_args()

    print()
    print("🚗 Kennzeichen-Update – Wikipedia + Wikidata")
    print("=" * 50)

    print("▶ Wikidata…", end=" ", flush=True)
    try:
        wd = fetch_wikidata()
        print(f"✓ {len(wd)} Einträge")
    except Exception as e:
        print(f"✗ {e}")
        wd = {}

    print("▶ Wikipedia…", end=" ", flush=True)
    try:
        wp = fetch_wikipedia()
        print(f"✓ {len(wp)} Einträge")
    except Exception as e:
        print(f"✗ {e}")
        wp = {}

    if not wd and not wp:
        print("\n❌ Beide Quellen leer – Abbruch.")
        return 1

    merged, conflicts, only_wp, only_wd = merge(wp, wd)
    print(f"\n▶ Merge-Ergebnis: {len(merged)} Einträge")
    print(f"   • Wikipedia:       {len(wp)}")
    print(f"   • Wikidata:        {len(wd)}")
    print(f"   • nur in Wikipedia: {len(only_wp)} {only_wp[:10]}{' …' if len(only_wp)>10 else ''}")
    print(f"   • nur in Wikidata:  {len(only_wd)} {only_wd[:10]}{' …' if len(only_wd)>10 else ''}")
    if conflicts:
        print(f"   • Konflikte (WP gewinnt): {len(conflicts)}")
        for code, a, b in conflicts[:10]:
            print(f"     {code}: WP={a}  WD={b}")

    # Validation
    if len(merged) < MIN_ENTRIES:
        print(f"\n❌ Nur {len(merged)} Einträge (Minimum {MIN_ENTRIES}) – Abbruch.")
        return 2

    prev = load_previous()
    if prev and "count" in prev:
        threshold = prev["count"] * (1 - MAX_REGRESSION_RATIO)
        if len(merged) < threshold:
            print(f"\n❌ Regression: {prev['count']} → {len(merged)} "
                  f"(> {MAX_REGRESSION_RATIO*100:.0f}% Verlust) – Abbruch.")
            return 3

    print("\n▶ Änderungen gegenüber bisheriger kennzeichen.json:")
    n_add, n_rem, n_chg = print_diff(merged, prev)

    out = {
        "generated":  datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source":     "Wikipedia + Wikidata (merge)",
        "sources": {
            "wikipedia": "https://de.wikipedia.org/wiki/Liste_der_Kfz-Kennzeichen_in_Deutschland",
            "wikidata":  "https://query.wikidata.org/sparql (P395)",
        },
        "count": len(merged),
        "stats": {
            "added": n_add, "removed": n_rem, "changed": n_chg,
            "only_wikipedia": len(only_wp), "only_wikidata": len(only_wd),
            "conflicts_wp_won": len(conflicts),
        },
        "kennzeichen": merged,
    }

    if args.dry_run:
        print(f"\n🧪 Dry-run – {OUT_FILE} NICHT geschrieben.")
        return 0

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"\n✅ {OUT_FILE} geschrieben ({len(merged)} Einträge).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

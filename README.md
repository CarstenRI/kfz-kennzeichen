# KFZ-Kennzeichen-Finder

Eine kleine Web-App, die nach der Eingabe eines deutschen KFZ-Unterscheidungszeichens
(z. B. `B`, `HH`, `MYK`) die Herkunft ermittelt und Stadt/Landkreis, Bundesland,
Einwohnerzahl sowie die Lage auf einer interaktiven Karte anzeigt.

**🌐 Live-Demo:** https://carstenri.github.io/kfz-kennzeichen/

## Features

- Deutsche KFZ-Unterscheidungszeichen vollständig eingebaut (offline verfügbar)
- Autovervollständigung während der Eingabe – funktioniert mit Code (`B`) oder Stadtname (`Berlin`)
- Anzeige von Bundesland und aktueller Einwohnerzahl inkl. Erhebungsjahr
  (z. B. „106.921 (Stand 2022)") – live aus Wikidata
- Kurzbeschreibung und Vorschaubild aus Wikipedia
- Interaktive Leaflet-Karte mit OpenStreetMap-Kacheln
- **Gebietsgrenzen statt Pin:** Bei Städten und Landkreisen wird die reale
  Verwaltungsgrenze als Polygon auf der Karte eingezeichnet; Fallback auf
  Marker bei Einträgen ohne OSM-Relation
- Reset-Button (✕) im Eingabefeld – setzt Formular, Ergebnis und Karte zurück
- Tastatur-Shortcuts: Pfeiltasten & Enter in der Vorschlagsliste, Escape zum Zurücksetzen
- Verlauf der letzten Abfragen (lokal im Browser gespeichert)
- Ergebnis-Cache im `localStorage` – wiederholte Abfragen sind sofort da
- Als Progressive Web App (PWA) installierbar
- **Monatlich automatisch aktualisierte Kennzeichen-Datenbank** aus Wikipedia + Wikidata
  (GitHub Action, siehe unten)

## Datenaktualisierung

Die Kennzeichen-Zuordnung (Code → Stadt/Landkreis) wird automatisch aktuell gehalten.
Details:

- Eine separate `kennzeichen.json` hält alle Codes inkl. Generierungs-Zeitstempel.
- Die App lädt beim Start die aktuellste Version via `fetch`; die im HTML
  eingebettete Liste dient nur als Fallback.
- `update_kennzeichen.py` zieht die Daten aus zwei unabhängigen Quellen
  (Wikipedia-Liste + Wikidata-SPARQL auf `P395`) und merged sie. Bei Konflikten
  gewinnt Wikipedia (wird aktiver gepflegt). Vor dem Schreiben werden
  Mindest-Anzahl und Regressionen gegen die vorherige Datei geprüft, damit
  ein defekter Scrape die App nicht zerschießt.
- Die GitHub Action `.github/workflows/update-kennzeichen.yml` führt das Skript
  am 1. jeden Monats (04:15 UTC) aus und committet bei Änderungen automatisch.
  Manuell auslösbar über den „Run workflow"-Button auf der Actions-Seite.
- Im Footer der App steht der Stand der geladenen Datenbank.

Bei Bedarf kann das Skript auch lokal laufen:

```bash
python update_kennzeichen.py            # schreibt kennzeichen.json
python update_kennzeichen.py --dry-run  # zeigt nur das Diff
```

## Tech-Stack

Single-File-HTML mit Vanilla-JS – keine Build-Pipeline, kein Framework:

- [Leaflet 1.9.4](https://leafletjs.com) für die Karte
- OpenStreetMap-Kacheln für die Kartendaten

Live-Datenabruf via:

- [Wikipedia REST-API](https://de.wikipedia.org/api/rest_v1/) – Kurzbeschreibung,
  Thumbnail und Wikidata-Item-ID
- [Wikidata SPARQL-Endpoint](https://query.wikidata.org/sparql) – aktuelle
  Einwohnerzahl (`P1082`) mit Stichtag (`P585`) und OSM-Relation-ID (`P402`) in
  einer einzigen Abfrage
- [Nominatim](https://nominatim.openstreetmap.org) – GeoJSON-Polygon der
  Gebietsgrenze via `polygon_geojson=1` bzw. Fallback-Geocoding

## Deployment

Die App besteht aus folgenden Dateien im Repository-Root:

| Datei                              | Zweck                                      |
|------------------------------------|--------------------------------------------|
| `index.html`                       | Die App (HTML + CSS + JS, single-file)     |
| `kennzeichen.json`                 | Kennzeichen-Datenbank (monatlich gepflegt) |
| `manifest.json`                    | PWA-Manifest                               |
| `icon.svg`                         | App-Icon                                   |
| `update_kennzeichen.py`            | Update-Skript (nur stdlib, kein pip)       |
| `.github/workflows/update-kennzeichen.yml` | GitHub Action (monatlich)          |
| `README.md`                        | diese Datei                                |

Ausgeliefert wird alles über **GitHub Pages** (Branch `main`, Root).

## Lizenz / Datenquellen

- Kennzeichen-Zuordnung: [Wikipedia](https://de.wikipedia.org/wiki/Liste_der_Kfz-Kennzeichen_in_Deutschland) (CC BY-SA) + [Wikidata](https://www.wikidata.org) (CC0)
- Karte, Geokodierung & Gebietsgrenzen: © [OpenStreetMap](https://www.openstreetmap.org/copyright)-Mitwirkende
- Beschreibungen: [Wikipedia](https://de.wikipedia.org) unter [CC BY-SA](https://creativecommons.org/licenses/by-sa/3.0/deed.de)
- Einwohnerzahlen & Strukturdaten: [Wikidata](https://www.wikidata.org) unter [CC0](https://creativecommons.org/publicdomain/zero/1.0/deed.de)

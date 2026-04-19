# KFZ-Kennzeichen-Finder

Eine kleine Web-App, die nach der Eingabe eines deutschen KFZ-Unterscheidungszeichens
(z. B. `B`, `HH`, `MYK`) die Herkunft ermittelt und Stadt/Landkreis, Bundesland,
Einwohnerzahl sowie die Lage auf einer interaktiven Karte anzeigt.

**🌐 Live-Demo:** https://carstenri.github.io/kfz-kennzeichen/

## Features

- 643 deutsche KFZ-Unterscheidungszeichen eingebaut (offline verfügbar)
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

## Tech-Stack

Single-File-HTML mit Vanilla-JS – keine Abhängigkeiten außer einem CDN-Skript:

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

Die App besteht aus drei Dateien:

- `index.html` – die App
- `manifest.json` – PWA-Manifest
- `icon.svg` – App-Icon

Diese liegen im Repository-Root und werden über **GitHub Pages** (Branch `main`, Root) ausgeliefert.

## Lizenz / Datenquellen

- Kennzeichen-Zuordnung: aus öffentlich verfügbaren Daten (Kraftfahrt-Bundesamt)
- Karte & Geokodierung & Gebietsgrenzen: © [OpenStreetMap](https://www.openstreetmap.org/copyright)-Mitwirkende
- Beschreibungen: [Wikipedia](https://de.wikipedia.org) unter [CC BY-SA](https://creativecommons.org/licenses/by-sa/3.0/deed.de)
- Einwohnerzahlen & Strukturdaten: [Wikidata](https://www.wikidata.org) unter [CC0](https://creativecommons.org/publicdomain/zero/1.0/deed.de)

# KFZ-Kennzeichen-Finder

Eine kleine Web-App, die nach der Eingabe eines deutschen KFZ-Unterscheidungszeichens
(z. B. `B`, `HH`, `MYK`) die Herkunft ermittelt und Stadt/Landkreis, Bundesland,
Einwohnerzahl sowie die Lage auf einer interaktiven Karte anzeigt.

**🌐 Live-Demo:** https://carstenri.github.io/kfz-kennzeichen/

## Features

- 643 deutsche KFZ-Unterscheidungszeichen eingebaut (offline verfügbar)
- Autovervollständigung während der Eingabe – funktioniert mit Code (`B`) oder Stadtname (`Berlin`)
- Anzeige von Bundesland und Einwohnerzahl
- Kurze Beschreibung und Vorschaubild aus Wikipedia
- Interaktive Leaflet-Karte mit OpenStreetMap-Kacheln und Marker auf der Kommune
- Verlauf der letzten Abfragen (lokal im Browser gespeichert)
- Als Progressive Web App (PWA) installierbar

## Tech-Stack

Single-File-HTML mit Vanilla-JS – keine Abhängigkeiten außer zwei CDN-Skripten:

- [Leaflet](https://leafletjs.com) für die Karte
- OpenStreetMap-Kacheln für die Kartendaten

Live-Datenabruf via:

- [Nominatim](https://nominatim.openstreetmap.org) (OpenStreetMap) für Geokodierung
- [Wikipedia REST-API](https://de.wikipedia.org/api/rest_v1/) für Beschreibungen & Einwohnerzahlen

## Deployment

Die App besteht aus drei Dateien:

- `index.html` – die App
- `manifest.json` – PWA-Manifest
- `icon.svg` – App-Icon

Diese liegen im Repository-Root und werden über **GitHub Pages** (Branch `main`, Root) ausgeliefert.

## Lizenz / Datenquellen

- Kennzeichen-Zuordnung: aus öffentlich verfügbaren Daten (Kraftfahrt-Bundesamt)
- Karte & Geokodierung: © [OpenStreetMap](https://www.openstreetmap.org/copyright)-Mitwirkende
- Beschreibungen: [Wikipedia](https://de.wikipedia.org) unter [CC BY-SA](https://creativecommons.org/licenses/by-sa/3.0/deed.de)

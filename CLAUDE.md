# Cancionero Digital — Ministerio Nueva Alianza, Sector San Roberto

Cancionero católico carismático como **página web de un solo archivo HTML** que funciona
offline. Las canciones provienen del PDF original del ministerio y de LaCuerda.net.

## Estructura

- `datos/Cancionero_..._2026.pdf` — PDF original (fuente de la extracción inicial).
- `datos/songs.json` — **Fuente de verdad**: las 103 canciones extraídas y estructuradas.
- `scripts/extract.py` — Extrae las canciones del PDF a `songs.json` (solo se corre si cambia el PDF).
- `scripts/build_html.py` — Genera el sitio: incrusta `songs.json` en la plantilla HTML.
- `salida/Cancionero_Nueva_Alianza_San_Roberto.html` — El cancionero final (un solo archivo, offline).

## Comandos

```bash
pip install pdfplumber          # solo para extract.py
python3 scripts/extract.py      # PDF -> datos/songs.json (rara vez necesario)
python3 scripts/build_html.py   # datos/songs.json -> salida/...html (siempre tras editar canciones)
```

Ejecutar siempre desde la raíz del proyecto (rutas relativas).

## Formato de una canción en `songs.json`

```json
{
  "title": "Bueno es alabar",
  "author": "Fernando Soto",          // "" si no hay
  "section": "Alabanza",              // Alabanza | Adoración | Exaltación | Espíritu Santo | María | Desagravio | Perdón
  "page": 8,                          // página del PDF original (0 o null para canciones nuevas)
  "lines": [
    {"k": "c", "t": "G             C         D"},   // k=c: línea de ACORDES
    {"k": "l", "t": "Bueno es alabar ¡Al Señor!"},  // k=l: línea de LETRA
    {"k": "b", "t": ""}                              // k=b: línea en blanco (separa estrofas)
  ]
}
```

Los acordes se alinean sobre la letra con espacios (fuente monoespaciada en el HTML).

## Para agregar una canción de LaCuerda.net

1. Obtener letra y acordes de la URL (formato: acordes arriba de la letra, monoespaciado).
2. Convertir a objetos `{"k","t"}` línea por línea; mantener la alineación con espacios.
3. Agregar el objeto al final de `datos/songs.json` con su `section` correcta.
4. Correr `python3 scripts/build_html.py`.
5. Actualizar el contador de canciones del footer en `build_html.py` si cambia el total.

## Reglas

- El HTML final no debe cargar nada externo (sin CDNs ni webfonts): debe funcionar 100% offline.
- La transposición de acordes vive en el JS de la plantilla (`build_html.py`) y soporta
  notación americana (Am, F#) y latina (Rem, Fa#).
- UI en español. Colores de marca: teal #0F4761 (títulos), azul #215E99 (acordes).

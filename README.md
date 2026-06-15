# Cancionero · Ministerio Nueva Alianza · Sector San Roberto

Cancionero católico carismático como sitio web. Funciona sin internet una vez descargado.

**Sitio:** https://<usuario>.github.io/ministerio-de-musica-sr/

## Cómo funciona

- `index.html` — el sitio (lector + descarga). Carga las canciones desde `datos/songs.json`.
- `datos/songs.json` — **fuente de verdad**: las canciones.
- `scripts/` — herramientas archivadas (extracción del PDF). No se usan en el día a día.
- `docs/superpowers/` — specs y planes de implementación.

## Desarrollo

```bash
npm test                      # pruebas de lógica pura (Node, sin dependencias)
python3 -m http.server 8765   # servir en local: http://localhost:8765/
```

## Editar canciones

Por ahora se editan en `datos/songs.json` y se sube el cambio a GitHub
(el sitio se actualiza solo en ~1 minuto). El editor en el navegador y el
importador por URL llegan en planes posteriores.

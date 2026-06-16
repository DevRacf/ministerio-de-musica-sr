# Mixes (popurrís / set lists) — Diseño

**Fecha:** 2026-06-16
**Proyecto:** Cancionero · Ministerio Nueva Alianza · Sector San Roberto

## Objetivo

Permitir armar "Mixes": listas ordenadas de canciones existentes para que el músico
enlace una canción con otra sin buscarla (ej: 1. Pues tú glorioso, 2. Hay gran voz,
3. Grande es el Señor). Compartidos para todos vía GitHub.

## Decisiones (del brainstorming)

- **Compartidos:** se publican a GitHub, igual que las canciones (reusa el token del editor).
- **Creación:** en el modo edición del navegador.
- **Navegación en vivo:** botones Anterior / Siguiente dentro de la canción.
- **Referencia estable:** los mixes referencian canciones por **título** (no por índice,
  que se corre). Título inexistente → se marca "no encontrada" y se salta al navegar.

## Datos

- Archivo nuevo `datos/mixes.json` = `[{ "name": "...", "songs": ["Título 1", "Título 2", ...] }]`.
  Estado inicial: `[]`.
- Se carga con `fetch('datos/mixes.json')` al abrir, con respaldo incrustado
  `EMBEDDED_MIXES` para la copia offline (slot `==EMBED-MIXES==`).
- La descarga offline incrusta canciones Y mixes.

## Lector

- Chip nuevo **"♫ Mixes"** al inicio de la fila de secciones.
- Al seleccionarlo, el índice muestra la **lista de mixes**: cada uno como tarjeta con el
  nombre y, debajo, los títulos en orden. Si no hay mixes: estado vacío.
- Tocar un mix abre su **primera canción** con contexto de mix.
- **Dentro de un mix** (estado `enMix = {mixIdx, pos}`):
  - La barra superior de la canción muestra "← Mix" (vuelve a la lista de mixes) y, al
    centro, "pos/total · nombre".
  - Al final de la canción, barra con **← Anterior** / **Siguiente →**. "Anterior" se
    desactiva en la primera; "Siguiente" en la última.
  - Resolver títulos→índices por coincidencia de título; los que no existan se saltan.

## Editor (modo edición, con token)

- En la vista de Mixes: botón **"➕ Nuevo mix"**; cada mix tiene ✎ / 🗑.
- Editor de mix (overlay): campo **nombre**, **buscador** que filtra canciones por título
  y permite agregarlas, y la **lista del mix** con cada canción y ↑ / ↓ / ✕ (reordenar/quitar).
- **Guardar** publica `datos/mixes.json` a GitHub (commit message "Mix: <nombre>").
- Borrar mix: confirma y publica.

## GitHub

- Generalizar el cliente para escribir/leer cualquier ruta (`datos/songs.json` o
  `datos/mixes.json`), con su propio `sha`. `publicarMixes(msg)` lee el sha y hace PUT.
- Mismo manejo de errores que el editor de canciones (token / conflicto / sin internet,
  con reversión del estado en memoria).

## Funciones puras (testeables)

- `resolverMix(mix, songs)` → `[{pos, title, idx|null}]` (resuelve títulos a índices;
  `idx=null` si no existe).
- `moverEnLista(arr, i, dir)` → nueva lista con el elemento `i` movido (-1 / +1), sin mutar.

## Criterios de éxito

1. Con token, el dueño crea un mix (nombre + canciones ordenadas) y se publica para todos.
2. Tocar un mix abre la primera canción; Anterior/Siguiente recorren el set en orden.
3. Una canción borrada del cancionero se marca "no encontrada" en el mix y se salta.
4. La copia descargada muestra los mixes y funciona sin internet.
5. El lector sigue 100% offline (mixes.json se incrusta; sin recursos externos salvo
   api.github.com en modo edición).

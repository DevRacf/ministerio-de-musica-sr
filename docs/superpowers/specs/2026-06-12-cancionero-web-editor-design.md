# Cancionero Digital Web — Editor en navegador + Importador por agente

**Fecha:** 2026-06-12
**Proyecto:** Ministerio de Música Nueva Alianza, Sector San Roberto

## Objetivo

Convertir el cancionero actual (un solo HTML generado por build) en un sitio web
publicado en GitHub Pages que:

1. Cualquiera puede **ver** (lector con búsqueda, transposición, etc.).
2. Cualquiera puede **descargar** como archivo HTML único para usar sin internet.
3. Solo el dueño puede **editar** (agregar, editar, borrar canciones) desde el navegador,
   y los cambios se publican automáticamente para todos.
4. El dueño puede **importar canciones desde una URL** (LaCuerda.net, Cifra Club, etc.)
   con ayuda de un agente en Claude Code que baja, convierte y sube la canción al repo.

Además, dos requisitos transversales:

- **Fidelidad de alineación al PDF:** cada acorde debe caer sobre la sílaba correcta,
  como en el cancionero impreso (ver "Fidelidad al PDF").
- **Rediseño de UI:** un pulido visual del único `index.html` (ver "Rediseño de UI").

## Lo que NO cambia

El lector hereda casi toda la funcionalidad y el estilo del HTML actual:
búsqueda por título/letra/autor, chips de sección con colores,
transposición de acordes (notación americana y latina), tamaño de letra, modo oscuro,
funcionamiento offline una vez cargado, UI en español, colores de marca
(teal `#0F4761`, azul `#215E99`).

**Cambio respecto al HTML actual:** se elimina la función de favoritas (estrella en
las filas, chip "★ Favoritas", y su almacenamiento en `localStorage`).

## Arquitectura

### Repositorio (público, en GitHub)

```
ministerio-de-musica-sr/   # nombre del repo (URL: github.io/ministerio-de-musica-sr/)
  index.html              # La app completa: lector + modo edición
  datos/
    songs.json            # FUENTE DE VERDAD: array de canciones
  scripts/                # Archivados (ya no en el flujo normal)
    extract.py            # Solo si cambia el PDF original
    build_html.py         # Ya no se usa para publicar; queda como referencia
  datos/Cancionero_..._2026.pdf   # PDF original (referencia)
  docs/                   # Specs y planes
```

- GitHub Pages sirve la raíz del repo en `https://<usuario>.github.io/ministerio-de-musica-sr/`.
  El título visible dentro del sitio sí puede decir "Ministerio de Música SR" (con espacios y acentos).
- **Se elimina el paso de build.** `index.html` carga `datos/songs.json` con `fetch()`
  al abrir, en vez de tener los datos incrustados por `build_html.py`.
- Los scripts de Python se conservan archivados (extracción del PDF es algo raro).

### `index.html` — estructura interna

Un solo archivo, sin dependencias externas (sin CDNs ni webfonts), igual que hoy.
Internamente tiene tres capas:

1. **Datos:** al cargar, `fetch('datos/songs.json')`. Si falla (p. ej. abierto como
   archivo local `file://`), usa una copia incrustada de respaldo para seguir funcionando
   offline. (Ver "Descarga offline".)
2. **Lector:** el código actual del cancionero, prácticamente sin cambios.
3. **Editor:** capa nueva, oculta por defecto, que se activa con el token.

## El formato de datos (sin cambios)

Cada canción en `songs.json`:

```json
{
  "title": "Bueno es alabar",
  "author": "Fernando Soto",
  "section": "Alabanza",
  "page": 8,
  "lines": [
    {"k": "c", "t": "G             C         D"},
    {"k": "l", "t": "Bueno es alabar ¡Al Señor!"},
    {"k": "b", "t": ""}
  ]
}
```

`k`: `c` = acordes, `l` = letra, `b` = línea en blanco (separa estrofas).
Secciones válidas: Alabanza, Adoración, Exaltación, Espíritu Santo, María, Desagravio, Perdón.
El `id` se asigna en runtime por índice (como hoy), no se guarda en el JSON. Se usa solo
para la navegación por hash (`#c<id>`); al quitar favoritas ya no hay estado persistente
atado al id, así que borrar o reordenar canciones no rompe nada guardado.

## Modo edición (solo el dueño)

### Activación y autenticación

- Un botón discreto en el footer ("✎ Editar") activa el modo edición.
- La primera vez pide un **GitHub Personal Access Token** (fine-grained, con permiso
  *Contents: read/write* solo sobre el repo del cancionero). Se guarda en `localStorage`.
- El token nunca se sube a ningún lado; vive solo en el navegador del dueño.
- Como el repo es público, cualquiera ve el botón, pero sin token válido no puede guardar.

### Acciones

Con el modo activo:

- Cada canción en el índice y en la vista muestra **Editar** y **Borrar**.
- Aparece **➕ Agregar canción**.
- **Formulario de canción:**
  - Título (texto)
  - Autor (texto, opcional)
  - Sección (desplegable con las 7 secciones)
  - Cuerpo: un `<textarea>` monoespaciado donde se escribe/pega acordes y letra
    tal cual (acordes arriba, letra abajo).
  - **Detección automática de acordes:** al teclear, cada línea se clasifica como
    acorde (`c`), letra (`l`) o blanco (`b`) usando la misma regex `RE_CHORD` / `RE_SEQ`
    que ya tiene el cancionero para la transposición. El usuario puede forzar el tipo
    de una línea si la detección se equivoca.
  - **Vista previa** coloreada en vivo (acordes en azul) antes de guardar.

### Guardado a GitHub

Al **Guardar**:

1. Lee el `songs.json` actual vía GitHub Contents API (para tener el `sha` vigente).
2. Aplica el cambio (agregar/editar/borrar) sobre el array.
3. Hace `PUT` del nuevo `songs.json` con un mensaje de commit descriptivo
   (p. ej. "Agregar: Bueno es alabar").
4. Muestra "Publicado — visible para todos en ~1 minuto" (GitHub Pages tarda en
   reconstruir).

### Manejo de errores del editor

- **Token inválido/vencido:** mensaje claro con cómo crear uno nuevo; no se pierde
  lo escrito en el formulario.
- **Conflicto (el `sha` cambió):** la app vuelve a leer `songs.json`, avisa
  "alguien más editó; reintenta" y conserva el borrador del formulario.
- **Sin internet al guardar:** el borrador queda en `localStorage` para reintentar.

## Importar desde una URL (agente en Claude Code)

No vive en el navegador. Es un flujo reutilizable en esta app (Claude Code):

1. El dueño da una o varias URLs (LaCuerda.net, Cifra Club, u otro sitio).
2. El agente baja cada página (WebFetch), extrae **título, autor, sección sugerida,
   acordes y letra**, y los convierte al formato `{"k","t"}` con los acordes alineados
   sobre la letra en fuente monoespaciada.
3. El agente **muestra la vista previa para aprobación**. Nada se publica sin el visto
   bueno del dueño.
4. Al aprobar, el agente agrega la(s) canción(es) a `datos/songs.json`, hace commit y
   push. En ~1 minuto está publicado.

Ventajas frente a importar en el navegador: lee cualquier sitio (sin proxy CORS ni
traductores frágiles por sitio), entiende formatos raros, corrige alineación y errores
de la fuente sobre la marcha.

Se documentará como un comando/skill reutilizable para que el flujo sea siempre igual.

## Descarga offline (para todos)

- Botón **"Descargar"** visible para cualquier visitante.
- Genera al momento un HTML único con las canciones al día: toma el `index.html` y
  le incrusta el `songs.json` actual como respaldo embebido, de modo que el archivo
  descargado funcione abierto desde `file://` sin internet (igual que el HTML actual).
- En la copia descargada el **modo edición queda desactivado** (sin botón de editar,
  ya que no hay forma de publicar desde un archivo local).

## Fidelidad al PDF (alineación de acordes)

El PDF impreso coloca la letra en fuente **proporcional** y los acordes en posición
absoluta encima. El cancionero web usa fuente **monoespaciada** y alinea los acordes
contando espacios. Decisión tomada: **se mantiene el estilo monoespaciado** (es el
estándar de hojas de acordes, garantiza que el acorde caiga siempre sobre un carácter
exacto y sobrevive a la transposición y al cambio de tamaño de letra). Lo que se exige
es **corrección de alineación**, no réplica visual del PDF.

**Criterio:** para cada canción, cada acorde debe quedar sobre la misma sílaba que en
el PDF.

**Método de verificación y corrección:**

1. Renderizar cada página del PDF a imagen (`pdftoppm`, poppler ya instalado).
2. Comparar contra la canción correspondiente en `songs.json` (la extracción posicional
   con `pdfplumber` da la posición exacta de cada acorde y sílaba como referencia).
3. Corregir en `songs.json` las líneas donde el acorde no caiga sobre la sílaba correcta.
4. Auditoría inicial: ~69 de 2522 líneas de acordes son más anchas que su letra; algunas
   son legítimas (intros, acordes finales, secciones instrumentales) y otras son
   desalineaciones reales. Se revisan una por una.

**Importante:** `songs.json` ya es la fuente de verdad con correcciones manuales; NO se
re-extrae el PDF en masa (rompería el trabajo ya hecho). La corrección es puntual,
canción por canción.

## Rediseño de UI

Hay un solo `index.html` (el que se publica en la web es el mismo que se descarga para
uso offline); rediseñarlo mejora ambas versiones a la vez.

- **Alcance:** pulido visual que conserva la identidad de marca (teal `#0F4761`,
  azul `#215E99`) y la hoja de acordes monoespaciada. Se mejoran tipografía, espaciado,
  contraste, jerarquía visual, botones, chips de sección y la vista de canción.
- **Se mantiene:** modo claro/oscuro, responsive (móvil primero), accesibilidad
  (focus visible, contraste, `prefers-reduced-motion`), y el funcionamiento offline
  sin recursos externos.
- **Restricción dura:** sin CDNs ni webfonts; todo embebido, el sitio funciona 100% offline.
- Se ejecutará durante la implementación con la skill `frontend-design`. Si tras verlo
  se quiere algo más atrevido (portada/navegación reimaginadas), se sube de nivel
  en ese momento.

## Riesgos y decisiones abiertas

- **Token en navegador:** aceptable para un solo editor. El token es fine-grained y
  acotado a un repo; si se filtra, solo afecta a este cancionero público.
- **Latencia de publicación:** GitHub Pages tarda ~1 min. Se comunica claramente en la UI.

## Criterios de éxito

1. El sitio carga en GitHub Pages y se ve igual o mejor que el HTML actual.
2. Un visitante sin token puede buscar, transponer y descargar offline.
3. El dueño, con token, agrega/edita/borra una canción desde el navegador y el cambio
   aparece publicado para todos.
4. El agente importa una canción de LaCuerda.net o Cifra Club desde su URL, con vista
   previa y aprobación, y la deja publicada.
5. El archivo descargado funciona abierto sin internet.
6. En una muestra de canciones revisadas contra el PDF, cada acorde cae sobre la sílaba
   correcta (fidelidad de alineación).
7. El UI rediseñado conserva la identidad de marca, funciona en móvil y de noche, y
   sigue cargando sin recursos externos.

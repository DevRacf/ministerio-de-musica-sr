# Plan A — Sitio base en GitHub Pages — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publicar el cancionero como sitio en GitHub Pages que carga las canciones desde `datos/songs.json` por `fetch`, sin paso de build, sin favoritas, con un botón de descarga que genera una copia offline autónoma.

**Architecture:** Un único `index.html` autocontenido (sin CDNs ni webfonts) sirve de lector. En el servidor carga `datos/songs.json` por `fetch`; una copia descargada lleva las canciones incrustadas en una constante `EMBEDDED` y omite el `fetch`, por lo que funciona desde `file://`. La lógica pura (transposición, inyección de datos) se aísla en una región marcada del script para poder probarla en Node sin DOM.

**Tech Stack:** HTML + CSS + JavaScript vanilla (un archivo). Pruebas con el runner integrado de Node (`node:test` + `node:vm`, sin dependencias). Deploy en GitHub Pages. Node v24 ya instalado.

**Estrategia de pruebas:** Este es un único HTML offline sin framework. Las funciones *puras* (sin DOM ni red) viven entre los marcadores `/* ==PURE-START== */` y `/* ==PURE-END== */` dentro del `<script>` de `index.html`. Un helper de test lee `index.html`, extrae esa región y la ejecuta en un contexto `vm` para probar cada función de forma aislada. El comportamiento que toca DOM/red (render del índice, botón de descarga disparando la bajada del archivo) se verifica manualmente en el navegador al final.

---

### Task 1: Inicializar repositorio y estructura del proyecto

**Files:**
- Create: `.gitignore`
- Create: `index.html` (copia del lector actual generado por el build)
- Modify: estructura (mover scripts a `scripts/`, ya están ahí)
- Conserva: `datos/songs.json`, `datos/Cancionero_...2026.pdf`, `scripts/extract.py`, `scripts/build_html.py`, `docs/`

- [ ] **Step 1: Generar el `index.html` de partida desde el build actual**

El `index.html` inicial es exactamente el HTML que produce el build actual (lector que ya funciona). Generarlo y colocarlo en la raíz:

Run:
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
python3 scripts/build_html.py
cp salida/Cancionero_Nueva_Alianza_San_Roberto.html index.html
```
Expected: `OK -> salida/...html (NNN KB)` y se crea `index.html` en la raíz.

- [ ] **Step 2: Crear `.gitignore`**

Create `.gitignore`:
```gitignore
.DS_Store
**/.DS_Store
salida/
node_modules/
```

> `salida/` se ignora porque el nuevo flujo no usa el HTML generado por build; `index.html` en la raíz es el sitio. `scripts/build_html.py` queda como referencia archivada.

- [ ] **Step 3: Inicializar git y primer commit**

Run:
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
git init
git add .gitignore index.html datos/songs.json datos/*.pdf scripts/ docs/ CLAUDE.md
git commit -m "chore: estructura inicial del repo del cancionero

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```
Expected: commit creado; `git status` limpio salvo `salida/` y `.DS_Store` ignorados.

- [ ] **Step 4: Verificar estructura**

Run: `git ls-files | sort`
Expected: incluye `index.html`, `datos/songs.json`, `datos/Cancionero_...2026.pdf`, `scripts/extract.py`, `scripts/build_html.py`, `docs/superpowers/specs/2026-06-12-cancionero-web-editor-design.md`, `.gitignore`, `CLAUDE.md`. No incluye nada bajo `salida/`.

---

### Task 2: Harness de pruebas para lógica pura + bloquear la transposición

Antes de refactorizar, aislamos la lógica pura en una región marcada y la cubrimos con tests, para no romperla en las tareas siguientes.

**Files:**
- Modify: `index.html` (envolver la lógica pura con marcadores)
- Create: `tests/helper.mjs`
- Create: `tests/transpose.test.mjs`
- Create: `package.json`

- [ ] **Step 1: Marcar la región de lógica pura en `index.html`**

En el `<script>` de `index.html`, las constantes y funciones de transposición ya existen (`SHARP`, `BASE`, `LAT`, `LAT_INV`, `ROOT`, `QUAL`, `RE_CHORD`, `RE_SEQ`, `RE_ROOT`, `shift`, `transponerLinea`). Envolverlas en marcadores. Localiza este bloque:

```javascript
/* ---------- transposición ---------- */
const SHARP=['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
```
y el final del bloque:
```javascript
function transponerLinea(linea, n){
  if (!n) return linea;
  return linea.split(/(\s+)/).map(tok=>{
    if (!tok.trim()) return tok;
    if (RE_CHORD.test(tok) || RE_SEQ.test(tok))
      return tok.replace(RE_ROOT, (m, r, a) => shift(r, a||'', n));
    return tok;
  }).join('');
}
```

Insertar `/* ==PURE-START== */` justo después del comentario `/* ---------- transposición ---------- */` (antes de `const SHARP`), y `/* ==PURE-END== */` justo después del cierre `}` de `transponerLinea`. El bloque entre marcadores NO debe referenciar `document`, `window`, `localStorage`, ni `fetch`.

- [ ] **Step 2: Crear `package.json`**

Create `package.json`:
```json
{
  "name": "cancionero-nueva-alianza",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "node --test tests/"
  }
}
```

> `package.json` no añade dependencias; solo declara el script de pruebas y `type: module` para usar `import`. No afecta al sitio (GitHub Pages sirve `index.html` directo).

- [ ] **Step 3: Crear el helper que extrae y evalúa la región pura**

Create `tests/helper.mjs`:
```javascript
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const __dirname = dirname(fileURLToPath(import.meta.url));
const HTML = join(__dirname, '..', 'index.html');

/**
 * Lee index.html, extrae el bloque entre /* ==PURE-START== *\/ y /* ==PURE-END== *\/
 * y lo ejecuta en un contexto aislado. Devuelve las funciones/const expuestas.
 */
export function cargarPuro(extra = '') {
  const src = readFileSync(HTML, 'utf8');
  const m = src.match(/\/\* ==PURE-START== \*\/([\s\S]*?)\/\* ==PURE-END== \*\//);
  if (!m) throw new Error('No se encontraron los marcadores ==PURE-START== / ==PURE-END== en index.html');
  const ctx = {};
  vm.createContext(ctx);
  vm.runInContext(m[1] + '\n' + extra, ctx);
  return ctx;
}

export function leerHtml() {
  return readFileSync(HTML, 'utf8');
}
```

> El `extra` permite exportar al contexto símbolos declarados con `const` (que no se vuelven propiedades del contexto). Cada test pasa algo como `'globalThis.transponerLinea = transponerLinea;'`.

- [ ] **Step 4: Escribir las pruebas de transposición**

Create `tests/transpose.test.mjs`:
```javascript
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cargarPuro } from './helper.mjs';

const ctx = cargarPuro(`
  globalThis.transponerLinea = transponerLinea;
`);
const { transponerLinea } = ctx;

test('sube un semitono en notación americana', () => {
  assert.equal(transponerLinea('C       G       Am', 1), 'C#      G#      A#m');
});

test('baja un semitono', () => {
  assert.equal(transponerLinea('D   A', -2), 'C   G');
});

test('transpone notación latina conservando el sistema', () => {
  assert.equal(transponerLinea('Do      Sol', 2), 'Re      La');
});

test('no toca las líneas de letra (texto que no son acordes)', () => {
  const letra = 'Cuando el Señor hiciere volver la cautividad';
  assert.equal(transponerLinea(letra, 3), letra);
});

test('n=0 devuelve la línea intacta', () => {
  assert.equal(transponerLinea('F#m7  B7', 0), 'F#m7  B7');
});

test('preserva el espaciado (la alineación no se corre con acordes de igual longitud)', () => {
  const out = transponerLinea('C   D   E', 1);
  assert.equal(out, 'C#  D#  F');
});
```

- [ ] **Step 5: Correr las pruebas y verificar que pasan**

Run: `cd "/Users/andre/Documents/Claude/Projects/cancionero 2" && npm test`
Expected: `# pass 6` y `# fail 0`.

> Si alguna falla por el espaciado esperado, ajusta el *string esperado* del test al output real de la lógica vigente (estamos bloqueando el comportamiento actual, no cambiándolo). Documenta el output real en el assert.

- [ ] **Step 6: Commit**

```bash
git add package.json tests/ index.html
git commit -m "test: harness de lógica pura y pruebas de transposición

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Cargar canciones por `fetch` con respaldo incrustado

Quitar la incrustación por build y cargar `datos/songs.json` en runtime, con un respaldo `EMBEDDED` para `file://`.

**Files:**
- Modify: `index.html` (constante de datos, slot de incrustación, arranque async)
- Create: `tests/carga.test.mjs`

- [ ] **Step 1: Reemplazar la constante de datos por el slot de incrustación**

En `index.html`, localiza al inicio del `<script>`:
```javascript
const SONGS = __DATA__;
```
Y la línea de build en `scripts/build_html.py` ya no actúa sobre la raíz. Reemplazar esa línea en `index.html` por:
```javascript
const EMBEDDED = null; /* ==EMBED-SLOT== */
let SONGS = [];
```

> El literal exacto `const EMBEDDED = null; /* ==EMBED-SLOT== */` es importante: el botón de descarga (Task 5) hace un reemplazo de string exacto sobre él. `SONGS` pasa de `const` a `let` porque se asigna tras el `fetch`.

- [ ] **Step 2: Añadir la función de carga dentro de la región pura**

Dentro de la región `==PURE-START==`/`==PURE-END==` de `index.html`, al final (antes de `/* ==PURE-END== */`), añadir:
```javascript
/* Devuelve el src de index.html con las canciones incrustadas en el slot EMBEDDED. */
function inyectarDatos(src, songs){
  const slot = 'const EMBEDDED = null; /* ==EMBED-SLOT== */';
  const relleno = 'const EMBEDDED = ' + JSON.stringify(songs) + '; /* ==EMBED-SLOT== */';
  if (!src.includes(slot)) throw new Error('No se encontró el slot EMBEDDED');
  return src.replace(slot, relleno);
}
```

> `inyectarDatos` es pura (string -> string), por eso vive en la región testeable. La usa la descarga en Task 5.

- [ ] **Step 3: Reemplazar el arranque sincrónico por carga async**

Al final del `<script>` de `index.html` está el arranque actual:
```javascript
render();
const m=location.hash.match(/^#c(\d+)$/);
if (m && SONGS[+m[1]]) abrir(+m[1]);
```
Reemplazarlo por:
```javascript
async function cargarSongs(){
  if (Array.isArray(EMBEDDED)) return EMBEDDED;
  try{
    const r = await fetch('datos/songs.json', {cache:'no-store'});
    if (!r.ok) throw new Error('HTTP '+r.status);
    return await r.json();
  }catch(e){
    return null;
  }
}
async function iniciar(){
  const data = await cargarSongs();
  if (!data){
    document.getElementById('lista').innerHTML =
      '<div class="vacio">No se pudieron cargar las canciones.<br>' +
      'Si abriste este archivo desde tu computadora, descárgalo de nuevo desde el sitio web ' +
      'usando el botón <b>Descargar</b>.</div>';
    return;
  }
  SONGS = data;
  SONGS.forEach((s, i) => { s.id = i; });
  SONGS.forEach(s => { s._busq = norm(s.title+' '+(s.author||'')+' '+s.lines.map(l=>l.t).join(' ')); });
  render();
  const m = location.hash.match(/^#c(\d+)$/);
  if (m && SONGS[+m[1]]) abrir(+m[1]);
}
iniciar();
```

- [ ] **Step 4: Quitar la asignación de `id` y `_busq` que se hacía en build/carga sincrónica**

En `index.html`, localiza la línea que precalcula la búsqueda (justo después de las utilidades):
```javascript
SONGS.forEach(s => { s._busq = norm(s.title+' '+(s.author||'')+' '+s.lines.map(l=>l.t).join(' ')); });
```
Borrarla (ahora se hace dentro de `iniciar()` tras cargar los datos). La asignación de `id` antes la hacía `build_html.py` en Python; ahora la hace `iniciar()`.

- [ ] **Step 5: Escribir pruebas de `inyectarDatos`**

Create `tests/carga.test.mjs`:
```javascript
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cargarPuro } from './helper.mjs';

const ctx = cargarPuro(`globalThis.inyectarDatos = inyectarDatos;`);
const { inyectarDatos } = ctx;

const SRC = 'antes\nconst EMBEDDED = null; /* ==EMBED-SLOT== */\ndespués';

test('incrusta el array en el slot EMBEDDED', () => {
  const out = inyectarDatos(SRC, [{title:'X'}]);
  assert.match(out, /const EMBEDDED = \[\{"title":"X"\}\]; \/\* ==EMBED-SLOT== \*\//);
});

test('conserva el resto del documento', () => {
  const out = inyectarDatos(SRC, []);
  assert.ok(out.startsWith('antes\n'));
  assert.ok(out.endsWith('\ndespués'));
});

test('lanza si no encuentra el slot', () => {
  assert.throws(() => inyectarDatos('sin slot', []), /slot EMBEDDED/);
});

test('el resultado vuelve a contener el slot (descarga idempotente del marcador)', () => {
  const out = inyectarDatos(SRC, [1,2,3]);
  assert.ok(out.includes('/* ==EMBED-SLOT== */'));
});
```

- [ ] **Step 6: Correr pruebas**

Run: `cd "/Users/andre/Documents/Claude/Projects/cancionero 2" && npm test`
Expected: todas las pruebas pasan (`# fail 0`), incluyendo las 4 nuevas de carga.

- [ ] **Step 7: Verificar el sitio en local con servidor**

Run (en segundo plano):
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2" && python3 -m http.server 8765
```
Luego abrir `http://localhost:8765/` y confirmar manualmente: el índice lista las 103 canciones por sección, la búsqueda filtra, y abrir una canción muestra acordes y letra. Detener el servidor al terminar.
Expected: el lector funciona igual que antes, ahora cargando desde `datos/songs.json`.

- [ ] **Step 8: Verificar el fallo controlado en `file://`**

Abrir `index.html` directamente con doble clic (protocolo `file://`).
Expected: aparece el mensaje "No se pudieron cargar las canciones... usa el botón Descargar" (porque `fetch` de `songs.json` falla en `file://` y no hay `EMBEDDED`). Esto confirma que el respaldo es necesario y que el mensaje guía al usuario.

- [ ] **Step 9: Commit**

```bash
git add index.html tests/carga.test.mjs
git commit -m "feat: cargar canciones por fetch con respaldo incrustado para offline

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Quitar la función de favoritas

Eliminar estrella, chip "★ Favoritas" y su almacenamiento, según el spec.

**Files:**
- Modify: `index.html` (CSS, HTML del botón, JS de favoritas, chips, filas)

- [ ] **Step 1: Quitar el estado y almacenamiento de favoritas (JS)**

En `index.html`, localiza y borra:
```javascript
let favoritas = new Set(store.get('favs', []));
```
(La variable `store` se mantiene: la usan tema y tamaño de letra.)

- [ ] **Step 2: Quitar el chip "★ Favoritas" del menú de secciones**

Localiza:
```javascript
const chipDefs=['Todas','★ Favoritas',...SECCIONES];
```
Reemplazar por:
```javascript
const chipDefs=['Todas',...SECCIONES];
```

- [ ] **Step 3: Quitar el filtro por favoritas en `render()`**

En `render()`, localiza y borra esta línea dentro del `.filter`:
```javascript
    if (filtroSec==='★ Favoritas' && !favoritas.has(s.id)) return false;
```

- [ ] **Step 4: Quitar la estrella de las filas del índice**

En la función `fila(s)`, localiza:
```javascript
    ${favoritas.has(s.id)?'<span class="fav">★</span>':''}
```
Borrar esa línea.

- [ ] **Step 5: Quitar el botón de favorita de la vista de canción (HTML)**

En el marcado de la vista de canción, localiza y borra:
```html
    <button id="btnFav" aria-label="Marcar como favorita">★</button>
```

- [ ] **Step 6: Quitar el manejo de `btnFav` y los toggles relacionados (JS)**

Borrar este bloque completo:
```javascript
document.getElementById('btnFav').onclick=()=>{
  if (favoritas.has(actual)) favoritas.delete(actual); else favoritas.add(actual);
  store.set('favs',[...favoritas]);
  document.getElementById('btnFav').classList.toggle('on', favoritas.has(actual));
  render();
};
```
En la función `abrir(id)`, borrar también:
```javascript
  document.getElementById('btnFav').classList.toggle('on', favoritas.has(id));
```

- [ ] **Step 7: Quitar el CSS de favoritas**

En el `<style>`, borrar las reglas que solo aplican a favoritas:
```css
.fila .fav{color:var(--dorado);font-size:15px;flex:none}
```
y
```css
#btnFav{margin-left:auto;font-size:20px;color:var(--suave)}
#btnFav.on{color:var(--dorado)}
```

> Nota: `#btnFav` tenía `margin-left:auto`, que empujaba los elementos. Tras quitarlo, el botón "← Índice" queda solo en `.c-top`; es el comportamiento deseado (la barra superior de la canción solo necesita Volver). Verificar visualmente en el Step 9.

- [ ] **Step 8: Correr pruebas (no debe romper la lógica pura)**

Run: `cd "/Users/andre/Documents/Claude/Projects/cancionero 2" && npm test`
Expected: `# fail 0` (las pruebas de transposición y carga siguen pasando; favoritas no era lógica pura).

- [ ] **Step 9: Verificar en navegador**

Servir en local (`python3 -m http.server 8765`) y confirmar: no hay chip de favoritas, no hay estrellas en las filas, la vista de canción solo muestra "← Índice" arriba, y abrir/cerrar/transponer/cambiar tema sigue funcionando. Detener el servidor.

- [ ] **Step 10: Commit**

```bash
git add index.html
git commit -m "feat: quitar la función de favoritas

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Botón de descarga offline

Generar al vuelo una copia autónoma del sitio con las canciones incrustadas.

**Files:**
- Modify: `index.html` (botón en el footer, CSS, función de descarga)

- [ ] **Step 1: Añadir el botón "Descargar" en el footer (HTML)**

En `index.html`, localiza el footer:
```html
  <footer>
    Ministerio de Música <b>Nueva Alianza</b> · Sector San Roberto Abad<br>
    103 canciones · Funciona sin internet: guarda este archivo y ábrelo cuando quieras.
  </footer>
```
Reemplazar por:
```html
  <footer>
    Ministerio de Música <b>Nueva Alianza</b> · Sector San Roberto Abad<br>
    Funciona sin internet una vez descargado.<br>
    <button id="btnDescargar" class="btn-desc">⬇ Descargar para usar sin internet</button>
  </footer>
```

> Se quita el conteo fijo "103 canciones" del texto (se mantenía a mano en build); el sitio ya no depende de ese número.

- [ ] **Step 2: Añadir CSS del botón de descarga**

En el `<style>`, dentro de las reglas de `footer`, añadir:
```css
.btn-desc{
  margin-top:12px;padding:9px 16px;border-radius:10px;
  border:1px solid var(--tinta);color:var(--tinta);background:var(--tarjeta);
  font-size:13px;font-weight:600;
}
.btn-desc:hover{background:var(--papel2)}
.btn-desc[disabled]{opacity:.5;cursor:progress}
```

- [ ] **Step 3: Añadir la función de descarga (JS)**

Al final del `<script>`, antes de `iniciar();`, añadir:
```javascript
async function descargar(){
  const btn = document.getElementById('btnDescargar');
  btn.disabled = true; const txt = btn.textContent;
  btn.textContent = 'Preparando…';
  try{
    const resp = await fetch('index.html', {cache:'no-store'});
    if (!resp.ok) throw new Error('HTTP '+resp.status);
    const src = await resp.text();
    const out = '<!DOCTYPE html>\n' + inyectarDatos(src, SONGS).replace(/^<!DOCTYPE html>\s*/i,'');
    const blob = new Blob([out], {type:'text/html;charset=utf-8'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'Cancionero_Nueva_Alianza_San_Roberto.html';
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
    btn.textContent = '✓ Descargado';
    setTimeout(()=>{ btn.textContent = txt; btn.disabled = false; }, 2500);
  }catch(e){
    btn.textContent = 'No se pudo descargar';
    setTimeout(()=>{ btn.textContent = txt; btn.disabled = false; }, 2500);
  }
}
document.getElementById('btnDescargar').addEventListener('click', descargar);
```

> Toma el `index.html` original por `fetch` (fuente pristina), le incrusta las canciones vigentes con `inyectarDatos`, y dispara la descarga de un Blob. La copia descargada tiene `EMBEDDED` lleno, así que al abrirla desde `file://` carga sin red.

- [ ] **Step 4: Correr pruebas**

Run: `cd "/Users/andre/Documents/Claude/Projects/cancionero 2" && npm test`
Expected: `# fail 0` (la lógica pura `inyectarDatos` ya estaba cubierta en Task 3).

- [ ] **Step 5: Verificar el ciclo completo de descarga en navegador**

Servir en local (`python3 -m http.server 8765`). En `http://localhost:8765/`:
1. Clic en "⬇ Descargar"; confirmar que baja `Cancionero_Nueva_Alianza_San_Roberto.html`.
2. Abrir el archivo descargado con **doble clic** (protocolo `file://`, sin servidor).

Expected: la copia descargada muestra las 103 canciones y funciona completa (búsqueda, abrir canción, transponer, tema) **sin servidor ni internet** — porque trae `EMBEDDED` lleno. Detener el servidor.

- [ ] **Step 6: Commit**

```bash
git add index.html
git commit -m "feat: botón de descarga que genera copia offline autónoma

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: README, deploy en GitHub Pages y verificación final

**Files:**
- Create: `README.md`
- GitHub: crear repo `ministerio-de-musica-sr`, habilitar Pages

- [ ] **Step 1: Escribir `README.md`**

Create `README.md`:
```markdown
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
```

- [ ] **Step 2: Commit del README**

```bash
git add README.md
git commit -m "docs: README del proyecto

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

- [ ] **Step 3: Crear el repositorio en GitHub y subir**

Run (requiere `gh` autenticado):
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
gh repo create ministerio-de-musica-sr --public --source=. --remote=origin --push
```
Expected: el repo se crea y se sube `main`. Si `gh` no está autenticado, el agente debe detenerse y pedir al usuario que corra `gh auth login` (acción del usuario, no automatizable a ciegas).

- [ ] **Step 4: Habilitar GitHub Pages**

Run:
```bash
gh api -X POST repos/{owner}/ministerio-de-musica-sr/pages \
  -f 'source[branch]=main' -f 'source[path]=/' 2>/dev/null || \
gh api -X PUT repos/{owner}/ministerio-de-musica-sr/pages \
  -f 'source[branch]=main' -f 'source[path]=/'
```
Expected: respuesta con la URL de Pages. Sustituir `{owner}` por el usuario real (obtener con `gh api user --jq .login`).

> Alternativa manual si la API falla: el usuario va a Settings → Pages del repo, elige rama `main` y carpeta `/ (root)`.

- [ ] **Step 5: Verificar el sitio publicado**

Esperar ~1-2 min al primer build de Pages y abrir `https://<usuario>.github.io/ministerio-de-musica-sr/`.
Expected: el cancionero carga las 103 canciones, la búsqueda y la transposición funcionan, y el botón "Descargar" produce una copia offline funcional. Confirmar en móvil y en modo oscuro.

- [ ] **Step 6: Verificación de los criterios de éxito de Plan A**

Confirmar (criterios 1, 2 y 5 del spec):
- [ ] El sitio carga en GitHub Pages y se ve igual que el HTML actual.
- [ ] Un visitante sin token puede buscar, transponer y descargar offline.
- [ ] El archivo descargado funciona abierto desde `file://` sin internet.

---

## Self-Review (cobertura del spec en Plan A)

Plan A cubre los requisitos del spec que corresponden al sitio base:

- **Lector con búsqueda/transposición/tema/tamaño** → conservado del HTML actual (Task 1, verificado en Tasks 3-5).
- **Carga por `fetch`, sin paso de build** → Task 3.
- **Respaldo incrustado para `file://`** → Task 3 (`EMBEDDED`) + Task 5 (descarga lo rellena).
- **Quitar favoritas** → Task 4.
- **Descarga offline para todos** → Task 5.
- **Repo `ministerio-de-musica-sr` + GitHub Pages** → Tasks 1 y 6.
- **Criterios de éxito 1, 2, 5** → Task 6, Step 6.

Quedan para planes posteriores (fuera de Plan A, por diseño):
- **Plan B** — fidelidad de alineación al PDF (criterio 6).
- **Plan C** — rediseño de UI con frontend-design (criterio 7).
- **Plan D** — modo edición en navegador + guardado a GitHub (criterios 3).
- **Plan E** — agente importador por URL (criterio 4).

Sin placeholders: cada paso incluye el código o comando concreto. Tipos consistentes: `EMBEDDED`, `SONGS`, `inyectarDatos`, el literal del slot `==EMBED-SLOT==` y los marcadores `==PURE-START==/==PURE-END==` se usan igual en todas las tareas.

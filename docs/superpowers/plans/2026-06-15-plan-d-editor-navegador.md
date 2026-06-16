# Plan D — Editor en el navegador + publicación a GitHub — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Iterar la UI sobre capturas reales del preview.

**Goal:** Que solo el dueño pueda agregar, editar y borrar canciones desde el navegador (con un token de GitHub guardado localmente) y que cada cambio se publique solo para todos.

**Architecture:** Todo dentro del único `index.html`. Una capa de edición oculta se activa con un botón en el footer (solo fuera de `file://`). El parseo del texto del editor a `lines:[{k,t}]` vive en funciones puras (región `==PURE==`, testeables). La publicación usa la GitHub Contents API (GET para el `sha`, PUT con el `songs.json` nuevo) con el token del dueño en `localStorage`. La copia descargada (abierta desde `file://`) no muestra el editor.

**Tech Stack:** HTML + CSS + JS vanilla (un archivo, offline). Pruebas con `npm test` (Node `node:test`, harness de la región pura ya existente). GitHub Contents API (sin librerías). Repo ya en GitHub Pages.

**Fases:** Fase 1 (Tasks 1-3) = editor local que aplica cambios en memoria y se reflejan en la descarga; es shippable sin GitHub. Fase 2 (Tasks 4-6) = publicación real a GitHub.

**Restricciones:**
- Sin recursos externos salvo las llamadas a `api.github.com` (solo en modo edición). El lector sigue 100% offline.
- No tocar los marcadores `==PURE-START==`/`==PURE-END==`/`==EMBED-SLOT==`.
- Formato de `songs.json` preservado: `JSON.stringify(songs, null, 1)` (1 espacio, unicode sin escapar), igual que el Python.
- El token (PAT fine-grained, Contents: read/write solo de este repo) vive solo en `localStorage` del dueño; nunca se incrusta ni se sube.
- La copia descargada (`file://`) NO muestra el botón de editar.
- `npm test` en verde tras cada tarea.

---

## FASE 1 — Editor local

### Task 1: Funciones puras de parseo (texto ↔ líneas) + pruebas

**Files:**
- Modify: `index.html` (añadir funciones dentro de la región `==PURE==`)
- Create: `tests/editor.test.mjs`

- [ ] **Step 1: Añadir las funciones puras dentro de la región pura**

En `index.html`, justo antes de `/* ==PURE-END== */`, añadir:
```javascript
/* clasifica una línea NO vacía como acordes ('c') o letra ('l') */
const MARCADORES = new Set(['x2','x3','x4','X2','X3','X4','(x2)','(x3)','(x4)','//','////','|','N.C.','(bis)','bis','*','-','–']);
function esTokenAcorde(tk){ return MARCADORES.has(tk) || RE_CHORD.test(tk) || RE_SEQ.test(tk); }
function clasificarLinea(t){
  const toks = t.trim().split(/\s+/).filter(Boolean);
  if (!toks.length) return 'l';
  let n = 0; for (const tk of toks) if (esTokenAcorde(tk)) n++;
  return n / toks.length >= 0.5 ? 'c' : 'l';
}
/* convierte el texto del editor en líneas {k,t}; línea vacía -> blanco;
   recorta blancos al inicio y al final */
function textoALineas(texto){
  const out = texto.replace(/\r/g,'').split('\n').map(raw=>{
    const t = raw.replace(/\s+$/,'');
    if (!t.trim()) return {k:'b', t:''};
    return {k: clasificarLinea(t), t};
  });
  while (out.length && out[0].k==='b') out.shift();
  while (out.length && out[out.length-1].k==='b') out.pop();
  return out;
}
/* inverso: líneas -> texto (blanco -> línea vacía) */
function lineasATexto(lines){
  return lines.map(l => l.k==='b' ? '' : l.t).join('\n');
}
/* quita campos de runtime (id, _busq) para guardar */
function limpiarSong(s){
  return {title:s.title, author:s.author||'', section:s.section, page:s.page||0, lines:s.lines};
}
```

- [ ] **Step 2: Escribir las pruebas**

Create `tests/editor.test.mjs`:
```javascript
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cargarPuro } from './helper.mjs';

const ctx = cargarPuro(`
  globalThis.clasificarLinea = clasificarLinea;
  globalThis.textoALineas = textoALineas;
  globalThis.lineasATexto = lineasATexto;
  globalThis.limpiarSong = limpiarSong;
`);
const { clasificarLinea, textoALineas, lineasATexto, limpiarSong } = ctx;

test('clasifica una línea de acordes como c', () => {
  assert.equal(clasificarLinea('Em7        Bm   G/B'), 'c');
});
test('clasifica una línea de letra como l', () => {
  assert.equal(clasificarLinea('Si te tengo a ti, lo tengo todo'), 'l');
});
test('vocalización "La, ra la" es letra, no acordes', () => {
  assert.equal(clasificarLinea('La, ra la la la la la la'), 'l');
});
test('textoALineas separa acordes, letra y blancos', () => {
  const r = textoALineas('G   C\nHola mundo\n\nfin');
  assert.deepEqual(r, [
    {k:'c', t:'G   C'},
    {k:'l', t:'Hola mundo'},
    {k:'b', t:''},
    {k:'l', t:'fin'},
  ]);
});
test('textoALineas recorta blancos al inicio y final', () => {
  const r = textoALineas('\n\nHola\n\n');
  assert.deepEqual(r, [{k:'l', t:'Hola'}]);
});
test('lineasATexto es inverso de textoALineas para contenido típico', () => {
  const txt = 'G   C\nHola\n\nDm\nadiós';
  assert.equal(lineasATexto(textoALineas(txt)), txt);
});
test('limpiarSong quita id y _busq', () => {
  const s = {title:'X', author:'', section:'Alabanza', page:0, lines:[], id:3, _busq:'x'};
  assert.deepEqual(limpiarSong(s), {title:'X', author:'', section:'Alabanza', page:0, lines:[]});
});
```

- [ ] **Step 3: Correr pruebas**

Run: `cd "/Users/andre/Documents/Claude/Projects/cancionero 2" && npm test`
Expected: todas pasan (10 previas + 7 nuevas = 17).

> Si `clasificarLinea` discrepa en algún caso por la regex existente, ajustar el *valor esperado del test* al comportamiento real (no cambiar RE_CHORD/RE_SEQ).

- [ ] **Step 4: Commit**
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
git add index.html tests/editor.test.mjs
git commit -m "feat(editor): funciones puras de parseo texto<->líneas

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Activar modo edición + acciones en las filas

**Files:**
- Modify: `index.html` (CSS de filas/acciones; HTML del footer; `fila()`, `render()`; estado de edición)

- [ ] **Step 1: Añadir estado de edición y guardas**

Cerca del inicio del `<script>` (después de `let fsMax = ...`), añadir:
```javascript
let editMode = false;
let token = store.get('ghtoken', '');
let editando = null;   // índice en SONGS, o null = agregar
const PUEDE_EDITAR = location.protocol !== 'file:';   // la copia offline no edita
```

- [ ] **Step 2: Reestructurar `fila()` para permitir botones de acción**

El `fila()` actual devuelve un `<button>`; no puede contener botones anidados. Reemplazar la función `fila(s)` por una que devuelve un `<div>` con un área clicable y acciones opcionales:
```javascript
function fila(s){
  const div = document.createElement('div');
  div.className = 'fila';
  const ir = document.createElement('button');
  ir.className = 'fila-ir';
  ir.innerHTML = `<span class="cinta" style="background:${COLOR[s.section]}"></span>
    <span class="t"><b>${s.title}</b>${s.author?`<i>${s.author}</i>`:''}</span>
    <span class="pg">p.${s.page}</span>
    <span class="chevron" aria-hidden="true">›</span>`;
  ir.onclick = () => abrir(s.id);
  div.appendChild(ir);
  if (editMode){
    const acc = document.createElement('div');
    acc.className = 'fila-acc';
    acc.innerHTML = `<button class="ed" title="Editar">✎</button><button class="bo" title="Borrar">🗑</button>`;
    acc.querySelector('.ed').onclick = (e)=>{ e.stopPropagation(); editarCancion(s.id); };
    acc.querySelector('.bo').onclick = (e)=>{ e.stopPropagation(); borrarCancion(s.id); };
    div.appendChild(acc);
  }
  return div;
}
```

- [ ] **Step 3: Ajustar el CSS de `.fila` para la nueva estructura**

Localiza la regla `.fila{...}` y sus relacionadas (sección índice). Reemplazar el bloque `.fila{...}` … `.fila .chevron{...}` por:
```css
.fila{
  display:flex;align-items:stretch;gap:0;width:100%;
  background:var(--tarjeta);border:1px solid var(--linea);border-radius:var(--r2);
  margin-bottom:var(--s2);box-shadow:var(--sombra);overflow:hidden;
}
.fila:hover{border-color:var(--tinta);box-shadow:var(--sombra-alta)}
.fila-ir{
  display:flex;align-items:center;gap:var(--s3);flex:1;min-width:0;text-align:left;
  padding:12px 14px;background:none;
}
.fila .cinta{width:4px;align-self:stretch;border-radius:var(--rpill);flex:none}
.fila .t{flex:1;min-width:0}
.fila .t b{font-weight:600;font-size:15px;display:block;line-height:1.3;color:var(--texto)}
.fila .t i{font-style:normal;font-size:12px;color:var(--suave)}
.fila .pg{font-family:var(--mono);font-size:11px;color:var(--suave);flex:none}
.fila .chevron{color:var(--suave);flex:none;font-size:17px;opacity:.5}
.fila-acc{display:flex;align-items:center;border-left:1px solid var(--linea)}
.fila-acc button{padding:0 12px;align-self:stretch;font-size:15px;color:var(--suave)}
.fila-acc .ed:hover{color:var(--tinta);background:var(--tinta-soft)}
.fila-acc .bo:hover{color:#C84B31;background:var(--papel2)}
```

- [ ] **Step 4: Añadir el botón "Editar" y "Agregar" al footer**

En el footer, después del botón de descarga, añadir un contenedor de edición:
```html
    <button id="btnDescargar" class="btn-desc">⬇ Descargar para usar sin internet</button>
    <div id="zonaEdicion"></div>
```
Y al final del `<script>`, antes de `iniciar();`, añadir el armado del botón:
```javascript
function pintarZonaEdicion(){
  const z = document.getElementById('zonaEdicion');
  if (!PUEDE_EDITAR){ z.innerHTML=''; return; }
  z.innerHTML = editMode
    ? `<button id="btnAgregar" class="btn-ed">➕ Agregar canción</button>
       <button id="btnSalirEd" class="btn-ed plano">Salir de edición</button>`
    : `<button id="btnEntrarEd" class="btn-ed plano">✎ Editar</button>`;
  if (editMode){
    document.getElementById('btnAgregar').onclick = ()=> agregarCancion();
    document.getElementById('btnSalirEd').onclick = ()=>{ editMode=false; pintarZonaEdicion(); render(); };
  } else {
    document.getElementById('btnEntrarEd').onclick = entrarEdicion;
  }
}
```

- [ ] **Step 5: Añadir CSS de los botones de edición y stubs de funciones**

En el `<style>`, junto a `.btn-desc`, añadir:
```css
.btn-ed{margin-top:var(--s3);margin-left:6px;margin-right:6px;padding:9px 14px;border-radius:var(--r2);border:1px solid var(--tinta);background:var(--tinta);color:var(--sobre-tinta);font-size:13px;font-weight:600}
.btn-ed.plano{background:var(--tarjeta);color:var(--tinta)}
.btn-ed:hover{box-shadow:var(--sombra-alta)}
```
Y stubs en el `<script>` (se completan en Tasks siguientes). En esta tarea, `entrarEdicion` activa el modo directamente (sin token todavía):
```javascript
function entrarEdicion(){ editMode = true; pintarZonaEdicion(); render(); }
function agregarCancion(){ abrirEditor(null); }
function editarCancion(id){ abrirEditor(id); }
function borrarCancion(id){
  const s = SONGS[id];
  if (!confirm('¿Borrar «'+s.title+'»?')) return;
  SONGS.splice(id,1);
  SONGS.forEach((x,i)=> x.id=i);
  render();
}
function abrirEditor(id){ alert('Editor en construcción (Task 3). id='+id); }
```
Llamar `pintarZonaEdicion();` justo antes de `iniciar();`.

- [ ] **Step 6: Correr pruebas y verificar en navegador**

Run: `npm test` → 17/17.
Servir con el preview (config `cancionero`). Confirmar en captura: aparece "✎ Editar" en el footer; al activarlo, cada fila muestra ✎ y 🗑, y aparecen "➕ Agregar canción" y "Salir de edición". Probar borrar una canción (confirmación + desaparece de la lista en memoria). NO recargar (el borrado es solo en memoria todavía).

- [ ] **Step 7: Commit**
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
git add index.html
git commit -m "feat(editor): modo edición con acciones editar/borrar y agregar (en memoria)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Formulario del editor con vista previa en vivo

**Files:**
- Modify: `index.html` (overlay `#editor`, CSS, lógica del formulario y preview)

- [ ] **Step 1: Añadir el overlay del editor (HTML)**

Después de la `<section id="cancion">` … `</section>`, añadir:
```html
<section id="editor" role="dialog" aria-modal="true" aria-labelledby="edTitulo">
  <div class="c-top">
    <button id="edCancelar">← Cancelar</button>
    <button id="edGuardar" class="btn-ed">Guardar</button>
  </div>
  <div class="ed-scroll">
    <h2 id="edTitulo" class="ed-h">Nueva canción</h2>
    <label class="ed-campo">Título<input id="edTitle" type="text" autocomplete="off"></label>
    <label class="ed-campo">Autor (opcional)<input id="edAutor" type="text" autocomplete="off"></label>
    <label class="ed-campo">Sección<select id="edSeccion"></select></label>
    <label class="ed-campo">Acordes y letra (acordes en su propia línea, encima de la letra)
      <textarea id="edCuerpo" rows="10" spellcheck="false"></textarea></label>
    <div class="ed-prev-tit">Vista previa <small>(toca una línea para cambiar acorde↔letra)</small></div>
    <pre class="hoja" id="edPreview"></pre>
    <div id="edMsg" class="ed-msg"></div>
  </div>
</section>
```

- [ ] **Step 2: Añadir el CSS del editor**

En el `<style>`, antes de `footer{`, añadir:
```css
#editor{position:fixed;inset:0;z-index:30;background:var(--papel);display:none;flex-direction:column}
#editor.abierto{display:flex}
.ed-scroll{flex:1;overflow:auto;-webkit-overflow-scrolling:touch;max-width:760px;margin:0 auto;width:100%;padding:var(--s4) var(--s5) 80px}
.ed-h{font-family:var(--mono);color:var(--tinta);font-size:20px;margin-bottom:var(--s4)}
.ed-campo{display:block;font-size:12px;color:var(--suave);margin-bottom:var(--s4);font-weight:600}
.ed-campo input,.ed-campo select,.ed-campo textarea{
  display:block;width:100%;margin-top:6px;padding:10px 12px;font-size:15px;
  border:1px solid var(--linea);border-radius:var(--r1);background:var(--tarjeta);color:var(--texto);
  font-weight:400;
}
.ed-campo textarea{font-family:var(--mono);font-size:13px;line-height:1.5;white-space:pre;overflow-x:auto;resize:vertical}
.ed-prev-tit{font-size:12px;color:var(--suave);font-weight:600;margin:var(--s4) 0 var(--s2)}
.ed-prev-tit small{font-weight:400}
#edPreview{cursor:pointer}
#edPreview .c{color:var(--acorde);font-weight:700}
#edPreview .b{display:block;height:1em}
.ed-msg{margin-top:var(--s4);font-size:13px;min-height:1.4em}
.ed-msg.error{color:#C84B31}
.ed-msg.ok{color:#5F8E6E}
```

- [ ] **Step 3: Poblar el select de secciones y la lógica de abrir/cerrar/preview**

Al final del `<script>`, antes de `pintarZonaEdicion();`, añadir:
```javascript
const $editor=document.getElementById('editor'),
      $edTitle=document.getElementById('edTitle'), $edAutor=document.getElementById('edAutor'),
      $edSeccion=document.getElementById('edSeccion'), $edCuerpo=document.getElementById('edCuerpo'),
      $edPreview=document.getElementById('edPreview'), $edMsg=document.getElementById('edMsg'),
      $edTitulo=document.getElementById('edTitulo');
SECCIONES.forEach(s=>{ const o=document.createElement('option'); o.value=s; o.textContent=s; $edSeccion.appendChild(o); });

let edOverrides = {};   // {indiceLinea: 'c'|'l'} forzado por el usuario
function edLineas(){
  const base = textoALineas($edCuerpo.value);
  return base.map((l,i)=> (l.k!=='b' && edOverrides[i]) ? {k:edOverrides[i], t:l.t} : l);
}
function pintarPreview(){
  const lines = edLineas();
  $edPreview.innerHTML = lines.map((l,i)=>{
    if (l.k==='b') return '<span class="b"></span>';
    const esc = l.t.replace(/&/g,'&amp;').replace(/</g,'&lt;');
    return `<span class="${l.k==='c'?'c':'l'}" data-i="${i}">${esc}</span>\n`;
  }).join('');
}
$edCuerpo.addEventListener('input', ()=>{ edOverrides={}; pintarPreview(); });
$edPreview.addEventListener('click', e=>{
  const sp = e.target.closest('span[data-i]'); if (!sp) return;
  const i = +sp.dataset.i; const lines = edLineas();
  if (lines[i].k==='b') return;
  edOverrides[i] = lines[i].k==='c' ? 'l' : 'c';
  pintarPreview();
});
function abrirEditor(id){
  editando = id;
  edOverrides = {}; $edMsg.className='ed-msg'; $edMsg.textContent='';
  if (id==null){
    $edTitulo.textContent='Nueva canción';
    $edTitle.value=''; $edAutor.value=''; $edSeccion.value=SECCIONES[0]; $edCuerpo.value='';
  } else {
    const s=SONGS[id];
    $edTitulo.textContent='Editar canción';
    $edTitle.value=s.title; $edAutor.value=s.author||''; $edSeccion.value=s.section;
    $edCuerpo.value=lineasATexto(s.lines);
  }
  pintarPreview();
  $editor.classList.add('abierto');
}
function cerrarEditor(){ $editor.classList.remove('abierto'); editando=null; }
document.getElementById('edCancelar').onclick=cerrarEditor;
```

- [ ] **Step 4: Implementar Guardar (en memoria por ahora)**

Añadir (después de lo anterior):
```javascript
function objetoDelForm(){
  return {
    title: $edTitle.value.trim(),
    author: $edAutor.value.trim(),
    section: $edSeccion.value,
    page: (editando!=null ? (SONGS[editando].page||0) : 0),
    lines: edLineas(),
  };
}
function validarForm(o){
  if (!o.title) return 'Falta el título.';
  if (!o.lines.length) return 'El cuerpo está vacío.';
  return '';
}
document.getElementById('edGuardar').onclick = async ()=>{
  const o = objetoDelForm();
  const err = validarForm(o);
  if (err){ $edMsg.className='ed-msg error'; $edMsg.textContent=err; return; }
  if (editando!=null) SONGS[editando] = {...o, id:editando};
  else SONGS.push({...o, id:SONGS.length});
  SONGS.forEach((s,i)=>{ s.id=i; s._busq = norm(s.title+' '+(s.author||'')+' '+s.lines.map(l=>l.t).join(' ')); });
  render();
  cerrarEditor();
};
```
Actualizar el stub `abrirEditor` de Task 2 — ya queda reemplazado por esta versión completa (borrar el stub `function abrirEditor(id){ alert(... }` de Task 2 si quedó).

- [ ] **Step 5: Correr pruebas y verificar en navegador**

Run: `npm test` → 17/17.
Servir y, en modo edición: (a) "➕ Agregar canción" → llenar título "Prueba", sección, y en el cuerpo pegar un par de líneas de acordes y letra; confirmar en captura que la vista previa colorea los acordes en azul y que tocar una línea cambia su tipo; Guardar → aparece en el índice. (b) Editar una canción existente → el cuerpo se llena con sus líneas; cambiar el título; Guardar → se refleja. (Todo en memoria; sin publicar aún.)

- [ ] **Step 6: Commit**
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
git add index.html
git commit -m "feat(editor): formulario con vista previa en vivo y override de tipo de línea

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## FASE 2 — Publicación a GitHub

### Task 4: Cliente de GitHub + captura y validación del token

**Files:**
- Modify: `index.html` (funciones de GitHub; flujo de token en `entrarEdicion`)

- [ ] **Step 1: Añadir el cliente de GitHub (no pure; va fuera de la región pura)**

Después de `/* ==PURE-END== */` (en el script normal), añadir:
```javascript
const REPO_FALLBACK = {owner:'DevRacf', repo:'ministerio-de-musica-sr'};
function repoInfo(){
  const host = location.hostname;
  if (host.endsWith('github.io')){
    const owner = host.split('.')[0];
    const repo = location.pathname.split('/').filter(Boolean)[0];
    if (owner && repo) return {owner, repo};
  }
  return REPO_FALLBACK;
}
function ghHeaders(t){ return {'Authorization':'Bearer '+t,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'}; }
const GH_PATH = 'datos/songs.json';
async function ghLeer(t){
  const {owner,repo}=repoInfo();
  const r = await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${GH_PATH}`, {headers:ghHeaders(t), cache:'no-store'});
  if (r.status===401) throw new Error('token');
  if (!r.ok) throw new Error('http '+r.status);
  const j = await r.json();
  const texto = decodeURIComponent(escape(atob(j.content.replace(/\n/g,''))));
  return {sha:j.sha, songs:JSON.parse(texto)};
}
async function ghEscribir(t, songs, sha, msg){
  const {owner,repo}=repoInfo();
  const contenido = btoa(unescape(encodeURIComponent(JSON.stringify(songs, null, 1))));
  const r = await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${GH_PATH}`, {
    method:'PUT', headers:ghHeaders(t),
    body: JSON.stringify({message:msg, content:contenido, sha})
  });
  if (r.status===401) throw new Error('token');
  if (r.status===409 || r.status===422) throw new Error('conflicto');
  if (!r.ok) throw new Error('http '+r.status);
  return r.json();
}
async function publicar(msg){
  const {sha} = await ghLeer(token);
  await ghEscribir(token, SONGS.map(limpiarSong), sha, msg);
}
```

- [ ] **Step 2: Reemplazar `entrarEdicion` por el flujo con token**

Reemplazar la función `entrarEdicion` (stub de Task 2) por:
```javascript
async function entrarEdicion(){
  if (!token){
    const t = prompt('Pega tu token de GitHub (fine-grained, con permiso Contents: read/write sobre el repo del cancionero):');
    if (!t) return;
    token = t.trim();
  }
  // validar el token con una lectura
  try{
    await ghLeer(token);
  }catch(e){
    token = '';
    alert(e.message==='token'
      ? 'El token no es válido o no tiene permiso. Crea uno fine-grained con Contents: read/write y reintenta.'
      : 'No se pudo verificar el token (¿sin internet?). Intenta de nuevo.');
    return;
  }
  store.set('ghtoken', token);
  editMode = true; pintarZonaEdicion(); render();
}
```

- [ ] **Step 3: Correr pruebas**

Run: `npm test` → 17/17 (las funciones de GitHub no son puras y no se cargan en el harness; no rompen nada).

- [ ] **Step 4: Commit**
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
git add index.html
git commit -m "feat(editor): cliente de GitHub Contents API + captura/validación de token

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Conectar guardar/borrar a la publicación + manejo de errores

**Files:**
- Modify: `index.html` (guardar y borrar publican; mensajes de estado)

- [ ] **Step 1: Hacer que Guardar publique**

Reemplazar el handler `document.getElementById('edGuardar').onclick = ...` (de Task 3) por:
```javascript
document.getElementById('edGuardar').onclick = async ()=>{
  const o = objetoDelForm();
  const err = validarForm(o);
  if (err){ $edMsg.className='ed-msg error'; $edMsg.textContent=err; return; }
  const btn = document.getElementById('edGuardar');
  btn.disabled = true; $edMsg.className='ed-msg'; $edMsg.textContent='Publicando…';
  // aplicar en memoria
  const respaldo = SONGS.map(limpiarSong);
  if (editando!=null) SONGS[editando] = {...o, id:editando};
  else SONGS.push({...o, id:SONGS.length});
  SONGS.forEach((s,i)=>{ s.id=i; s._busq = norm(s.title+' '+(s.author||'')+' '+s.lines.map(l=>l.t).join(' ')); });
  try{
    await publicar((editando!=null?'Editar: ':'Agregar: ')+o.title);
    render(); cerrarEditor();
  }catch(e){
    // revertir memoria
    SONGS.length = 0; respaldo.forEach((s,i)=> SONGS.push({...s, id:i}));
    SONGS.forEach(s=>{ s._busq = norm(s.title+' '+(s.author||'')+' '+s.lines.map(l=>l.t).join(' ')); });
    $edMsg.className='ed-msg error';
    $edMsg.textContent = mensajeError(e);
  }finally{ btn.disabled=false; }
};
function mensajeError(e){
  if (e.message==='token'){ token=''; store.set('ghtoken',''); return 'Token inválido o vencido. Sal de edición y vuelve a entrar para ponerlo de nuevo.'; }
  if (e.message==='conflicto') return 'Alguien más editó el cancionero. Recarga la página y reintenta (tu texto sigue aquí).';
  return 'No se pudo publicar (¿sin internet?). Reintenta; tu texto sigue aquí.';
}
```

- [ ] **Step 2: Hacer que Borrar publique**

Reemplazar `borrarCancion` (de Task 2) por:
```javascript
async function borrarCancion(id){
  const s = SONGS[id];
  if (!confirm('¿Borrar «'+s.title+'» y publicar el cambio?')) return;
  const respaldo = SONGS.map(limpiarSong);
  SONGS.splice(id,1);
  SONGS.forEach((x,i)=> x.id=i);
  render();
  try{
    await publicar('Borrar: '+s.title);
  }catch(e){
    SONGS.length=0; respaldo.forEach((x,i)=> SONGS.push({...x, id:i}));
    SONGS.forEach(x=>{ x._busq = norm(x.title+' '+(x.author||'')+' '+x.lines.map(l=>l.t).join(' ')); });
    render();
    alert(mensajeError(e));
  }
}
```

- [ ] **Step 3: Correr pruebas**

Run: `npm test` → 17/17.

- [ ] **Step 4: Commit**
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
git add index.html
git commit -m "feat(editor): publicar a GitHub al guardar/borrar, con reversión y mensajes de error

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Verificación end-to-end y deploy

**Files:**
- Verificación + push. La copia descargada NO debe mostrar el editor.

- [ ] **Step 1: Verificar que la descarga offline no trae editor**

Servir con el preview. Confirmar que en `http://localhost` aparece "✎ Editar"; descargar la copia y abrirla por `file://`: el botón "✎ Editar" NO aparece (porque `PUEDE_EDITAR` es falso en `file://`). Capturar ambas.

- [ ] **Step 2: Tests y push**

Run: `cd "/Users/andre/Documents/Claude/Projects/cancionero 2" && npm test` → 17/17.
```bash
git push origin main
```
Esperar el rebuild de Pages.

- [ ] **Step 3: Prueba real de publicación (la hace el dueño con su token)**

En el sitio en vivo `https://devracf.github.io/ministerio-de-musica-sr/`:
1. El dueño crea un **PAT fine-grained** en GitHub (Settings → Developer settings → Fine-grained tokens) con acceso **solo** al repo `ministerio-de-musica-sr` y permiso **Contents: Read and write**.
2. Clic en "✎ Editar", pegar el token. Debe entrar en modo edición.
3. Agregar una canción de prueba (o editar una), Guardar → ver "Publicando…" y luego que cierra. En ~1 min, recargar y confirmar que el cambio quedó. Verificar el commit nuevo en GitHub.
4. Borrar esa canción de prueba para dejar el cancionero limpio; confirmar que se publica.

> Esta prueba requiere el token del dueño (no se puede automatizar sin él). El agente acompaña y verifica el resultado (commits en el repo, conteo de canciones).

- [ ] **Step 4: Verificación del criterio de éxito de Plan D (criterio 3 del spec)**
- [ ] El dueño, con token, agrega/edita/borra una canción desde el navegador y el cambio aparece publicado para todos.
- [ ] La copia descargada no muestra el editor.

---

## Self-Review (cobertura del spec en Plan D)

La sección "Modo edición" del spec pide: botón en footer que activa edición; pedir PAT fine-grained la primera vez y guardarlo en localStorage; editar/borrar por canción y agregar; formulario (título, autor, sección, cuerpo monoespaciado) con detección automática de acordes y override por línea; vista previa coloreada; guardar vía Contents API (leer sha, PUT) con mensaje de commit; manejo de errores (token, conflicto, offline); la copia descargada desactiva edición. Cobertura:

- **Parseo + detección de acordes + override** → Task 1 (puro, testeado) + Task 3 (preview con toggle por línea).
- **Botón en footer + editar/borrar/agregar** → Task 2.
- **Formulario + vista previa coloreada** → Task 3.
- **Token PAT en localStorage + validación** → Task 4.
- **Guardar/borrar vía Contents API (sha + PUT) + commit message** → Tasks 4-5.
- **Errores (token/conflicto/offline) con reversión** → Task 5.
- **Copia descargada sin editor (`file://`)** → Task 2 (`PUEDE_EDITAR`) + Task 6.
- **Criterio de éxito 3** → Task 6.

Sin placeholders salvo los stubs intencionales de Task 2 (alert/entrarEdicion simples) que se reemplazan explícitamente por la versión completa en Tasks 3-4 (indicado en cada caso). Nombres consistentes: `clasificarLinea`, `textoALineas`, `lineasATexto`, `limpiarSong`, `edLineas`, `edOverrides`, `objetoDelForm`, `validarForm`, `publicar`, `ghLeer`, `ghEscribir`, `repoInfo`, `entrarEdicion`, `abrirEditor`, `borrarCancion`, `PUEDE_EDITAR`, `editando`, `token` se usan igual en todas las tareas.

**Riesgo aceptado (del spec):** el token vive en `localStorage` de un sitio público; es fine-grained y acotado a un repo. `publicar()` reescribe `songs.json` con el estado local + sha fresco; para un solo editor el riesgo de pisar cambios remotos es bajo y el caso de conflicto se maneja con mensaje + reintento.

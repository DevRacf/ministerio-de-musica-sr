# Mixes — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development o executing-plans. Pasos con checkbox. Iterar la UI sobre capturas del preview.

**Goal:** Agregar "Mixes" (listas ordenadas de canciones) compartidas vía GitHub, con navegación Anterior/Siguiente en vivo y editor en el navegador.

**Architecture:** Dentro del único `index.html`. Datos en `datos/mixes.json` (cargado por fetch, con respaldo `EMBEDDED_MIXES` para offline). Lógica de resolución/orden en funciones puras testeables. Publicación reusando el cliente GitHub del editor, generalizado por ruta.

**Tech Stack:** HTML/CSS/JS vanilla; `npm test` (node:test); GitHub Contents API.

**Restricciones:** sin recursos externos salvo api.github.com (modo edición); no tocar marcadores existentes; formato `JSON.stringify(x,null,1)`; `npm test` verde tras cada tarea; mixes referencian canciones por título.

---

### Task 1: Datos de mixes + funciones puras + carga

**Files:** Create `datos/mixes.json`; Modify `index.html` (slot EMBEDDED_MIXES, funciones puras, carga); Create `tests/mixes.test.mjs`.

- [ ] **Step 1: Crear `datos/mixes.json`** con contenido `[]`.

- [ ] **Step 2: Añadir slot de incrustación de mixes** en `index.html`, junto a `EMBEDDED`:
```javascript
const EMBEDDED_MIXES = null; /* ==EMBED-MIXES== */
let MIXES = [];
```
(justo después de `let SONGS = [];`)

- [ ] **Step 3: Añadir funciones puras** dentro de la región `==PURE==` (antes de `==PURE-END==`):
```javascript
/* resuelve los títulos de un mix a índices de songs; idx=null si no existe */
function resolverMix(mix, songs){
  const porTitulo = {};
  songs.forEach((s,i)=>{ const k=(s.title||'').trim().toLowerCase(); if(!(k in porTitulo)) porTitulo[k]=i; });
  return (mix.songs||[]).map((t,pos)=>{
    const idx = porTitulo[(t||'').trim().toLowerCase()];
    return {pos, title:t, idx: idx==null ? null : idx};
  });
}
/* mueve el elemento i de arr en dirección dir (-1 arriba, +1 abajo); no muta */
function moverEnLista(arr, i, dir){
  const j = i + dir;
  if (j < 0 || j >= arr.length) return arr.slice();
  const out = arr.slice();
  [out[i], out[j]] = [out[j], out[i]];
  return out;
}
```
Y extender `inyectarDatos` para incrustar también los mixes:
```javascript
function inyectarDatos(src, songs, mixes){
  const slotS = 'const EMBEDDED = null; /* ==EMBED-SLOT== */';
  const slotM = 'const EMBEDDED_MIXES = null; /* ==EMBED-MIXES== */';
  if (!src.includes(slotS)) throw new Error('No se encontró el slot EMBEDDED');
  let out = src.replace(slotS, 'const EMBEDDED = ' + JSON.stringify(songs) + '; /* ==EMBED-SLOT== */');
  if (src.includes(slotM)) out = out.replace(slotM, 'const EMBEDDED_MIXES = ' + JSON.stringify(mixes||[]) + '; /* ==EMBED-MIXES== */');
  return out;
}
```

- [ ] **Step 4: Cargar mixes en `iniciar()`** y reflejar en el render. Tras asignar SONGS en `iniciar()`, añadir:
```javascript
  MIXES = await cargarMixes();
```
y definir junto a `cargarSongs`:
```javascript
async function cargarMixes(){
  if (Array.isArray(EMBEDDED_MIXES)) return EMBEDDED_MIXES;
  try{ const r = await fetch('datos/mixes.json', {cache:'no-store'}); if(!r.ok) throw 0; return await r.json(); }
  catch(e){ return []; }
}
```

- [ ] **Step 5: Actualizar la llamada de descarga** `inyectarDatos(src, SONGS)` → `inyectarDatos(src, SONGS, MIXES)`.

- [ ] **Step 6: Pruebas** `tests/mixes.test.mjs`:
```javascript
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cargarPuro } from './helper.mjs';
const ctx = cargarPuro(`globalThis.resolverMix=resolverMix; globalThis.moverEnLista=moverEnLista; globalThis.inyectarDatos=inyectarDatos;`);
const { resolverMix, moverEnLista, inyectarDatos } = ctx;
const igual=(a,b)=>assert.equal(JSON.stringify(a),JSON.stringify(b));
const songs=[{title:'Pues tú glorioso'},{title:'Hay gran voz'},{title:'Grande es el Señor'}];

test('resolverMix mapea títulos a índices', () => {
  igual(resolverMix({songs:['Hay gran voz','Pues tú glorioso']}, songs),
        [{pos:0,title:'Hay gran voz',idx:1},{pos:1,title:'Pues tú glorioso',idx:0}]);
});
test('resolverMix marca no encontrada con idx null', () => {
  igual(resolverMix({songs:['No existe']}, songs), [{pos:0,title:'No existe',idx:null}]);
});
test('moverEnLista sube un elemento sin mutar', () => {
  const a=['a','b','c']; igual(moverEnLista(a,1,-1), ['b','a','c']); igual(a,['a','b','c']);
});
test('moverEnLista en el borde no cambia', () => {
  igual(moverEnLista(['a','b'],0,-1), ['a','b']);
});
test('inyectarDatos incrusta songs y mixes', () => {
  const src='X\nconst EMBEDDED = null; /* ==EMBED-SLOT== */\nconst EMBEDDED_MIXES = null; /* ==EMBED-MIXES== */\nY';
  const out=inyectarDatos(src,[{title:'A'}],[{name:'M',songs:['A']}]);
  assert.ok(out.includes('const EMBEDDED = [{"title":"A"}]'));
  assert.ok(out.includes('const EMBEDDED_MIXES = [{"name":"M","songs":["A"]}]'));
});
```

- [ ] **Step 7:** `npm test` → todas pasan. Verificar carga en navegador (sin errores).

- [ ] **Step 8: Commit** `feat(mixes): datos, funciones puras de resolución/orden y carga`.

---

### Task 2: Vista de Mixes (chip + lista) en el lector

**Files:** Modify `index.html` (chip, render de mixes, CSS, abrir mix).

- [ ] **Step 1: Añadir el chip "♫ Mixes"** al inicio de `chipDefs`:
```javascript
const chipDefs=['♫ Mixes','Todas',...SECCIONES];
```

- [ ] **Step 2: En `render()`, si `filtroSec==='♫ Mixes'`, pintar la lista de mixes** y salir antes del render normal. Añadir al inicio de `render()` (tras calcular q):
```javascript
  if (filtroSec==='♫ Mixes'){ renderMixes(); return; }
```

- [ ] **Step 3: Implementar `renderMixes()` y `filaMix()`**:
```javascript
function renderMixes(){
  $lista.innerHTML='';
  if (!MIXES.length){
    $lista.innerHTML='<div class="vacio">Aún no hay mixes.'+(editMode?'<br>Toca “➕ Nuevo mix” para crear uno.':'')+'</div>';
    if (editMode) pintarNuevoMix();
    return;
  }
  if (editMode) pintarNuevoMix();
  MIXES.forEach((m,mi)=> $lista.appendChild(filaMix(m,mi)));
}
function filaMix(m, mi){
  const div=document.createElement('div'); div.className='fila';
  const ir=document.createElement('button'); ir.className='fila-ir mix-ir';
  const items=resolverMix(m,SONGS);
  const lista=items.map(it=>`<span class="${it.idx==null?'mx-no':''}">${it.pos+1}. ${it.title}</span>`).join('<br>');
  ir.innerHTML=`<span class="t"><b>♫ ${m.name}</b><span class="mx-lista">${lista}</span></span><span class="chevron">›</span>`;
  ir.onclick=()=> abrirMix(mi,0);
  div.appendChild(ir);
  if (editMode){
    const acc=document.createElement('div'); acc.className='fila-acc';
    acc.innerHTML=`<button class="ed" title="Editar">✎</button><button class="bo" title="Borrar">🗑</button>`;
    acc.querySelector('.ed').onclick=(e)=>{e.stopPropagation();abrirEditorMix(mi);};
    acc.querySelector('.bo').onclick=(e)=>{e.stopPropagation();borrarMix(mi);};
    div.appendChild(acc);
  }
  return div;
}
function pintarNuevoMix(){
  const b=document.createElement('button'); b.className='btn-ed'; b.style.margin='0 0 12px';
  b.textContent='➕ Nuevo mix'; b.onclick=()=>abrirEditorMix(null); $lista.appendChild(b);
}
```

- [ ] **Step 4: CSS** (junto al índice):
```css
.mx-lista{display:block;font-size:12px;color:var(--suave);line-height:1.7;margin-top:4px}
.mx-no{text-decoration:line-through;color:var(--suave);opacity:.7}
.mix-ir b{color:var(--tinta)}
```

- [ ] **Step 5: Stubs** (se completan en Tasks 3-4) — añadir:
```javascript
function abrirMix(mi,pos){ alert('navegación de mix (Task 3)'); }
function abrirEditorMix(mi){ alert('editor de mix (Task 4)'); }
function borrarMix(mi){ alert('borrar mix (Task 4)'); }
```

- [ ] **Step 6:** `npm test` verde. En navegador: el chip "♫ Mixes" aparece; seleccionarlo muestra el estado vacío (aún sin mixes). Commit `feat(mixes): vista de lista con chip Mixes`.

---

### Task 3: Navegación dentro del mix (Anterior/Siguiente)

**Files:** Modify `index.html` (estado enMix, barra de navegación en la canción, `abrir`/`cerrar`).

- [ ] **Step 1: Estado** — junto a `let actual=...`: `let enMix = null;  // {mixIdx, pos}`.

- [ ] **Step 2: Implementar `abrirMix`** (reemplaza el stub):
```javascript
function abrirMix(mi, pos){
  const items = resolverMix(MIXES[mi], SONGS).filter(it=>it.idx!=null);
  if (!items.length){ alert('Este mix no tiene canciones disponibles.'); return; }
  pos = Math.max(0, Math.min(pos, items.length-1));
  enMix = {mixIdx:mi, pos};
  abrir(items[pos].idx);
}
function navMix(d){
  if (!enMix) return;
  const items = resolverMix(MIXES[enMix.mixIdx], SONGS).filter(it=>it.idx!=null);
  const np = enMix.pos + d;
  if (np<0 || np>=items.length) return;
  enMix.pos = np; abrir(items[np].idx);
}
```

- [ ] **Step 3: Añadir la barra de navegación** al final del scroll de la canción. En el HTML de `#cancion`, tras `.hoja-wrap`, añadir:
```html
      <div class="mix-nav" id="mixNav"></div>
```
Y CSS:
```css
.mix-nav{display:none;gap:8px;max-width:760px;margin:0 auto;padding:0 var(--s5) 96px}
.mix-nav.on{display:flex}
.mix-nav button{flex:1;padding:11px;border-radius:var(--r2);border:1px solid var(--linea);background:var(--tarjeta);color:var(--tinta);font-weight:600;font-size:13px}
.mix-nav button.sig{background:var(--tinta);color:var(--sobre-tinta);border-color:var(--tinta)}
.mix-nav button[disabled]{opacity:.4}
```

- [ ] **Step 4: Pintar la barra en `abrir()`** — al final de `abrir(id)`, añadir:
```javascript
  pintarMixNav();
```
y la función:
```javascript
function pintarMixNav(){
  const nav=document.getElementById('mixNav');
  const cTop=document.getElementById('btnVolver');
  if (!enMix){ nav.className='mix-nav'; nav.innerHTML=''; cTop.textContent='← Índice'; return; }
  const items=resolverMix(MIXES[enMix.mixIdx],SONGS).filter(it=>it.idx!=null);
  const m=MIXES[enMix.mixIdx];
  cTop.textContent='← '+m.name+'  ('+(enMix.pos+1)+'/'+items.length+')';
  nav.className='mix-nav on';
  nav.innerHTML=`<button id="mxAnt" ${enMix.pos===0?'disabled':''}>← Anterior</button>
                 <button id="mxSig" class="sig" ${enMix.pos===items.length-1?'disabled':''}>Siguiente →</button>`;
  document.getElementById('mxAnt').onclick=()=>navMix(-1);
  document.getElementById('mxSig').onclick=()=>navMix(1);
}
```

- [ ] **Step 5: Salir del mix** — en `cerrar()` (botón volver), si `enMix`, volver a la lista de mixes en vez del índice:
```javascript
function cerrar(){
  $vista.classList.remove('abierta');
  if (enMix){ enMix=null; filtroSec='♫ Mixes'; [...$chips.children].forEach(x=>x.setAttribute('aria-pressed', x.textContent.includes('Mixes'))); render(); }
  if (location.hash) history.pushState(null,'','#');
}
```
(Asegurar que abrir una canción normal pone `enMix=null`: en `fila()`→`abrir`, el flujo normal no setea enMix; añadir `enMix=null;` al inicio de `abrir(id)` SOLO si no viene de abrirMix. Para distinguir, abrirMix setea enMix ANTES de llamar abrir; abrir NO debe resetearlo. Las filas normales: en su `onclick` llamar `enMix=null; abrir(s.id)`.)

Actualizar `fila()` `ir.onclick=()=>{ enMix=null; abrir(s.id); }`.

- [ ] **Step 6:** `npm test` verde. (No hay mixes reales aún; la prueba visual completa va en la verificación final tras crear un mix.) Commit `feat(mixes): navegación anterior/siguiente dentro del mix`.

---

### Task 4: Editor de mixes + publicación a GitHub

**Files:** Modify `index.html` (overlay editor de mix, cliente GitHub por ruta, publicar/borrar).

- [ ] **Step 1: Generalizar el cliente GitHub por ruta.** Cambiar `ghLeer`/`ghEscribir` para aceptar `path`:
```javascript
async function ghLeer(t, path){
  const {owner,repo}=repoInfo();
  const r = await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${path}`, {headers:ghHeaders(t), cache:'no-store'});
  if (r.status===401) throw new Error('token');
  if (!r.ok) throw new Error('http '+r.status);
  const j = await r.json();
  return {sha:j.sha, datos:JSON.parse(decodeURIComponent(escape(atob(j.content.replace(/\n/g,'')))))};
}
async function ghEscribir(t, path, datos, sha, msg){
  const {owner,repo}=repoInfo();
  const contenido = btoa(unescape(encodeURIComponent(JSON.stringify(datos, null, 1))));
  const r = await fetch(`https://api.github.com/repos/${owner}/${repo}/contents/${path}`, {
    method:'PUT', headers:ghHeaders(t), body: JSON.stringify({message:msg, content:contenido, sha})});
  if (r.status===401) throw new Error('token');
  if (r.status===409||r.status===422) throw new Error('conflicto');
  if (!r.ok) throw new Error('http '+r.status);
  return r.json();
}
async function publicar(msg){ const {sha}=await ghLeer(token, GH_PATH); await ghEscribir(token, GH_PATH, SONGS.map(limpiarSong), sha, msg); }
async function publicarMixes(msg){ const {sha}=await ghLeer(token, 'datos/mixes.json'); await ghEscribir(token, 'datos/mixes.json', MIXES, sha, msg); }
```
(Actualizar la validación de token en `entrarEdicion`: `await ghLeer(token, GH_PATH);`)

- [ ] **Step 2: Overlay del editor de mix (HTML)** tras `#editor`:
```html
<section id="mixEditor" role="dialog" aria-modal="true">
  <div class="c-top"><button id="mxCancelar">← Cancelar</button><button id="mxGuardar" class="btn-ed">Guardar</button></div>
  <div class="ed-scroll">
    <h2 class="ed-h" id="mxTitulo">Nuevo mix</h2>
    <label class="ed-campo">Nombre<input id="mxNombre" type="text" autocomplete="off"></label>
    <label class="ed-campo">Agregar canción<input id="mxBuscar" type="text" placeholder="Buscar por título…" autocomplete="off"></label>
    <div id="mxResultados" class="mx-res"></div>
    <div class="ed-prev-tit">En el mix</div>
    <div id="mxLista"></div>
    <div id="mxMsg" class="ed-msg"></div>
  </div>
</section>
```
CSS:
```css
#mixEditor{position:fixed;inset:0;z-index:31;background:var(--papel);display:none;flex-direction:column}
#mixEditor.abierto{display:flex}
.mx-res{display:flex;flex-direction:column;gap:4px;max-height:160px;overflow:auto}
.mx-res button{text-align:left;padding:8px 10px;border:1px solid var(--linea);background:var(--tarjeta);border-radius:var(--r1);font-size:13px}
.mx-it{display:flex;align-items:center;gap:8px;background:var(--tarjeta);border:1px solid var(--linea);border-radius:var(--r1);padding:7px 9px;margin-bottom:6px}
.mx-it .n{font-family:var(--mono);color:var(--suave);font-size:12px}
.mx-it .tt{flex:1;font-size:13px}
.mx-it button{color:var(--suave);font-size:15px;padding:2px 5px}
.mx-it .qu{color:#C84B31}
```

- [ ] **Step 3: Lógica del editor de mix:**
```javascript
const $mixEditor=document.getElementById('mixEditor');
let mixEditando=null, mixBorrador={name:'',songs:[]};
function abrirEditorMix(mi){
  mixEditando=mi;
  mixBorrador = mi==null ? {name:'',songs:[]} : {name:MIXES[mi].name, songs:[...MIXES[mi].songs]};
  document.getElementById('mxTitulo').textContent = mi==null?'Nuevo mix':'Editar mix';
  document.getElementById('mxNombre').value=mixBorrador.name;
  document.getElementById('mxBuscar').value='';
  document.getElementById('mxMsg').textContent='';
  pintarMxResultados(''); pintarMxLista();
  $mixEditor.classList.add('abierto');
}
function pintarMxLista(){
  const c=document.getElementById('mxLista'); c.innerHTML='';
  mixBorrador.songs.forEach((t,i)=>{
    const d=document.createElement('div'); d.className='mx-it';
    d.innerHTML=`<span class="n">${i+1}</span><span class="tt">${t}</span>
      <button class="up">↑</button><button class="dn">↓</button><button class="qu">✕</button>`;
    d.querySelector('.up').onclick=()=>{ mixBorrador.songs=moverEnLista(mixBorrador.songs,i,-1); pintarMxLista(); };
    d.querySelector('.dn').onclick=()=>{ mixBorrador.songs=moverEnLista(mixBorrador.songs,i,1); pintarMxLista(); };
    d.querySelector('.qu').onclick=()=>{ mixBorrador.songs.splice(i,1); pintarMxLista(); };
    c.appendChild(d);
  });
}
function pintarMxResultados(q){
  const c=document.getElementById('mxResultados'); c.innerHTML=''; const nq=norm(q.trim());
  if (!nq) return;
  SONGS.filter(s=>norm(s.title).includes(nq)).slice(0,8).forEach(s=>{
    const b=document.createElement('button'); b.textContent='➕ '+s.title;
    b.onclick=()=>{ mixBorrador.songs.push(s.title); document.getElementById('mxBuscar').value=''; pintarMxResultados(''); pintarMxLista(); };
    c.appendChild(b);
  });
}
document.getElementById('mxBuscar').addEventListener('input', e=>pintarMxResultados(e.target.value));
document.getElementById('mxNombre').addEventListener('input', e=>{ mixBorrador.name=e.target.value; });
document.getElementById('mxCancelar').onclick=()=>$mixEditor.classList.remove('abierto');
```

- [ ] **Step 4: Guardar y borrar (publican):**
```javascript
document.getElementById('mxGuardar').onclick = async ()=>{
  const msg=document.getElementById('mxMsg');
  if (!mixBorrador.name.trim()){ msg.className='ed-msg error'; msg.textContent='Falta el nombre.'; return; }
  if (!mixBorrador.songs.length){ msg.className='ed-msg error'; msg.textContent='Agrega al menos una canción.'; return; }
  const btn=document.getElementById('mxGuardar'); btn.disabled=true; msg.className='ed-msg'; msg.textContent='Publicando…';
  const respaldo=JSON.parse(JSON.stringify(MIXES));
  const obj={name:mixBorrador.name.trim(), songs:[...mixBorrador.songs]};
  if (mixEditando!=null) MIXES[mixEditando]=obj; else MIXES.push(obj);
  try{ await publicarMixes('Mix: '+obj.name); $mixEditor.classList.remove('abierto'); render(); }
  catch(e){ MIXES.length=0; respaldo.forEach(x=>MIXES.push(x)); msg.className='ed-msg error'; msg.textContent=mensajeError(e); }
  finally{ btn.disabled=false; }
};
async function borrarMix(mi){
  if (!confirm('¿Borrar el mix «'+MIXES[mi].name+'» y publicar?')) return;
  const respaldo=JSON.parse(JSON.stringify(MIXES));
  const nombre=MIXES[mi].name; MIXES.splice(mi,1); render();
  try{ await publicarMixes('Borrar mix: '+nombre); }
  catch(e){ MIXES.length=0; respaldo.forEach(x=>MIXES.push(x)); render(); alert(mensajeError(e)); }
}
```

- [ ] **Step 5:** `npm test` verde; navegador sin errores. Commit `feat(mixes): editor de mixes con publicación a GitHub`.

---

### Task 5: Verificación end-to-end y deploy

- [ ] **Step 1:** `npm test` → todo verde.
- [ ] **Step 2:** Servir; verificar el chip Mixes, el estado vacío, y que la copia descargada incrusta `EMBEDDED_MIXES` (revisar el blob).
- [ ] **Step 3:** Confirmar que el reader sigue sin recursos externos salvo api.github.com.
- [ ] **Step 4:** `git push origin main`; esperar Pages.
- [ ] **Step 5 (prueba real con token del dueño):** crear un mix (nombre + 2-3 canciones ordenadas), publicar; abrirlo y recorrer con Anterior/Siguiente; verificar el commit en el repo. Borrar el mix de prueba o dejar uno real.

---

## Self-Review

Cubre spec: datos+carga (T1), chip+lista (T2), navegación (T3), editor+publicar (T4), verificación/deploy/offline (T5). Funciones puras `resolverMix`/`moverEnLista`/`inyectarDatos` testeadas (T1). Referencia por título y "no encontrada" → resolverMix (idx null) + clase `.mx-no`. Offline → EMBEDDED_MIXES + inyectarDatos extendido. Sin placeholders salvo stubs de T2 reemplazados en T3-T4 (indicado). Nombres consistentes: MIXES, EMBEDDED_MIXES, resolverMix, moverEnLista, enMix, abrirMix, navMix, pintarMixNav, abrirEditorMix, borrarMix, publicarMixes, mixBorrador.

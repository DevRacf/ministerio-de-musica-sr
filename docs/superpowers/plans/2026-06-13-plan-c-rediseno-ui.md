# Plan C — Rediseño de UI con frontend-design — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. La ejecución debe apoyarse en la skill **frontend-design** para las decisiones estéticas, e iterar sobre capturas de pantalla reales.

**Goal:** Elevar la calidad visual del único `index.html` del cancionero (pulido, no rediseño radical) conservando la identidad de marca, la hoja de acordes monoespaciada y el funcionamiento 100% offline.

**Architecture:** Cambios solo en el `<style>` y el marcado del `index.html`; la lógica JS (transposición, carga, descarga, render) NO se toca salvo cambios mínimos de clases/estructura necesarios para el estilo. Se refina primero el sistema de diseño (tokens CSS) y luego cada zona (encabezado, índice, vista de canción, footer) se reconstruye sobre esos tokens.

**Tech Stack:** HTML + CSS (un archivo, sin dependencias). Solo fuentes del sistema (sin webfonts ni CDNs). Verificación visual con el preview en navegador; `npm test` para confirmar que la lógica pura sigue intacta.

**Restricciones duras (aplican a TODAS las tareas):**
- Sin CDNs, sin webfonts, sin recursos externos: el sitio debe seguir cargando 100% offline.
- Conservar marca: teal `#0F4761`, azul de acordes `#215E99` (y sus equivalentes en modo oscuro).
- La hoja de acordes (`.hoja`) sigue en fuente **monoespaciada** con `white-space:pre` (no romper la alineación de acordes).
- Conservar: modo claro/oscuro, responsive móvil-primero, `focus-visible`, `prefers-reduced-motion`.
- No tocar los marcadores `==PURE-START==`/`==PURE-END==` ni `==EMBED-SLOT==`, ni la lógica JS dentro.
- Tras cada tarea: `npm test` debe seguir en verde (10/10) y la app debe cargar las 103 canciones.

**Método de verificación visual (se usa en cada tarea):** servir con el preview (`launch.json` ya existe en la raíz del workspace con la config `cancionero`), tomar capturas en modo claro y oscuro, y revisar en ancho móvil (~390px) y escritorio. La ejecución itera sobre estas capturas con la skill frontend-design hasta que la zona se vea pulida.

---

### Task 1: Sistema de diseño (tokens CSS refinados)

Establece la base: paleta más rica, y escalas de espaciado, radios, sombras y tipografía como variables. Todo lo demás se construye sobre esto.

**Files:**
- Modify: `index.html` (bloque `:root` y `html[data-theme="oscuro"]` dentro de `<style>`, líneas ~9-30)

- [ ] **Step 1: Reemplazar el bloque de variables `:root` y oscuro**

Localiza el bloque actual `:root{ ... }` y `html[data-theme="oscuro"]{ ... }` (líneas ~9-30) y reemplázalo por:
```css
:root{
  /* marca (no cambiar los hex de marca) */
  --tinta:#0F4761;        /* teal de títulos */
  --acorde:#215E99;       /* azul de acordes */
  --dorado:#C8A24B;
  /* superficies y texto (paleta papel cálido) */
  --papel:#FBF8F2;
  --papel2:#F2ECDF;
  --tarjeta:#FFFFFF;
  --texto:#22282B;
  --suave:#6A7280;
  --linea:#E6DFCD;
  /* tono de marca translúcido para realces */
  --tinta-soft:rgba(15,71,97,.08);
  --acorde-soft:rgba(33,94,153,.10);
  /* escala de espaciado */
  --s1:4px; --s2:8px; --s3:12px; --s4:16px; --s5:24px; --s6:32px;
  /* radios */
  --r1:8px; --r2:12px; --r3:16px; --rpill:999px;
  /* sombras (suaves, modo claro) */
  --sombra:0 1px 2px rgba(20,30,40,.04), 0 2px 8px rgba(20,30,40,.05);
  --sombra-alta:0 6px 24px rgba(20,30,40,.10);
  /* tipografía */
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace;
  --fs:13px;              /* tamaño de la hoja de acordes */
}
html[data-theme="oscuro"]{
  --tinta:#9CCBE0;
  --acorde:#7FB3E8;
  --papel:#0B181F;
  --papel2:#10242E;
  --tarjeta:#13272F;
  --texto:#E7E3D7;
  --suave:#8F9DA4;
  --linea:#213642;
  --tinta-soft:rgba(156,203,224,.10);
  --acorde-soft:rgba(127,179,232,.14);
  --sombra:0 1px 2px rgba(0,0,0,.30), 0 2px 10px rgba(0,0,0,.30);
  --sombra-alta:0 8px 28px rgba(0,0,0,.45);
}
```

- [ ] **Step 2: Actualizar `body` y utilidades base para usar los tokens de fuente**

Localiza la regla `body{ ... font-family:-apple-system,...; }` (línea ~33-37) y cambia la familia a la variable:
```css
body{
  background:var(--papel);color:var(--texto);
  font-family:var(--sans);
  -webkit-text-size-adjust:100%;
}
```
Y la utilidad `.mono`:
```css
.mono{font-family:var(--mono)}
```

- [ ] **Step 3: Añadir transición global suave (respetando reduced-motion)**

Justo después de la regla `*{box-sizing:border-box;margin:0;padding:0}` añade:
```css
.fila,.chip,.btn-desc,.grupo button,#btnAcordes,#btnTema{transition:background .15s ease,border-color .15s ease,color .15s ease,box-shadow .15s ease,transform .08s ease}
```
(La regla `@media (prefers-reduced-motion:reduce){*{transition:none!important;...}}` ya existe y la neutraliza cuando corresponde — confirma que sigue presente.)

- [ ] **Step 4: Verificar tests y carga**

Run: `cd "/Users/andre/Documents/Claude/Projects/cancionero 2" && npm test`
Expected: 10/10 pass (no tocamos JS).

Servir con el preview (config `cancionero`) y confirmar que la app carga las 103 canciones y NO hay colores rotos (ningún valor de color inválido). Tomar una captura en claro y otra en oscuro.

- [ ] **Step 5: Commit**
```bash
git add index.html
git commit -m "refactor(ui): sistema de diseño con tokens de espaciado, sombra y tipografía

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Encabezado, búsqueda y chips de sección

Hacer el encabezado más confiado y la búsqueda más prominente; chips con mejor estado activo.

**Files:**
- Modify: `index.html` (CSS de `header`, `.brand`, `.cruz`, `.buscar`, `.chips`, `.chip`; marcado del `<header>` si hace falta)

- [ ] **Step 1: Reescribir el CSS del encabezado y marca**

Localiza las reglas desde `/* ====== encabezado ====== */` hasta justo antes de `/* ====== índice ====== */` (líneas ~43-71) y reemplázalas por:
```css
/* ====== encabezado ====== */
header{
  position:sticky;top:0;z-index:10;
  background:color-mix(in srgb,var(--papel) 88%,transparent);
  backdrop-filter:saturate(1.2) blur(8px);
  -webkit-backdrop-filter:saturate(1.2) blur(8px);
  border-bottom:1px solid var(--linea);
  padding:env(safe-area-inset-top) 0 0;
}
.brand{display:flex;align-items:center;gap:var(--s3);padding:var(--s3) var(--s4) var(--s2)}
.cruz{
  width:38px;height:38px;flex:none;border-radius:10px;
  background:linear-gradient(145deg,var(--tinta),color-mix(in srgb,var(--tinta) 70%,#000));
  display:grid;place-items:center;color:#fff;font-weight:700;
  font-family:var(--mono);font-size:20px;box-shadow:var(--sombra);
}
.brand h1{font-family:var(--mono);font-size:18px;letter-spacing:.01em;color:var(--tinta);line-height:1.05}
.brand small{display:block;font-family:var(--sans);font-weight:500;font-size:10.5px;color:var(--suave);letter-spacing:.10em;text-transform:uppercase;margin-top:3px}
#btnTema{margin-left:auto;font-size:20px;padding:8px 10px;border-radius:var(--r1);color:var(--suave)}
#btnTema:hover{background:var(--papel2);color:var(--tinta)}
.buscar{padding:0 var(--s4) var(--s3)}
.buscar input{
  width:100%;padding:11px 15px;font-size:16px;border-radius:var(--r2);
  border:1px solid var(--linea);background:var(--tarjeta);color:var(--texto);
  box-shadow:var(--sombra);
}
.buscar input:focus{border-color:var(--acorde)}
.buscar input::placeholder{color:var(--suave)}
.chips{display:flex;gap:var(--s2);overflow-x:auto;padding:0 var(--s4) var(--s3);scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chip{
  flex:none;padding:7px 14px;border-radius:var(--rpill);font-size:13px;font-weight:500;
  border:1px solid var(--linea);background:var(--tarjeta);color:var(--texto);white-space:nowrap;
}
.chip:hover{border-color:var(--tinta)}
.chip[aria-pressed="true"]{background:var(--tinta);border-color:var(--tinta);color:#fff;font-weight:600}
.chip .dot{display:inline-block;width:8px;height:8px;border-radius:99px;margin-right:6px;vertical-align:1px}
.chip[aria-pressed="true"] .dot{box-shadow:0 0 0 2px rgba(255,255,255,.5)}
```

> `color-mix` y `backdrop-filter` tienen amplio soporte en navegadores modernos; si el preview no los soporta, el `background` translúcido degrada de forma aceptable. Verifica en la captura que el header se lee bien al hacer scroll.

- [ ] **Step 2: Verificar tests, carga y apariencia**

Run: `npm test` → 10/10.
Servir y capturar el encabezado en claro y oscuro, en móvil (~390px) y escritorio. Confirmar: marca legible, búsqueda prominente, chips con estado activo claro, header translúcido al hacer scroll.

- [ ] **Step 3: Commit**
```bash
git add index.html
git commit -m "feat(ui): encabezado translúcido, búsqueda y chips pulidos

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Índice — cabeceras de sección y filas de canción

Mejorar jerarquía y tacto de las tarjetas del índice.

**Files:**
- Modify: `index.html` (CSS de `main`, `.sec-h`, `.fila`, `.vacio`)

- [ ] **Step 1: Reescribir el CSS del índice**

Localiza desde `/* ====== índice ====== */` hasta justo antes de `/* ====== vista de canción ====== */` (líneas ~73-91) y reemplázalo por:
```css
/* ====== índice ====== */
main{max-width:680px;margin:0 auto;padding:var(--s3) var(--s3) 64px}
.sec-h{
  display:flex;align-items:center;gap:var(--s3);
  margin:var(--s6) var(--s1) var(--s3);
  position:sticky;top:0;z-index:1;
}
.sec-h .cinta{width:28px;height:14px;border-radius:0 0 6px 6px;flex:none}
.sec-h h2{font-family:var(--mono);font-size:14px;letter-spacing:.16em;text-transform:uppercase;color:var(--tinta);flex:1}
.sec-h span{
  font-size:11px;color:var(--suave);font-family:var(--mono);
  background:var(--papel2);padding:2px 9px;border-radius:var(--rpill);
}
.fila{
  display:flex;align-items:center;gap:var(--s3);width:100%;text-align:left;
  background:var(--tarjeta);border:1px solid var(--linea);border-radius:var(--r2);
  padding:12px 14px;margin-bottom:var(--s2);box-shadow:var(--sombra);
}
.fila:hover{border-color:var(--tinta);transform:translateY(-1px);box-shadow:var(--sombra-alta)}
.fila:active{transform:translateY(0)}
.fila .cinta{width:4px;align-self:stretch;border-radius:var(--rpill);flex:none}
.fila .t{flex:1;min-width:0}
.fila .t b{font-weight:600;font-size:15px;display:block;line-height:1.3;color:var(--texto)}
.fila .t i{font-style:normal;font-size:12px;color:var(--suave)}
.fila .pg{font-family:var(--mono);font-size:11px;color:var(--suave);flex:none}
.fila .chevron{color:var(--suave);flex:none;font-size:15px;opacity:.5}
.vacio{text-align:center;color:var(--suave);padding:56px 16px;font-size:14px;line-height:1.7}
```

- [ ] **Step 2: Añadir un chevron a la fila (marcado JS)**

En la función `fila(s)` (líneas ~266-274) el `innerHTML` termina con `<span class="pg">p.${s.page}</span>`. Para dar señal de "tocable", añade un chevron después de la página. Reemplaza:
```javascript
    <span class="pg">p.${s.page}</span>`;
```
por:
```javascript
    <span class="pg">p.${s.page}</span>
    <span class="chevron" aria-hidden="true">›</span>`;
```
(Es el único cambio de JS en esta tarea; no afecta la lógica.)

- [ ] **Step 3: Verificar**

Run: `npm test` → 10/10.
Servir y capturar el índice: confirmar tarjetas con sombra suave, hover que eleva, cabeceras de sección sticky con contador en píldora, y el chevron en cada fila. Probar en oscuro y móvil.

- [ ] **Step 4: Commit**
```bash
git add index.html
git commit -m "feat(ui): índice con tarjetas elevadas y cabeceras de sección sticky

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Vista de canción — barra, cabecera y hoja de acordes

Refinar la pantalla de canción: barra superior, herramientas (tono/tamaño/acordes) y la "hoja" tipo papel.

**Files:**
- Modify: `index.html` (CSS de `#cancion`, `.c-top`, `.c-cab`, `.c-herr`, `.grupo`, `#btnAcordes`, `.hoja-wrap`, `.hoja`)

- [ ] **Step 1: Reescribir el CSS de la vista de canción**

Localiza desde `/* ====== vista de canción ====== */` hasta justo antes de `footer{` (líneas ~93-129) y reemplázalo por:
```css
/* ====== vista de canción ====== */
#cancion{position:fixed;inset:0;z-index:20;background:var(--papel);display:none;flex-direction:column}
#cancion.abierta{display:flex}
.c-top{
  display:flex;align-items:center;gap:var(--s2);padding:10px var(--s3) 9px;
  padding-top:calc(10px + env(safe-area-inset-top));
  border-bottom:1px solid var(--linea);
  background:color-mix(in srgb,var(--papel) 90%,transparent);
  backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);
}
.c-top button{padding:8px 11px;border-radius:var(--r1);font-size:14px}
#btnVolver{font-weight:600;color:var(--tinta)}
#btnVolver:hover{background:var(--tinta-soft)}
.c-scroll{flex:1;overflow:auto;-webkit-overflow-scrolling:touch}
.c-cab{padding:var(--s5) var(--s5) var(--s1);max-width:760px;margin:0 auto;width:100%}
.c-cab .eyebrow{display:flex;align-items:center;gap:var(--s2);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--suave);margin-bottom:var(--s2)}
.c-cab .eyebrow .cinta{width:24px;height:11px;border-radius:0 0 5px 5px}
.c-cab h2{font-family:var(--mono);color:var(--tinta);font-size:25px;line-height:1.18;font-weight:700;letter-spacing:-.01em}
.c-cab .autor{font-size:13px;color:var(--suave);font-style:italic;margin-top:6px}
.c-herr{
  display:flex;flex-wrap:wrap;gap:var(--s2);align-items:center;
  padding:var(--s4) var(--s5);max-width:760px;margin:0 auto;width:100%;
}
.grupo{display:flex;align-items:center;border:1px solid var(--linea);border-radius:var(--r1);background:var(--tarjeta);overflow:hidden;box-shadow:var(--sombra)}
.grupo button{padding:8px 13px;font-size:15px;line-height:1}
.grupo button:hover{background:var(--papel2)}
.grupo .val{font-family:var(--mono);font-size:12px;min-width:48px;text-align:center;color:var(--texto)}
.grupo .lbl{font-size:10.5px;color:var(--suave);padding-left:12px;letter-spacing:.06em;text-transform:uppercase}
#btnAcordes{border:1px solid var(--linea);border-radius:var(--r1);background:var(--tarjeta);padding:8px 13px;font-size:12px;color:var(--texto);box-shadow:var(--sombra);font-weight:600}
#btnAcordes:hover{background:var(--papel2)}
#btnAcordes[aria-pressed="false"]{color:var(--suave);text-decoration:line-through;font-weight:400}
.hoja-wrap{padding:var(--s1) var(--s5) 96px;max-width:760px;margin:0 auto;width:100%}
.hoja{
  font-family:var(--mono);
  font-size:var(--fs);line-height:1.5;white-space:pre;overflow-x:auto;
  background:var(--tarjeta);border:1px solid var(--linea);border-radius:var(--r3);
  padding:var(--s5) var(--s4);box-shadow:var(--sombra);
}
.hoja .c{color:var(--acorde);font-weight:700}
.hoja.sin-acordes .c{display:none}
.hoja .b{display:block;height:1em}
.hoja.sin-acordes .c + .b{display:none}
```

> CRÍTICO: la `.hoja` debe seguir con `font-family:var(--mono)` (monoespaciada) y `white-space:pre`. No cambies eso o se rompe la alineación de acordes.

- [ ] **Step 2: Verificar la alineación de acordes no se rompió**

Servir, abrir "Así como David danzaba", y confirmar en captura que los acordes (azul) siguen cayendo exactamente sobre la misma columna de letra que antes (la fuente sigue monoespaciada). Probar transponer +2 y −2: la hoja se actualiza y los acordes siguen alineados por carácter. Probar el botón "Acordes" (ocultar/mostrar). Probar A+/A−.

Run: `npm test` → 10/10.

- [ ] **Step 3: Commit**
```bash
git add index.html
git commit -m "feat(ui): vista de canción con barra translúcida y hoja tipo papel

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: Footer, estado vacío, botón de descarga y repaso de modo oscuro

Cerrar detalles: footer, descarga, estado vacío y una pasada final de contraste en oscuro.

**Files:**
- Modify: `index.html` (CSS de `footer`, `.btn-desc`; revisión de `.vacio` en oscuro)

- [ ] **Step 1: Reescribir el CSS del footer y botón de descarga**

Localiza desde `footer{` hasta el final del `<style>` (`.btn-desc[disabled]{...}`, líneas ~130-141) y reemplázalo por:
```css
footer{
  text-align:center;color:var(--suave);font-size:12px;line-height:1.8;
  padding:var(--s6) var(--s5) calc(var(--s6) + env(safe-area-inset-bottom));
  border-top:1px solid var(--linea);margin-top:var(--s6);
}
footer b{color:var(--tinta);font-family:var(--mono);font-weight:700}
.btn-desc{
  margin-top:var(--s4);padding:11px 18px;border-radius:var(--r2);
  border:1px solid var(--tinta);color:#fff;
  background:linear-gradient(145deg,var(--tinta),color-mix(in srgb,var(--tinta) 78%,#000));
  font-size:13px;font-weight:600;box-shadow:var(--sombra);
}
.btn-desc:hover{box-shadow:var(--sombra-alta);transform:translateY(-1px)}
.btn-desc:active{transform:translateY(0)}
.btn-desc[disabled]{opacity:.6;cursor:progress;transform:none;box-shadow:var(--sombra)}
```

- [ ] **Step 2: Repaso de contraste en modo oscuro**

Servir en modo oscuro y revisar en captura cada zona (encabezado, índice, vista de canción, footer). Verifica con el preview que el texto sobre fondos cumple contraste razonable. Si algún token de color oscuro da bajo contraste (p. ej. `--suave` sobre `--tarjeta`), ajusta SOLO el valor del token en `html[data-theme="oscuro"]` (no las reglas de componentes). Documenta cualquier ajuste.

- [ ] **Step 3: Verificar todo el flujo**

Run: `npm test` → 10/10.
Servir y recorrer: índice → abrir canción → transponer → volver → cambiar tema → descargar. Capturar el footer con el botón de descarga en claro y oscuro.

- [ ] **Step 4: Commit**
```bash
git add index.html
git commit -m "feat(ui): footer, botón de descarga y repaso de modo oscuro

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Verificación integral, descarga offline y deploy

**Files:**
- Verificación + push a `origin/main`

- [ ] **Step 1: Confirmar que la copia descargada conserva el nuevo diseño y funciona offline**

Servir, hacer clic en "Descargar" (o capturar el blob como en Plan A), guardar el HTML y abrirlo desde `file://`. Confirmar que la copia offline:
- Muestra el nuevo diseño (tokens, encabezado, índice, hoja).
- Carga las 103 canciones desde `EMBEDDED` (sin red).
- Permite abrir canción y transponer.

- [ ] **Step 2: Verificación responsive y de accesibilidad**

Con el preview, capturar a ~390px (móvil) y ~1000px (escritorio), en claro y oscuro. Confirmar: nada se desborda, los chips hacen scroll horizontal, la hoja de acordes hace scroll horizontal si una línea es larga, y el `focus-visible` se ve al tabular por los controles.

- [ ] **Step 3: Tests finales**

Run: `cd "/Users/andre/Documents/Claude/Projects/cancionero 2" && npm test`
Expected: 10/10 pass.

- [ ] **Step 4: Push y verificación en vivo**
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
git push origin main
```
Esperar ~1-2 min al rebuild de Pages y abrir `https://devracf.github.io/ministerio-de-musica-sr/`. Confirmar que el sitio en vivo muestra el rediseño y carga las 103 canciones.

- [ ] **Step 5: Verificación de los criterios de éxito de Plan C (criterio 7 del spec)**
- [ ] El UI rediseñado conserva la identidad de marca (teal/azul).
- [ ] Funciona en móvil y en modo oscuro.
- [ ] Sigue cargando sin recursos externos (sin CDNs/webfonts).
- [ ] La alineación de acordes monoespaciada se conserva intacta.

---

## Self-Review (cobertura del spec en Plan C)

La sección "Rediseño de UI" del spec pide: pulido visual conservando marca y hoja monoespaciada; mantener claro/oscuro, responsive, accesibilidad y offline sin recursos externos; ejecutar con frontend-design. Cobertura:

- **Tokens / sistema de diseño** → Task 1.
- **Encabezado, búsqueda, chips** → Task 2.
- **Índice (secciones + filas)** → Task 3.
- **Vista de canción + hoja monoespaciada intacta** → Task 4 (con verificación explícita de alineación).
- **Footer, descarga, contraste oscuro** → Task 5.
- **Offline conservado, responsive, accesibilidad, deploy** → Task 6 (criterio de éxito 7).

Restricciones duras (sin externos, marca, monoespaciado, reduced-motion, no tocar marcadores/JS) declaradas arriba y repetidas en las tareas críticas. Sin placeholders. Nombres de tokens consistentes (`--s1..--s6`, `--r1..--r3`, `--rpill`, `--sombra`, `--sombra-alta`, `--sans`, `--mono`, `--tinta-soft`, `--acorde-soft`) usados igual en todas las tareas.
```

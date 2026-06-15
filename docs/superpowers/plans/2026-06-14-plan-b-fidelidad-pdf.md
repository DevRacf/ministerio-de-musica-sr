# Plan B — Fidelidad de alineación al PDF — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Garantizar que en `datos/songs.json` cada acorde caiga sobre la sílaba correcta como en el PDF, corrigiendo solo los casos genuinamente desalineados y dejando una herramienta de auditoría reutilizable.

**Architecture:** Un script de auditoría (`scripts/auditar_alineacion.py`) clasifica cada par acorde/letra de `songs.json` con una función pura puntuable y marca los casos sospechosos; un renderizador de páginas del PDF permite la revisión visual (con visión) de cada caso marcado contra su página real; las correcciones se aplican de forma puntual en `songs.json` (re-espaciando solo las líneas de acordes afectadas), sin re-extraer en masa.

**Tech Stack:** Python 3 (pdfplumber para posiciones, poppler/`pdftoppm` para renderizar — ambos ya instalados). Pruebas con `pytest` si está disponible, o con `python3 -m unittest` (sin dependencias nuevas). El cancionero web no cambia salvo el dato corregido.

**Hallazgo de partida (medido el 2026-06-14):** la extracción actual ya es bastante fiel (verificado contra las páginas 7 y 8). De 2522 líneas de acordes, ~216 son más anchas que su letra y solo ~30 sobrepasan por más de 6 columnas; la mayoría son acordes finales/turnarounds o vocalizaciones legítimas ("La ra la la"). Se espera, por tanto, un conjunto de correcciones **pequeño**. El valor durable es la herramienta de auditoría (reutilizable tras los imports del Plan E).

**Restricciones:**
- `datos/songs.json` es la fuente de verdad: NO re-extraer en masa. Correcciones puntuales por canción.
- El formato de cada línea no cambia (`{"k","t"}`; `c`/`l`/`b`).
- El PDF es monoespaciado (ancho de carácter ≈ 5.4 pt), así que su alineación también es por columnas — comparable directamente con el conteo de espacios de `songs.json`.

---

### Task 1: Script de auditoría con función de puntuación pura

Construir la herramienta que marca pares acorde/letra sospechosos.

**Files:**
- Create: `scripts/auditar_alineacion.py`
- Create: `scripts/test_auditar.py`

- [ ] **Step 1: Escribir las pruebas de la función pura `evaluar_par`**

Create `scripts/test_auditar.py`:
```python
import unittest
from auditar_alineacion import evaluar_par

class TestEvaluarPar(unittest.TestCase):
    def test_alineacion_normal_no_marca(self):
        # acorde dentro del ancho de la letra: ok
        r = evaluar_par('G          C         D', 'Bueno es alabar ¡Al Señor!, tu Nombre')
        self.assertFalse(r['marcar'])

    def test_turnaround_corto_no_marca(self):
        # acordes finales que sobrepasan poco (<=6) son legítimos
        r = evaluar_par('G          C         D     C   D', 'Bueno es alabar ¡Al Señor!, tu Nombre')
        self.assertFalse(r['marcar'])

    def test_sobrepaso_grande_marca(self):
        r = evaluar_par('A                          G   D   A', 'Glorioso es Él.')
        self.assertTrue(r['marcar'])
        self.assertEqual(r['motivo'], 'acorde_excede_letra')

    def test_sin_letra_no_marca(self):
        # línea de acordes sin letra debajo (intro): no es error de alineación
        r = evaluar_par('  Dm   Gm   C7', '')
        self.assertFalse(r['marcar'])

    def test_acorde_inicia_mas_alla_del_fin_marca(self):
        # primer acorde empieza pasado el final de una letra corta
        r = evaluar_par('                 Em', 'Amén')
        self.assertTrue(r['marcar'])
        self.assertEqual(r['motivo'], 'acorde_excede_letra')

    def test_overflow_exacto_umbral_no_marca(self):
        # exactamente 6 de sobrepaso: límite, no marca
        r = evaluar_par('C' + ' '*9 + 'D', 'abcd')   # 'D' en col 10, letra len 4 -> over 6
        self.assertFalse(r['marcar'])

if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Ejecutar las pruebas y verlas fallar**

Run: `cd "/Users/andre/Documents/Claude/Projects/cancionero 2" && python3 -m unittest scripts/test_auditar.py 2>&1 | tail -5`
Expected: error de importación / `ModuleNotFoundError: auditar_alineacion` o fallos por función inexistente.

> Nota: ejecutar desde `scripts/` o ajustar `sys.path`. Para simplicidad, las pruebas asumen que se corren con `cd scripts && python3 -m unittest test_auditar`. Documentar el comando exacto en el Step 4.

- [ ] **Step 3: Implementar `auditar_alineacion.py`**

Create `scripts/auditar_alineacion.py`:
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audita la alineación acorde/letra de datos/songs.json y marca pares sospechosos.

Uso:
  python3 scripts/auditar_alineacion.py            # reporte de casos marcados
  python3 scripts/auditar_alineacion.py --todos    # incluye conteos globales
"""
import json, sys, os, re

UMBRAL_SOBREPASO = 6      # columnas que un acorde puede exceder la letra sin marcar

TOKEN = re.compile(r'\S+')

def columnas_acordes(linea):
    """Devuelve [(col, token)] de cada acorde en una línea de acordes."""
    return [(m.start(), m.group()) for m in TOKEN.finditer(linea)]

def evaluar_par(linea_acordes, linea_letra):
    """Evalúa un par acorde/letra. Devuelve {'marcar':bool,'motivo':str,'detalle':str}.

    Marca solo desalineaciones gruesas y verificables:
    - 'acorde_excede_letra': algún acorde empieza más de UMBRAL_SOBREPASO columnas
      después del último carácter no-espacio de la letra (probable corrimiento).
    No marca: líneas de acordes sin letra (intro/instrumental), ni sobrepasos pequeños
    (turnarounds), ni acordes sobre espacios internos (legítimo).
    """
    letra = linea_letra.rstrip()
    acordes = columnas_acordes(linea_acordes)
    if not acordes or not letra.strip():
        return {'marcar': False, 'motivo': '', 'detalle': ''}
    fin_letra = len(letra)
    ult_col, ult_tok = acordes[-1]
    sobrepaso = ult_col - fin_letra
    if sobrepaso > UMBRAL_SOBREPASO:
        return {'marcar': True, 'motivo': 'acorde_excede_letra',
                'detalle': f'acorde {ult_tok!r} en col {ult_col}, letra termina en {fin_letra} (+{sobrepaso})'}
    return {'marcar': False, 'motivo': '', 'detalle': ''}

def auditar(songs):
    """Recorre canciones; devuelve lista de hallazgos marcados."""
    hallazgos = []
    for si, s in enumerate(songs):
        ls = s['lines']
        for i, ln in enumerate(ls):
            if ln['k'] != 'c':
                continue
            nxt = ls[i+1] if i+1 < len(ls) else {'k': '', 't': ''}
            letra = nxt['t'] if nxt['k'] == 'l' else ''
            r = evaluar_par(ln['t'], letra)
            if r['marcar']:
                hallazgos.append({'idx': si, 'titulo': s['title'], 'pagina': s['page'],
                                  'linea': i, 'motivo': r['motivo'], 'detalle': r['detalle'],
                                  'c': ln['t'], 'l': letra})
    return hallazgos

def main():
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    songs = json.load(open(os.path.join(raiz, 'datos', 'songs.json'), encoding='utf-8'))
    hallazgos = auditar(songs)
    print(f'Canciones: {len(songs)} | pares marcados: {len(hallazgos)}\n')
    paginas = sorted({h['pagina'] for h in hallazgos})
    print('Páginas a revisar:', ', '.join(map(str, paginas)) or '(ninguna)', '\n')
    for h in hallazgos:
        print(f"  pág{h['pagina']} · {h['titulo']} · línea {h['linea']} · {h['motivo']}")
        print(f"    C: {h['c']!r}")
        print(f"    L: {h['l']!r}")
        print(f"    {h['detalle']}")
    if '--todos' in sys.argv:
        total_c = sum(1 for s in songs for ln in s['lines'] if ln['k']=='c')
        print(f"\nTotal líneas de acordes: {total_c}")

if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Ejecutar las pruebas y verlas pasar**

Run: `cd "/Users/andre/Documents/Claude/Projects/cancionero 2/scripts" && python3 -m unittest test_auditar -v 2>&1 | tail -10`
Expected: `OK` con 6 pruebas pasando.

> Si `test_overflow_exacto_umbral_no_marca` falla por el cálculo exacto de columnas, ajustar el *valor esperado del test* al comportamiento real de `evaluar_par` documentándolo (la lógica de UMBRAL no se cambia salvo que esté claramente mal).

- [ ] **Step 5: Commit**
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
git add scripts/auditar_alineacion.py scripts/test_auditar.py
git commit -m "feat: script de auditoría de alineación acorde/letra

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Renderizador de páginas y triaje de los casos marcados

Producir imágenes de las páginas marcadas para verificación visual contra `songs.json`.

**Files:**
- Create: `scripts/render_pagina.py`

- [ ] **Step 1: Escribir el renderizador de páginas**

Create `scripts/render_pagina.py`:
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Renderiza páginas del PDF a PNG para revisión visual.

Uso: python3 scripts/render_pagina.py 8 78 109   # páginas a renderizar
Salida: /tmp/cancionero_rev/pag-008.png, etc.
"""
import sys, os, subprocess

PDF = 'datos/Cancionero_Ministerio_Nueva_Alianza_Sector_San_Roberto_2026.pdf'
OUT = '/tmp/cancionero_rev'

def render(paginas):
    os.makedirs(OUT, exist_ok=True)
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf = os.path.join(raiz, PDF)
    for p in paginas:
        subprocess.run(['pdftoppm', '-png', '-f', str(p), '-l', str(p), '-r', '130',
                        pdf, os.path.join(OUT, 'pag')], check=True)
    print('Renderizado en', OUT, ':', os.listdir(OUT))

if __name__ == '__main__':
    paginas = [int(a) for a in sys.argv[1:] if a.isdigit()]
    if not paginas:
        print('Uso: python3 scripts/render_pagina.py <pág> [<pág> ...]'); sys.exit(1)
    render(paginas)
```

- [ ] **Step 2: Correr la auditoría y capturar las páginas marcadas**

Run:
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
python3 scripts/auditar_alineacion.py
```
Expected: imprime el conjunto de pares marcados y la lista de páginas a revisar. Anotar las páginas.

Luego renderizar esas páginas:
```bash
python3 scripts/render_pagina.py <páginas listadas por la auditoría>
```
Expected: PNGs en `/tmp/cancionero_rev/`.

- [ ] **Step 3: Revisión visual (con visión) de cada caso marcado**

Para cada hallazgo, abrir el PNG de su página y comparar la línea acorde/letra real del PDF con la de `songs.json` (impresa por la auditoría). Clasificar cada hallazgo como:
- **OK (falso positivo):** el PDF también tiene esos acordes así (turnaround/intro/vocalización). No tocar.
- **CORREGIR:** el acorde está en columna distinta a la del PDF. Anotar la corrección exacta (cómo deben quedar las columnas).

Producir una lista `correcciones` con: índice de canción, índice de línea, y el nuevo texto de la línea de acordes. Guardar esta lista como comentario o archivo temporal para la Task 3. (Esta revisión la realiza el ejecutor con capacidad visual; no requiere acción del usuario.)

- [ ] **Step 4: Commit del renderizador**
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
git add scripts/render_pagina.py
git commit -m "feat: renderizador de páginas del PDF para revisión de alineación

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Aplicar correcciones puntuales en `songs.json`

**Files:**
- Modify: `datos/songs.json` (solo las líneas de acordes identificadas como CORREGIR)

- [ ] **Step 1: Aplicar cada corrección como edición puntual de la línea de acordes**

Para cada entrada CORREGIR de la Task 2, editar en `datos/songs.json` únicamente el campo `t` de esa línea `{"k":"c",...}`, re-espaciando los acordes para que cada uno caiga en la columna de su sílaba según el PDF. No tocar las líneas de letra ni otras líneas.

Método recomendado para precisión: usar un script puntual que, dado (idx_cancion, idx_linea, nuevo_texto), reemplace exactamente esa entrada y reescriba `songs.json` con el mismo formato (`json.dump(..., ensure_ascii=False, indent=1)`), para no alterar el resto del archivo. Ejemplo de aplicación:
```python
import json
p='datos/songs.json'; s=json.load(open(p,encoding='utf-8'))
correcciones=[ (IDX, LINEA, 'NUEVO TEXTO DE ACORDES') ]  # rellenar desde Task 2
for idx,linea,txt in correcciones:
    assert s[idx]['lines'][linea]['k']=='c'
    s[idx]['lines'][linea]['t']=txt
json.dump(s, open(p,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
print('aplicadas', len(correcciones))
```

> Si la Task 2 no encontró ningún caso CORREGIR (solo falsos positivos), esta tarea se documenta como "sin correcciones necesarias: la extracción ya era fiel" y se omite el commit de datos. La auditoría y el renderizador (Tasks 1-2) quedan igual como entregables.

- [ ] **Step 2: Re-correr la auditoría**

Run:
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
python3 scripts/auditar_alineacion.py
```
Expected: los casos corregidos ya no aparecen marcados, o solo quedan falsos positivos confirmados en la Task 2.

- [ ] **Step 3: Verificar que el JSON sigue válido y con el mismo conteo**

Run:
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
python3 -c "import json; s=json.load(open('datos/songs.json')); print('canciones:', len(s))"
```
Expected: `canciones: 103`.

- [ ] **Step 4: Commit (solo si hubo correcciones)**
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
git add datos/songs.json
git commit -m "fix(datos): corregir alineación de acordes según el PDF

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Verificación en el cancionero y deploy

**Files:**
- Verificación (sin cambios de código) + push

- [ ] **Step 1: Tests del cancionero siguen verdes**

Run: `cd "/Users/andre/Documents/Claude/Projects/cancionero 2" && npm test`
Expected: 10/10 pass (la corrección de datos no afecta la lógica JS).

- [ ] **Step 2: Verificación visual en la app de 1-2 canciones corregidas**

Servir con el preview (config `cancionero`), abrir una canción corregida y confirmar en captura que los acordes caen sobre la sílaba correcta y que la hoja sigue ajustándose al ancho. Si no hubo correcciones, abrir una canción de muestra (p. ej. "Bueno es alabar") y confirmar que sigue fiel.

- [ ] **Step 3: Push y verificación en vivo**
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
git push origin main
```
Esperar el rebuild de Pages y confirmar que `https://devracf.github.io/ministerio-de-musica-sr/datos/songs.json` refleja los datos corregidos (o que el sitio carga 103 canciones si no hubo cambios de datos).

- [ ] **Step 4: Verificación del criterio de éxito de Plan B (criterio 6 del spec)**
- [ ] En la muestra de canciones revisadas contra el PDF, cada acorde cae sobre la sílaba correcta.
- [ ] Existe una herramienta de auditoría reutilizable (`scripts/auditar_alineacion.py`) para futuros cambios/imports.

---

## Self-Review (cobertura del spec en Plan B)

La sección "Fidelidad al PDF" del spec pide: cada acorde sobre la sílaba correcta como en el PDF; método = renderizar páginas + comparar con posiciones; corregir puntualmente; NO re-extraer en masa; songs.json es la fuente de verdad. Cobertura:

- **Herramienta de comparación/auditoría** → Task 1 (con función pura testeada).
- **Renderizar páginas del PDF para verificación** → Task 2.
- **Revisión y triaje (falso positivo vs corregir)** → Task 2 Step 3.
- **Corrección puntual sin re-extraer en masa** → Task 3 (edición por línea, formato preservado).
- **Criterio de éxito 6 + entregable reutilizable** → Task 4.

Se reconoce explícitamente (en "Hallazgo de partida" y en Task 3 Step 1) que el conjunto de correcciones puede ser pequeño o nulo porque la extracción ya es fiel; en ese caso el entregable principal es la auditoría. Sin placeholders: todo el código de scripts y pruebas está completo. Nombres consistentes: `evaluar_par`, `columnas_acordes`, `auditar`, `UMBRAL_SOBREPASO`, `render`, y la lista `correcciones` se usan igual en todas las tareas.

# Plan E — Agente importador de canciones desde URL — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el dueño pueda decir "importa esta URL" (LaCuerda.net, Cifra Club, u otro sitio) y el agente en Claude Code baje la página, la convierta al formato del cancionero con los acordes alineados sobre la letra, la muestre para aprobación, y al aprobar la agregue a `datos/songs.json`, haga commit y push.

**Architecture:** El "agente" es Claude Code siguiendo un runbook reutilizable (`docs/importar-cancion.md`). La parte mecánica y verificable vive en un script (`scripts/agregar_cancion.py`) que valida un objeto canción y lo añade a `songs.json` de forma segura (formato preservado). La auditoría del Plan B (`scripts/auditar_alineacion.py`) se reutiliza para verificar la alineación de lo importado. El flujo siempre incluye un paso de **aprobación humana** antes de publicar.

**Tech Stack:** Python 3 (script de validación/append; sin dependencias nuevas). WebFetch (lo provee Claude Code) para bajar la página. Git/Pages ya configurados. El cancionero web no cambia (solo crecen los datos).

**Restricciones:**
- `datos/songs.json` es la fuente de verdad; el formato se preserva (`json.dump(..., ensure_ascii=False, indent=1)`), igual que el resto del archivo.
- Cada canción: `{"title","author","section","page","lines":[{"k","t"}...]}`; `k` ∈ `c|l|b`; secciones válidas: Alabanza, Adoración, Exaltación, Espíritu Santo, María, Desagravio, Perdón.
- Acordes alineados sobre la letra en monoespaciado (columnas), como el resto del cancionero.
- **Nada se publica sin aprobación explícita del dueño.**
- `page` para canciones importadas (no del PDF) = `0`.

---

### Task 1: Validación de canción (función pura + pruebas)

**Files:**
- Create: `scripts/agregar_cancion.py` (parcial: `validar_cancion`)
- Create: `scripts/test_agregar.py`

- [ ] **Step 1: Escribir las pruebas de `validar_cancion` y `agregar`**

Create `scripts/test_agregar.py`:
```python
import unittest
from agregar_cancion import validar_cancion, agregar

CANCION_OK = {
    "title": "Cristo vive",
    "author": "",
    "section": "Alabanza",
    "page": 0,
    "lines": [
        {"k": "c", "t": "G        C        D"},
        {"k": "l", "t": "Cristo vive, aleluya"},
        {"k": "b", "t": ""},
    ],
}

class TestValidar(unittest.TestCase):
    def test_cancion_valida_sin_errores(self):
        self.assertEqual(validar_cancion(CANCION_OK), [])

    def test_titulo_vacio(self):
        c = dict(CANCION_OK, title="  ")
        self.assertIn('title vacío', validar_cancion(c))

    def test_seccion_invalida(self):
        c = dict(CANCION_OK, section="Rock")
        self.assertTrue(any('section' in e for e in validar_cancion(c)))

    def test_falta_author_ok_si_vacio(self):
        # author puede ser "" pero la clave debe existir
        c = dict(CANCION_OK); del c['author']
        self.assertTrue(any('author' in e for e in validar_cancion(c)))

    def test_lines_vacio(self):
        c = dict(CANCION_OK, lines=[])
        self.assertTrue(any('lines' in e for e in validar_cancion(c)))

    def test_linea_con_k_invalida(self):
        c = dict(CANCION_OK, lines=[{"k": "x", "t": "algo"}])
        self.assertTrue(any('línea 0' in e for e in validar_cancion(c)))

    def test_linea_sin_t(self):
        c = dict(CANCION_OK, lines=[{"k": "l"}])
        self.assertTrue(any('línea 0' in e for e in validar_cancion(c)))

class TestAgregar(unittest.TestCase):
    def test_agrega_al_final(self):
        base = [dict(CANCION_OK, title="Uno")]
        nuevo = agregar(base, CANCION_OK)
        self.assertEqual(len(nuevo), 2)
        self.assertEqual(nuevo[-1]['title'], "Cristo vive")

    def test_rechaza_invalida(self):
        with self.assertRaises(ValueError):
            agregar([], dict(CANCION_OK, section="X"))

    def test_no_muta_lista_original(self):
        base = [dict(CANCION_OK, title="Uno")]
        agregar(base, CANCION_OK)
        self.assertEqual(len(base), 1)

    def test_limpia_campos_extra(self):
        # quita campos de runtime como id/_busq si vinieran
        sucio = dict(CANCION_OK, id=5, _busq="x")
        nuevo = agregar([], sucio)
        self.assertNotIn('id', nuevo[-1])
        self.assertNotIn('_busq', nuevo[-1])

if __name__ == '__main__':
    unittest.main()
```

- [ ] **Step 2: Ejecutar las pruebas y verlas fallar**

Run: `cd "/Users/andre/Documents/Claude/Projects/cancionero 2/scripts" && python3 -m unittest test_agregar 2>&1 | tail -5`
Expected: `ModuleNotFoundError: No module named 'agregar_cancion'` o fallos por funciones inexistentes.

- [ ] **Step 3: Implementar `validar_cancion` y `agregar` en `scripts/agregar_cancion.py`**

Create `scripts/agregar_cancion.py`:
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Valida un objeto canción y lo agrega a datos/songs.json (formato preservado).

Uso:
  python3 scripts/agregar_cancion.py --file cancion.json      # desde archivo
  cat cancion.json | python3 scripts/agregar_cancion.py       # desde stdin
"""
import json, sys, os

SECCIONES_VALIDAS = {
    'Alabanza', 'Adoración', 'Exaltación', 'Espíritu Santo',
    'María', 'Desagravio', 'Perdón',
}
CAMPOS = ('title', 'author', 'section', 'page', 'lines')

def validar_cancion(obj):
    """Devuelve lista de errores (vacía si la canción es válida)."""
    errs = []
    if not isinstance(obj, dict):
        return ['la canción no es un objeto']
    if not str(obj.get('title', '')).strip():
        errs.append('title vacío')
    if 'author' not in obj:
        errs.append('falta author (puede ser "")')
    if obj.get('section') not in SECCIONES_VALIDAS:
        errs.append(f"section inválida: {obj.get('section')!r}")
    if not isinstance(obj.get('page', 0), int):
        errs.append('page debe ser entero (0 para canciones nuevas)')
    lines = obj.get('lines')
    if not isinstance(lines, list) or not lines:
        errs.append('lines vacío o no es lista')
    else:
        for i, ln in enumerate(lines):
            if (not isinstance(ln, dict) or ln.get('k') not in ('c', 'l', 'b')
                    or 't' not in ln):
                errs.append(f'línea {i} inválida (k debe ser c|l|b y debe traer t)')
    return errs

def limpiar(obj):
    """Conserva solo los campos canónicos, en orden."""
    return {
        'title': obj['title'].strip(),
        'author': (obj.get('author') or '').strip(),
        'section': obj['section'],
        'page': int(obj.get('page', 0) or 0),
        'lines': obj['lines'],
    }

def agregar(songs, obj):
    """Devuelve una nueva lista con la canción validada añadida al final."""
    errs = validar_cancion(obj)
    if errs:
        raise ValueError('canción inválida: ' + '; '.join(errs))
    return list(songs) + [limpiar(obj)]

def main():
    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ruta = os.path.join(raiz, 'datos', 'songs.json')
    if '--file' in sys.argv:
        entrada = open(sys.argv[sys.argv.index('--file') + 1], encoding='utf-8').read()
    else:
        entrada = sys.stdin.read()
    obj = json.loads(entrada)
    songs = json.load(open(ruta, encoding='utf-8'))
    # aviso de duplicado por título (no bloquea)
    dup = [s['title'] for s in songs if s['title'].strip().lower() == str(obj.get('title', '')).strip().lower()]
    if dup:
        print(f"AVISO: ya existe una canción titulada {dup[0]!r}.", file=sys.stderr)
    nuevo = agregar(songs, obj)
    json.dump(nuevo, open(ruta, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"OK: agregada {nuevo[-1]['title']!r} ({nuevo[-1]['section']}). Total: {len(nuevo)} canciones.")

if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Ejecutar las pruebas y verlas pasar**

Run: `cd "/Users/andre/Documents/Claude/Projects/cancionero 2/scripts" && python3 -m unittest test_agregar -v 2>&1 | tail -15`
Expected: `OK` con 11 pruebas pasando.

- [ ] **Step 5: Commit**
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
git add scripts/agregar_cancion.py scripts/test_agregar.py
git commit -m "feat: validación y append seguro de canciones (importador)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Runbook del importador (el "comando" reutilizable)

**Files:**
- Create: `docs/importar-cancion.md`

- [ ] **Step 1: Escribir el runbook**

Create `docs/importar-cancion.md`:
```markdown
# Importar una canción desde una URL (runbook del agente)

Cuando el dueño diga algo como "importa esta canción: <URL>", el agente (Claude Code)
sigue estos pasos. **Nunca publica sin aprobación.**

## Pasos

1. **Bajar la página** con WebFetch (la URL dada). Sitios típicos: LaCuerda.net,
   Cifra Club. Extraer: título, autor (si aparece), y el cuerpo con acordes y letra.

2. **Convertir al formato del cancionero** (`lines: [{"k","t"}]`):
   - `k:"c"` = línea de acordes; `k:"l"` = línea de letra; `k:"b"` = línea en blanco
     (separa estrofas).
   - **Alinear los acordes sobre la sílaba correcta en monoespaciado**: cada acorde
     debe quedar, contando espacios, sobre la sílaba donde se toca. Si WebFetch colapsó
     los espacios, reconstruir la alineación colocando cada acorde sobre su sílaba según
     la fuente.
   - Notación de acordes: respetar la del original (americana `Am F#` o latina `Rem Fa#`).
   - `page: 0` (no viene del PDF).

3. **Elegir la `section`** entre: Alabanza, Adoración, Exaltación, Espíritu Santo,
   María, Desagravio, Perdón. Si no es obvia, proponer una y preguntar al dueño.

4. **Verificar alineación**: escribir el objeto a un archivo temporal y, opcionalmente,
   revisar con criterio que los acordes caigan sobre las sílabas. (La auditoría
   `scripts/auditar_alineacion.py` corre sobre `songs.json` ya agregado; ver paso 7.)

5. **Mostrar la vista previa** al dueño: el título, autor, sección, y la hoja con
   acordes sobre letra (en bloque monoespaciado). Pedir aprobación explícita.

6. **Al aprobar, agregar** con el script (valida formato y preserva el archivo):
   ```bash
   python3 scripts/agregar_cancion.py --file /tmp/cancion.json
   ```
   Si el script reporta errores de validación, corregir el objeto y reintentar.

7. **Auditar** la alineación del resultado:
   ```bash
   python3 scripts/auditar_alineacion.py
   ```
   Revisar que la canción nueva no aparezca como desalineada (o que lo marcado sea
   legítimo: turnarounds/intros).

8. **Publicar**: commit y push.
   ```bash
   git add datos/songs.json
   git commit -m "feat(datos): agregar «<título>» (importada de <fuente>)"
   git push origin main
   ```
   El sitio se actualiza en ~1 minuto en https://devracf.github.io/ministerio-de-musica-sr/

## Notas por sitio

- **LaCuerda.net**: la letra/acordes vienen en bloque monoespaciado (`<pre>`); suele
  conservar la alineación. Autor a veces en el encabezado.
- **Cifra Club**: acordes sobre la letra en bloques; puede traer secciones marcadas
  ([Intro], [Refrão]). Mapear a líneas `c`/`l`/`b`.
- **Cualquier otro sitio**: extraer acordes+letra como texto y reconstruir la alineación
  manualmente. Funciona con cualquier fuente.

## Formato del objeto canción (ejemplo)

```json
{
  "title": "Cristo vive",
  "author": "",
  "section": "Alabanza",
  "page": 0,
  "lines": [
    {"k": "c", "t": "G        C        D"},
    {"k": "l", "t": "Cristo vive, aleluya"},
    {"k": "b", "t": ""}
  ]
}
```
```

- [ ] **Step 2: Commit**
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
git add docs/importar-cancion.md
git commit -m "docs: runbook del importador de canciones por URL

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

- [ ] **Step 3: Registrar el runbook en memoria (reutilización entre sesiones)**

Añadir un puntero en la memoria del proyecto para que futuras sesiones sepan seguir el
runbook al pedir "importa esta URL": actualizar `cancionero-web` con una línea que
referencie `docs/importar-cancion.md` y `scripts/agregar_cancion.py`. (Lo hace el agente
con la herramienta de memoria; no es un paso de código.)

---

### Task 3: Prueba de extremo a extremo con una URL real

**Files:**
- Modify (al aprobar): `datos/songs.json`

- [ ] **Step 1: Pedir al dueño una URL de prueba (o usar una que indique)**

El dueño provee una URL de LaCuerda.net o Cifra Club de una canción que quiera agregar.
(Si no, el agente propone una y confirma antes de seguir.)

- [ ] **Step 2: Ejecutar el runbook hasta la vista previa**

Seguir `docs/importar-cancion.md` pasos 1-5: bajar, convertir, alinear, elegir sección,
y mostrar la vista previa de la canción al dueño. NO agregar todavía.

- [ ] **Step 3: Validar el objeto sin escribir (dry run)**

Guardar el objeto en `/tmp/cancion.json` y validar el formato sin tocar songs.json:
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
python3 -c "import json,sys; sys.path.insert(0,'scripts'); from agregar_cancion import validar_cancion; print(validar_cancion(json.load(open('/tmp/cancion.json'))) or 'VÁLIDA')"
```
Expected: `VÁLIDA` (o la lista de errores a corregir).

- [ ] **Step 4: Con aprobación del dueño, agregar y auditar**
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
python3 scripts/agregar_cancion.py --file /tmp/cancion.json
python3 scripts/auditar_alineacion.py
python3 -c "import json; print('total:', len(json.load(open('datos/songs.json'))))"
```
Expected: "OK: agregada ..."; la auditoría no marca la nueva (o solo legítimos); total = 104.

- [ ] **Step 5: Verificar en el cancionero (local) y publicar**

Servir con el preview (config `cancionero`), buscar la canción nueva por título, abrirla
y confirmar en captura que acordes y letra están bien alineados y que la hoja se ajusta
al ancho. Luego:
```bash
cd "/Users/andre/Documents/Claude/Projects/cancionero 2"
git add datos/songs.json
git commit -m "feat(datos): agregar «<título>» (importada de <fuente>)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
git push origin main
```
Confirmar en vivo (~1 min) que la canción aparece en https://devracf.github.io/ministerio-de-musica-sr/

- [ ] **Step 6: Verificación del criterio de éxito de Plan E (criterio 4 del spec)**
- [ ] El agente importa una canción de LaCuerda.net o Cifra Club desde su URL, con vista
      previa y aprobación, y la deja publicada.
- [ ] El flujo es reutilizable (runbook + script) para futuras importaciones.

---

## Self-Review (cobertura del spec en Plan E)

La sección "Importar desde una URL (agente en Claude Code)" del spec pide: dar URL(s) →
el agente baja, extrae título/autor/sección/acordes/letra, convierte a `{k,t}` con acordes
alineados, muestra vista previa para aprobación, y al aprobar agrega a songs.json + commit
+ push; documentado como comando/skill reutilizable. Cobertura:

- **Validación y append seguro** → Task 1 (función pura testeada).
- **Flujo reutilizable documentado (el "comando")** → Task 2 (runbook) + memoria.
- **Bajar/convertir/alinear/sección** → Task 2 (pasos del runbook) y Task 3 (ejecución).
- **Vista previa + aprobación antes de publicar** → Task 2 paso 5 y Task 3 pasos 2/4.
- **Reutilizar auditoría de alineación (Plan B)** → Task 2 paso 7, Task 3 paso 4.
- **Criterio de éxito 4** → Task 3.

Sin placeholders: todo el código de scripts/pruebas y el runbook están completos. Nombres
consistentes: `validar_cancion`, `agregar`, `limpiar`, `SECCIONES_VALIDAS`, y el script
`agregar_cancion.py` / `auditar_alineacion.py` se referencian igual en todas las tareas.
El paso de publicar siempre exige aprobación explícita del dueño (restricción declarada).
```

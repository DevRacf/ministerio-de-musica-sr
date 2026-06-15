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
    dup = [s['title'] for s in songs
           if s['title'].strip().lower() == str(obj.get('title', '')).strip().lower()]
    if dup:
        print(f"AVISO: ya existe una canción titulada {dup[0]!r}.", file=sys.stderr)
    nuevo = agregar(songs, obj)
    json.dump(nuevo, open(ruta, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f"OK: agregada {nuevo[-1]['title']!r} ({nuevo[-1]['section']}). "
          f"Total: {len(nuevo)} canciones.")

if __name__ == '__main__':
    main()

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
        total_c = sum(1 for s in songs for ln in s['lines'] if ln['k'] == 'c')
        print(f"\nTotal líneas de acordes: {total_c}")

if __name__ == '__main__':
    main()

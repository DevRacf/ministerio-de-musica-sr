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
    print('Renderizado en', OUT, ':', sorted(os.listdir(OUT)))

if __name__ == '__main__':
    paginas = [int(a) for a in sys.argv[1:] if a.isdigit()]
    if not paginas:
        print('Uso: python3 scripts/render_pagina.py <pág> [<pág> ...]'); sys.exit(1)
    render(paginas)

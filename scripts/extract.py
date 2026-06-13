#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extrae canciones del cancionero PDF a JSON estructurado."""
import json, re, statistics
import pdfplumber

PDF = 'datos/Cancionero_Ministerio_Nueva_Alianza_Sector_San_Roberto_2026.pdf'

SECTIONS = [
    (6,   'Alabanza'),
    (37,  'Adoración'),
    (66,  'Exaltación'),
    (100, 'Espíritu Santo'),
    (119, 'María'),
    (125, 'Desagravio'),
    (128, 'Perdón'),
]
DIVIDER_PAGES = {p for p, _ in SECTIONS}
TEAL = (0.0588, 0.278, 0.38)
BLUE = (0.129, 0.369, 0.6)
UNIT = 5.4          # ancho de carácter de referencia (Courier 9pt)
COL_SPLIT = 300.0   # división de columnas
LEFT_BASE = 70.0
RIGHT_BASE = 320.0
FOOTER_Y = 690.0

ROOT = r"(?:[A-G](?:##?|bb?)?|(?:Do|Re|Mi|Fa|Sol|La|Si)[#b]?)"
QUAL = r"(?:maj|min|sus|dim|aug|add|m|M|°)?\d{0,2}(?:sus\d?|add\d{0,2}|maj\d{0,2})?"
CHORD_TOKEN = re.compile(
    r"^\(?\/{0,4}" + ROOT + QUAL +
    r"(?:\((?:[b#]?\d+|" + ROOT + QUAL + r")\))?"
    r"(?:/" + ROOT + r")?\)?[\/\-–]{0,4}[\*']?$"
)
AMBIG = re.compile(r"^(Do|Re|Mi|Fa|Sol|La|Si)$")
SEQ_TOKEN = re.compile(r"^[A-G][#b]?(?:m|M)?\d{0,2}(?:[-–][A-G][#b]?(?:m|M)?\d{0,2})+$")
MARKERS = {'x2','x3','x4','X2','X3','X4','(x2)','(x3)','(x4)','-','–','//','////','|',
           'N.C.','(bis)','bis','Intro:','Intro','Final:','Coro:','Puente:','*'}

def is_chord_token(tok):
    return tok in MARKERS or bool(CHORD_TOKEN.match(tok))

def is_chord_text(text):
    toks = text.split()
    if not toks:
        return False
    n_match = n_unambig = n_ambig = 0
    for t in toks:
        if t in MARKERS or SEQ_TOKEN.match(t):
            n_match += 1
            n_unambig += 1
        elif CHORD_TOKEN.match(t):
            n_match += 1
            if AMBIG.match(t):
                n_ambig += 1
            else:
                n_unambig += 1
    if n_match / len(toks) < 0.75:
        return False
    # evitar falsos positivos con palabras como "La", "Mi", "Si", "Sol"
    if n_unambig == 0:
        return len(toks) == 1 and n_ambig == 1
    return True

def color_close(c, ref, tol=0.05):
    if not isinstance(c, (tuple, list)) or len(c) != 3:
        return False
    return all(abs(a - b) <= tol for a, b in zip(c, ref))

def line_meta(chars):
    """Devuelve (es_titulo, frac_azul, frac_italic) de una línea."""
    vis = [c for c in chars if c['text'].strip()]
    if not vis:
        return False, 0, 0
    title = any(c['size'] >= 13 and color_close(c.get('non_stroking_color'), TEAL) for c in vis)
    blue = sum(1 for c in vis if color_close(c.get('non_stroking_color'), BLUE)) / len(vis)
    ital = sum(1 for c in vis if 'Italic' in c['fontname']) / len(vis)
    return title, blue, ital

def build_line_text(words, base):
    """Reconstruye la línea colocando cada palabra en su columna de caracteres."""
    out = []
    pos = 0
    for w in sorted(words, key=lambda x: x['x0']):
        col = max(round((w['x0'] - base) / UNIT), pos + (1 if pos else 0))
        out.append(' ' * (col - pos))
        out.append(w['text'])
        pos = col + len(w['text'])
    return ''.join(out).rstrip()

def page_lines(page):
    """Extrae líneas clasificadas de una página, en orden de lectura (col izq, col der)."""
    chars = [c for c in page.chars if c['top'] < FOOTER_Y]
    # agrupar por renglón
    rows = {}
    for c in chars:
        if not c['text'].strip():
            continue
        placed = False
        for top in list(rows):
            if abs(top - c['top']) <= 2.5:
                rows[top].append(c)
                placed = True
                break
        if not placed:
            rows[c['top']] = [c]

    # separar título (ancho completo) y columnas
    flow = []  # (orden, top, tipo, texto)
    col_rows = {'L': [], 'R': []}
    for top in sorted(rows):
        chs = sorted(rows[top], key=lambda c: c['x0'])
        text_join = ''.join(c['text'] for c in chs).strip()
        if re.fullmatch(r'\d+', text_join):
            continue  # número de página
        is_title, blue, ital = line_meta(chs)
        if is_title:
            side = 'L' if chs[0]['x0'] < COL_SPLIT else 'R'
            col_rows[side].append((top, chs, True))
            continue
        # dividir por columna
        L = [c for c in chs if c['x0'] < COL_SPLIT]
        R = [c for c in chs if c['x0'] >= COL_SPLIT]
        if L:
            col_rows['L'].append((top, L, False))
        if R:
            col_rows['R'].append((top, R, False))

    def words_from_chars(chs):
        ws = []
        cur = None
        for c in sorted(chs, key=lambda x: x['x0']):
            if cur and c['x0'] - cur['x1'] < 1.2:
                cur['text'] += c['text']
                cur['x1'] = c['x1']
            else:
                cur = {'text': c['text'], 'x0': c['x0'], 'x1': c['x1'],
                       'chars': []}
                ws.append(cur)
            cur['chars'].append(c)
        return ws

    def render_col(key, base):
        items = []
        prev_top = None
        for top, chs, is_t in sorted(col_rows[key], key=lambda r: r[0]):
            if is_t:
                items.append(('T', top, text_join_with_spaces(chs)))
                prev_top = top
                continue
            ws = words_from_chars(chs)
            text = build_line_text(ws, base)
            if not text.strip():
                continue
            _, blue, ital = line_meta(chs)
            kind = 'chord' if (blue >= 0.6 or (ital >= 0.6 and is_chord_text(text)) or is_chord_text(text)) else 'lyric'
            if kind == 'lyric' and ital >= 0.6:
                kind = 'italic'  # posible autor / nota
            if prev_top is not None and top - prev_top > 22:
                items.append(('B', top, ''))
            items.append((kind, top, text))
            prev_top = top
        return items

    seq = []
    for kind, top, text in render_col('L', LEFT_BASE):
        seq.append((kind, text))
    if col_rows['R']:
        seq.append(('B', ''))
        for kind, top, text in render_col('R', RIGHT_BASE):
            seq.append((kind, text))
    return seq, [f[1] for f in flow], rows

def text_join_with_spaces(chs):
    ws = []
    cur = ''
    last_x1 = None
    for c in sorted(chs, key=lambda x: x['x0']):
        if last_x1 is not None and c['x0'] - last_x1 > 1.5:
            cur += ' '
        cur += c['text']
        last_x1 = c['x1']
    return cur.strip()

CHORD_SEQ = re.compile(r"^[\[\]A-G#bmM0-9\s\-–/:().xX,]+$")
def looks_like_author(text):
    t = text.strip()
    if not t or len(t) >= 45:
        return False
    low = t.lower()
    if any(w in low for w in ('capo', 'tono', 'intro', 'cejilla', 'tiempo', 'acorde', 'ritmo')):
        return False
    if any(ch.isdigit() for ch in t):
        return False
    if CHORD_SEQ.match(t):
        return False
    if is_chord_text(t):
        return False
    return True

def section_for(page_no):
    sec = SECTIONS[0][1]
    for p, name in SECTIONS:
        if page_no >= p:
            sec = name
    return sec

def main():
    pdf = pdfplumber.open(PDF)
    songs = []
    current = None
    for i in range(6, len(pdf.pages)):  # desde página 7 (índice 6)... ojo: divisor pg6 es índice 5
        pass
    current = None
    for idx in range(5, len(pdf.pages)):  # páginas PDF 6..130
        page_no = idx + 1
        if page_no in DIVIDER_PAGES:
            continue
        page = pdf.pages[idx]
        seq, titles, _ = page_lines(page)
        # reordenar: el título puede haber quedado antes; recorremos seq
        j = 0
        for kind, text in seq:
            if kind == 'T':
                if current:
                    songs.append(current)
                current = {
                    'title': text,
                    'author': '',
                    'section': section_for(page_no),
                    'page': page_no,
                    'lines': [],
                }
            elif current is None:
                continue
            elif kind == 'B':
                if current['lines']:
                    current['lines'].append({'k': 'b', 't': ''})
            elif kind == 'italic' and not current['lines'] and not current['author'] \
                    and looks_like_author(text):
                current['author'] = text.strip()
            else:
                k = 'c' if kind == 'chord' else 'l'
                current['lines'].append({'k': k, 't': text})
    if current:
        songs.append(current)

    # limpiar: colapsar blanks repetidos, quitar blanks al inicio/fin
    for s in songs:
        cleaned = []
        for ln in s['lines']:
            if ln['k'] == 'b' and (not cleaned or cleaned[-1]['k'] == 'b'):
                continue
            cleaned.append(ln)
        while cleaned and cleaned[-1]['k'] == 'b':
            cleaned.pop()
        s['lines'] = cleaned

    with open('datos/songs.json', 'w', encoding='utf-8') as f:
        json.dump(songs, f, ensure_ascii=False, indent=1)

    print(f"Canciones extraídas: {len(songs)}")
    from collections import Counter
    print(Counter(s['section'] for s in songs))
    for s in songs[:5]:
        print('-', s['title'], '| autor:', s['author'] or '—', '| pág', s['page'], '| líneas', len(s['lines']))

if __name__ == '__main__':
    main()

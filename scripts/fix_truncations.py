#!/usr/bin/env python3
"""Fix truncated lines across all affected songs in datos/songs.json."""
import json, sys

with open('datos/songs.json', 'r', encoding='utf-8') as f:
    songs = json.load(f)

def fix_song(songs, title, fixes):
    """
    Apply fixes to a song.
    fixes is a list of:
      ('edit',   idx, field, new_value)  — set lines[idx][field] = new_value
      ('delete', idx)                     — delete lines[idx]
    Edits are applied first (before any index shifts).
    Deletions are applied in descending index order (so high indices first,
    avoiding cascade shifts).
    """
    for song in songs:
        if song['title'] == title:
            lines = song['lines']
            deletions = []
            for fix in fixes:
                if fix[0] == 'edit':
                    _, idx, field, val = fix
                    lines[idx][field] = val
                else:
                    deletions.append(fix[1])
            for idx in sorted(deletions, reverse=True):
                del lines[idx]
            return True
    print(f'WARNING: song not found: {title}', file=sys.stderr)
    return False

# ── 1. Canta, Canta ──────────────────────────────────────────────────────────
# Orphaned fragment block: lines 28-39
fix_song(songs, 'Canta, Canta', [
    ('edit', 7,  't', 'Canta, Canta,   oh hija de Sión regocíjate Israel'),
    ('edit', 9,  't', 'Canta y danza,   con todo el corazón  hija de Jerusalén.'),
    ('edit', 12, 't', 'Pues Hashem  quitó su castigo, tu enemigo huyó'),
    ('edit', 14, 't', 'Rey de Israel Adonai   en medio de ti, poderoso es,'),
    ('edit', 17, 't', 'Él se gozará, cantará por ti, callará de amor y te salvará.'),
    ('edit', 22, 't', 'Él se gozará, cantará por ti, callará de amor y te salvará.'),
    ('delete', 28), ('delete', 29), ('delete', 30), ('delete', 31),
    ('delete', 32), ('delete', 33), ('delete', 34), ('delete', 35),
    ('delete', 36), ('delete', 37), ('delete', 38), ('delete', 39),
])

# ── 2. Eres Todo Poderoso ─────────────────────────────────────────────────────
# Orphaned fragment block: lines 43-50
fix_song(songs, 'Eres Todo Poderoso', [
    ('edit', 8,  't', 'Mi única verdad está en ti, eres mi luz y mi salvación'),
    ('edit', 10, 't', 'Mi único amor eres Tú Señor y por siempre te alabaré'),
    ('edit', 22, 't', 'Mi única verdad está en ti, eres mi luz y mi salvación'),
    ('edit', 24, 't', 'Mi único amor eres Tú Señor y por siempre te alabaré'),
    ('delete', 43), ('delete', 44), ('delete', 45), ('delete', 46),
    ('delete', 47), ('delete', 48), ('delete', 49), ('delete', 50),
])

# ── 3. Grandes son tus obras ─────────────────────────────────────────────────
# Orphaned fragment block: lines 24-28 (line 29 'lara la la la la' is legitimate)
fix_song(songs, 'Grandes son tus obras', [
    ('edit', 2,  't', '  Grandes son tus obras,  maravillosas obras'),
    ('edit', 11, 't', '¿Quién no da - rá a tu nombre   Gloria y Honor?'),
    ('delete', 24), ('delete', 25), ('delete', 26), ('delete', 27), ('delete', 28),
])

# ── 4. Cantico de Moises ─────────────────────────────────────────────────────
# Orphaned fragment block: lines 25-33 (line 24 blank is a legitimate separator)
fix_song(songs, 'Cantico de Moises', [
    ('edit', 5,  't', 'Él es mi Dios y yo le he preparado Una habitación donde alabarle'),
    ('edit', 11, 't', 'El triunfó gloriosamente, caballos y carros en el mar arrojó.'),
    ('edit', 14, 't', 'Un gran guerrero es, al faraón y a sus hombres humilló.'),
    ('edit', 19, 't', '¿Quién como Tú, Señor?, haciendo maravillas y temido,'),
    ('edit', 20, 't', '¿Quién como Tú, Señor?, temido, alabado y glorioso en santidad.'),
    ('delete', 25), ('delete', 26), ('delete', 27), ('delete', 28),
    ('delete', 29), ('delete', 30), ('delete', 31), ('delete', 32), ('delete', 33),
])

# ── 5. No Puedo Dejar ────────────────────────────────────────────────────────
# Orphaned fragment block: lines 24-25
fix_song(songs, 'No Puedo Dejar', [
    ('edit', 21, 't', 'No puedo dejar de cantar, no puedo dejar de brincar,'),
    ('delete', 24), ('delete', 25),
])

# ── 6. La Bendición ──────────────────────────────────────────────────────────
# Chord lines 10, 16 truncated; lyric lines 34, 46 truncated.
# Orphaned block: lines 37-41 (line 42 ' Tu familia...' is legitimate).
# Trailing orphan 'yas' at line 66, preceded by blank at line 65.
fix_song(songs, 'La Bendición', [
    ('edit', 10, 't', '          Cadd9    G/B       G     [G - Cadd9]'),
    ('edit', 16, 't', '          Cadd9    G/B       G     [G - Cadd9]'),
    ('edit', 34, 't', '//Que te cubra con su gracia hasta mil generaciones'),
    ('edit', 46, 't', ' Su presencia te acompañe donde quiera que tu vayas'),
    # Lines 37-41: chord 'd9]', blank, chord 'd9]', blank, lyric 's'
    ('delete', 37), ('delete', 38), ('delete', 39), ('delete', 40), ('delete', 41),
    # Trailing orphan at original lines 65 (blank) and 66 ('yas')
    ('delete', 65), ('delete', 66),
])

# ── 7. 1000 Pedazos ──────────────────────────────────────────────────────────
# Many truncations in CORO 1 and CORO 2.
# Orphaned block 1: lines 36-53 (line 54 'PUENTE 2' is legitimate).
# Orphaned block 2: lines 79-90 (includes FINAL continuation at line 90).
fix_song(songs, '1000 Pedazos', [
    # VERSO 1
    ('edit', 4,  't', 'A veces das y a veces quitas, tu voluntad puede doler'),
    ('edit', 8,  't', 'El mundo quita y no perdona, y soy culpable yo también'),
    # CORO 1
    ('edit', 22, 't', 'Tu verdad siempre me ha cuidado, aun cuando he dudado'),
    ('edit', 24, 't', 'Y si estoy en mil pedazos es porque no es el final'),
    ('edit', 26, 't', 'Alma mía en mil pedazos nunca dejes de adorar,'),
    # VERSO 2
    ('edit', 32, 't', 'Un día más en el desierto donde me hablas en silencio'),
    ('edit', 33, 't', '       Bm          G        D        A'),   # chord missing 'A'
    # CORO 2
    ('edit', 64, 't', 'Tu verdad siempre me ha cuidado, aun cuando he dudado'),
    ('edit', 68, 't', 'Tu verdad siempre me ha cuidado, aun cuando he dudado.'),
    ('edit', 71, 't', 'Y si estoy en mil pedazos es porque no es el final'),
    ('edit', 72, 't', '      G          A          D    A/C#     Bm'),  # chord 'B'->'Bm'
    ('edit', 73, 't', 'Alma mía en mil pedazos nunca dejes de adorar,'),
    # FINAL chord line: append FINAL continuation
    ('edit', 77, 't', 'FINAL |Bm   G   |D    A   |Bm   G   |D    A   |A    G    |'),
    # Delete orphaned block 1 (lines 36-53)
    ('delete', 36), ('delete', 37), ('delete', 38), ('delete', 39),
    ('delete', 40), ('delete', 41), ('delete', 42), ('delete', 43),
    ('delete', 44), ('delete', 45), ('delete', 46), ('delete', 47),
    ('delete', 48), ('delete', 49), ('delete', 50), ('delete', 51),
    ('delete', 52), ('delete', 53),
    # Delete orphaned block 2 (lines 79-90)
    ('delete', 79), ('delete', 80), ('delete', 81), ('delete', 82),
    ('delete', 83), ('delete', 84), ('delete', 85), ('delete', 86),
    ('delete', 87), ('delete', 88), ('delete', 89), ('delete', 90),
])

# ── 8. Cantico del cordero ───────────────────────────────────────────────────
# Orphaned fragment block: lines 26-29
fix_song(songs, 'Cantico del cordero', [
    ('edit', 5,  't', '   Grandes son tus obras,  maravillosas obras,'),
    ('edit', 14, 't', '¿Quién no da – rá a tu Nombre   gloria y honor?'),
    ('delete', 26), ('delete', 27), ('delete', 28), ('delete', 29),
])

# ── 9. Dios manda lluvia ─────────────────────────────────────────────────────
# Orphaned fragment block: lines 24-32 (line 23 blank is a legitimate separator)
fix_song(songs, 'Dios manda lluvia', [
    ('edit', 1, 't', 'Dios manda   la lluvia derrama de tu Espíritu'),
    ('edit', 8, 't', 'Dios manda   la lluvia derrama de tu Espíritu'),
    ('delete', 24), ('delete', 25), ('delete', 26), ('delete', 27),
    ('delete', 28), ('delete', 29), ('delete', 30), ('delete', 31), ('delete', 32),
])

# ── 10. El Espíritu de Dios ──────────────────────────────────────────────────
# Orphaned fragment block: lines 40-44
fix_song(songs, 'El Espíritu de Dios', [
    ('edit', 7,  't', 'Está aquí para guiar, el Espíritu de Dios está aquí'),
    ('edit', 16, 't', 'Está aquí para guiar, el Espíritu de Dios está aquí'),
    ('delete', 40), ('delete', 41), ('delete', 42), ('delete', 43), ('delete', 44),
])

# ── 11. Ven y lléname ────────────────────────────────────────────────────────
# Orphaned fragment block: lines 24-25
fix_song(songs, 'Ven y lléname', [
    ('edit', 17, 't', 'Que  se pueda  respirar de tu amor  y tu perdón'),
    ('delete', 24), ('delete', 25),
])

with open('datos/songs.json', 'w', encoding='utf-8') as f:
    json.dump(songs, f, ensure_ascii=False, indent=2)

print('Done. All truncations fixed.')

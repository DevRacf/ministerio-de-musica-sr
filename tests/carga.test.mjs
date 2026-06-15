import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cargarPuro } from './helper.mjs';

const ctx = cargarPuro(`globalThis.inyectarDatos = inyectarDatos;`);
const { inyectarDatos } = ctx;

const SRC = 'antes\nconst EMBEDDED = null; /* ==EMBED-SLOT== */\ndespués';

test('incrusta el array en el slot EMBEDDED', () => {
  const out = inyectarDatos(SRC, [{title:'X'}]);
  assert.match(out, /const EMBEDDED = \[\{"title":"X"\}\]; \/\* ==EMBED-SLOT== \*\//);
});

test('conserva el resto del documento', () => {
  const out = inyectarDatos(SRC, []);
  assert.ok(out.startsWith('antes\n'));
  assert.ok(out.endsWith('\ndespués'));
});

test('lanza si no encuentra el slot', () => {
  assert.throws(() => inyectarDatos('sin slot', []), /slot EMBEDDED/);
});

test('el resultado vuelve a contener el slot (descarga idempotente del marcador)', () => {
  const out = inyectarDatos(SRC, [1,2,3]);
  assert.ok(out.includes('/* ==EMBED-SLOT== */'));
});

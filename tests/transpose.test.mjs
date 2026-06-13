import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cargarPuro } from './helper.mjs';

const ctx = cargarPuro(`
  globalThis.transponerLinea = transponerLinea;
`);
const { transponerLinea } = ctx;

test('sube un semitono en notación americana', () => {
  assert.equal(transponerLinea('C       G       Am', 1), 'C#       G#       A#m');
});

test('baja un semitono', () => {
  assert.equal(transponerLinea('D   A', -2), 'C   G');
});

test('transpone notación latina conservando el sistema', () => {
  assert.equal(transponerLinea('Do      Sol', 2), 'Re      La');
});

test('no toca las líneas de letra (texto que no son acordes)', () => {
  const letra = 'Cuando el Señor hiciere volver la cautividad';
  assert.equal(transponerLinea(letra, 3), letra);
});

test('n=0 devuelve la línea intacta', () => {
  assert.equal(transponerLinea('F#m7  B7', 0), 'F#m7  B7');
});

test('preserva el espaciado (la alineación no se corre con acordes de igual longitud)', () => {
  const out = transponerLinea('C   D   E', 1);
  assert.equal(out, 'C#   D#   F');
});

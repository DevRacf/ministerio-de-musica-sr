import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cargarPuro } from './helper.mjs';

const ctx = cargarPuro(`
  globalThis.clasificarLinea = clasificarLinea;
  globalThis.textoALineas = textoALineas;
  globalThis.lineasATexto = lineasATexto;
  globalThis.limpiarSong = limpiarSong;
`);
const { clasificarLinea, textoALineas, lineasATexto, limpiarSong } = ctx;

// Los objetos vienen del contexto vm (otro realm); comparamos por estructura JSON
// en vez de deepEqual estricto (que exige igualdad de prototipos).
const igual = (a, b) => assert.equal(JSON.stringify(a), JSON.stringify(b));

test('clasifica una línea de acordes como c', () => {
  assert.equal(clasificarLinea('Em7        Bm   G/B'), 'c');
});
test('clasifica una línea de letra como l', () => {
  assert.equal(clasificarLinea('Si te tengo a ti, lo tengo todo'), 'l');
});
test('vocalización "La, ra la" es letra, no acordes', () => {
  assert.equal(clasificarLinea('La, ra la la la la la la'), 'l');
});
test('textoALineas separa acordes, letra y blancos', () => {
  const r = textoALineas('G   C\nHola mundo\n\nfin');
  igual(r, [
    {k:'c', t:'G   C'},
    {k:'l', t:'Hola mundo'},
    {k:'b', t:''},
    {k:'l', t:'fin'},
  ]);
});
test('textoALineas recorta blancos al inicio y final', () => {
  const r = textoALineas('\n\nHola\n\n');
  igual(r, [{k:'l', t:'Hola'}]);
});
test('lineasATexto es inverso de textoALineas para contenido típico', () => {
  const txt = 'G   C\nHola\n\nDm\nadiós';
  assert.equal(lineasATexto(textoALineas(txt)), txt);
});
test('limpiarSong quita id y _busq', () => {
  const s = {title:'X', author:'', section:'Alabanza', page:0, lines:[], id:3, _busq:'x'};
  igual(limpiarSong(s), {title:'X', author:'', section:'Alabanza', page:0, lines:[]});
});

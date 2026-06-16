import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cargarPuro } from './helper.mjs';

const ctx = cargarPuro(`
  globalThis.resolverMix = resolverMix;
  globalThis.moverEnLista = moverEnLista;
  globalThis.inyectarDatos = inyectarDatos;
`);
const { resolverMix, moverEnLista, inyectarDatos } = ctx;
const igual = (a, b) => assert.equal(JSON.stringify(a), JSON.stringify(b));
const songs = [{title:'Pues tú glorioso'},{title:'Hay gran voz'},{title:'Grande es el Señor'}];

test('resolverMix mapea títulos a índices', () => {
  igual(resolverMix({songs:['Hay gran voz','Pues tú glorioso']}, songs),
        [{pos:0,title:'Hay gran voz',idx:1},{pos:1,title:'Pues tú glorioso',idx:0}]);
});
test('resolverMix marca no encontrada con idx null', () => {
  igual(resolverMix({songs:['No existe']}, songs), [{pos:0,title:'No existe',idx:null}]);
});
test('resolverMix ignora mayúsculas y espacios', () => {
  igual(resolverMix({songs:['  hay GRAN voz ']}, songs), [{pos:0,title:'  hay GRAN voz ',idx:1}]);
});
test('moverEnLista sube un elemento sin mutar', () => {
  const a=['a','b','c']; igual(moverEnLista(a,1,-1), ['b','a','c']); igual(a,['a','b','c']);
});
test('moverEnLista baja un elemento', () => {
  igual(moverEnLista(['a','b','c'],0,1), ['b','a','c']);
});
test('moverEnLista en el borde no cambia', () => {
  igual(moverEnLista(['a','b'],0,-1), ['a','b']);
});
test('inyectarDatos incrusta songs y mixes', () => {
  const src='X\nconst EMBEDDED = null; /* ==EMBED-SLOT== */\nconst EMBEDDED_MIXES = null; /* ==EMBED-MIXES== */\nY';
  const out=inyectarDatos(src,[{title:'A'}],[{name:'M',songs:['A']}]);
  assert.ok(out.includes('const EMBEDDED = [{"title":"A"}]'));
  assert.ok(out.includes('const EMBEDDED_MIXES = [{"name":"M","songs":["A"]}]'));
});

import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const __dirname = dirname(fileURLToPath(import.meta.url));
const HTML = join(__dirname, '..', 'index.html');

/**
 * Lee index.html, extrae el bloque entre los marcadores PURE-START y PURE-END
 * y lo ejecuta en un contexto aislado. Devuelve las funciones/const expuestas.
 */
export function cargarPuro(extra = '') {
  const src = readFileSync(HTML, 'utf8');
  const m = src.match(/\/\* ==PURE-START== \*\/([\s\S]*?)\/\* ==PURE-END== \*\//);
  if (!m) throw new Error('No se encontraron los marcadores ==PURE-START== / ==PURE-END== en index.html');
  const ctx = {};
  vm.createContext(ctx);
  vm.runInContext(m[1] + '\n' + extra, ctx);
  return ctx;
}

export function leerHtml() {
  return readFileSync(HTML, 'utf8');
}

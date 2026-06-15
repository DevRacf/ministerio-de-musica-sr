# Importar una canción desde una URL (runbook del agente)

Cuando el dueño diga algo como "importa esta canción: <URL>", el agente (Claude Code)
sigue estos pasos. **Nunca publica sin aprobación.**

## Pasos

1. **Bajar la página** con WebFetch (la URL dada). Sitios típicos: LaCuerda.net,
   Cifra Club. Extraer: título, autor (si aparece), y el cuerpo con acordes y letra.

2. **Convertir al formato del cancionero** (`lines: [{"k","t"}]`):
   - `k:"c"` = línea de acordes; `k:"l"` = línea de letra; `k:"b"` = línea en blanco
     (separa estrofas).
   - **Alinear los acordes sobre la sílaba correcta en monoespaciado**: cada acorde
     debe quedar, contando espacios, sobre la sílaba donde se toca. Si WebFetch colapsó
     los espacios, reconstruir la alineación colocando cada acorde sobre su sílaba según
     la fuente.
   - Notación de acordes: respetar la del original (americana `Am F#` o latina `Rem Fa#`).
   - `page: 0` (no viene del PDF).

3. **Elegir la `section`** entre: Alabanza, Adoración, Exaltación, Espíritu Santo,
   María, Desagravio, Perdón. Si no es obvia, proponer una y preguntar al dueño.

4. **Verificar alineación**: escribir el objeto a un archivo temporal y, opcionalmente,
   revisar con criterio que los acordes caigan sobre las sílabas. (La auditoría
   `scripts/auditar_alineacion.py` corre sobre `songs.json` ya agregado; ver paso 7.)

5. **Mostrar la vista previa** al dueño: el título, autor, sección, y la hoja con
   acordes sobre letra (en bloque monoespaciado). Pedir aprobación explícita.

6. **Al aprobar, agregar** con el script (valida formato y preserva el archivo):
   ```bash
   python3 scripts/agregar_cancion.py --file /tmp/cancion.json
   ```
   Si el script reporta errores de validación, corregir el objeto y reintentar.

7. **Auditar** la alineación del resultado:
   ```bash
   python3 scripts/auditar_alineacion.py
   ```
   Revisar que la canción nueva no aparezca como desalineada (o que lo marcado sea
   legítimo: turnarounds/intros).

8. **Publicar**: commit y push.
   ```bash
   git add datos/songs.json
   git commit -m "feat(datos): agregar «<título>» (importada de <fuente>)"
   git push origin main
   ```
   El sitio se actualiza en ~1 minuto en https://devracf.github.io/ministerio-de-musica-sr/

## Notas por sitio

- **LaCuerda.net**: la letra/acordes vienen en bloque monoespaciado (`<pre>`); suele
  conservar la alineación. Autor a veces en el encabezado.
- **Cifra Club**: acordes sobre la letra en bloques; puede traer secciones marcadas
  ([Intro], [Refrão]). Mapear a líneas `c`/`l`/`b`.
- **Cualquier otro sitio**: extraer acordes+letra como texto y reconstruir la alineación
  manualmente. Funciona con cualquier fuente.

## Formato del objeto canción (ejemplo)

```json
{
  "title": "Cristo vive",
  "author": "",
  "section": "Alabanza",
  "page": 0,
  "lines": [
    {"k": "c", "t": "G        C        D"},
    {"k": "l", "t": "Cristo vive, aleluya"},
    {"k": "b", "t": ""}
  ]
}
```

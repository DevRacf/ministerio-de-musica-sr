import unittest
from agregar_cancion import validar_cancion, agregar

CANCION_OK = {
    "title": "Cristo vive",
    "author": "",
    "section": "Alabanza",
    "page": 0,
    "lines": [
        {"k": "c", "t": "G        C        D"},
        {"k": "l", "t": "Cristo vive, aleluya"},
        {"k": "b", "t": ""},
    ],
}

class TestValidar(unittest.TestCase):
    def test_cancion_valida_sin_errores(self):
        self.assertEqual(validar_cancion(CANCION_OK), [])

    def test_titulo_vacio(self):
        c = dict(CANCION_OK, title="  ")
        self.assertIn('title vacío', validar_cancion(c))

    def test_seccion_invalida(self):
        c = dict(CANCION_OK, section="Rock")
        self.assertTrue(any('section' in e for e in validar_cancion(c)))

    def test_falta_author_ok_si_vacio(self):
        # author puede ser "" pero la clave debe existir
        c = dict(CANCION_OK); del c['author']
        self.assertTrue(any('author' in e for e in validar_cancion(c)))

    def test_lines_vacio(self):
        c = dict(CANCION_OK, lines=[])
        self.assertTrue(any('lines' in e for e in validar_cancion(c)))

    def test_linea_con_k_invalida(self):
        c = dict(CANCION_OK, lines=[{"k": "x", "t": "algo"}])
        self.assertTrue(any('línea 0' in e for e in validar_cancion(c)))

    def test_linea_sin_t(self):
        c = dict(CANCION_OK, lines=[{"k": "l"}])
        self.assertTrue(any('línea 0' in e for e in validar_cancion(c)))

class TestAgregar(unittest.TestCase):
    def test_agrega_al_final(self):
        base = [dict(CANCION_OK, title="Uno")]
        nuevo = agregar(base, CANCION_OK)
        self.assertEqual(len(nuevo), 2)
        self.assertEqual(nuevo[-1]['title'], "Cristo vive")

    def test_rechaza_invalida(self):
        with self.assertRaises(ValueError):
            agregar([], dict(CANCION_OK, section="X"))

    def test_no_muta_lista_original(self):
        base = [dict(CANCION_OK, title="Uno")]
        agregar(base, CANCION_OK)
        self.assertEqual(len(base), 1)

    def test_limpia_campos_extra(self):
        # quita campos de runtime como id/_busq si vinieran
        sucio = dict(CANCION_OK, id=5, _busq="x")
        nuevo = agregar([], sucio)
        self.assertNotIn('id', nuevo[-1])
        self.assertNotIn('_busq', nuevo[-1])

if __name__ == '__main__':
    unittest.main()

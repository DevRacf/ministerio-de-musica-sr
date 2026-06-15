import unittest
from auditar_alineacion import evaluar_par

class TestEvaluarPar(unittest.TestCase):
    def test_alineacion_normal_no_marca(self):
        # acorde dentro del ancho de la letra: ok
        r = evaluar_par('G          C         D', 'Bueno es alabar ¡Al Señor!, tu Nombre')
        self.assertFalse(r['marcar'])

    def test_turnaround_corto_no_marca(self):
        # acordes finales que sobrepasan poco (<=6) son legítimos
        r = evaluar_par('G          C         D     C   D', 'Bueno es alabar ¡Al Señor!, tu Nombre')
        self.assertFalse(r['marcar'])

    def test_sobrepaso_grande_marca(self):
        r = evaluar_par('A                          G   D   A', 'Glorioso es Él.')
        self.assertTrue(r['marcar'])
        self.assertEqual(r['motivo'], 'acorde_excede_letra')

    def test_sin_letra_no_marca(self):
        # línea de acordes sin letra debajo (intro): no es error de alineación
        r = evaluar_par('  Dm   Gm   C7', '')
        self.assertFalse(r['marcar'])

    def test_acorde_inicia_mas_alla_del_fin_marca(self):
        # primer acorde empieza pasado el final de una letra corta
        r = evaluar_par('                 Em', 'Amén')
        self.assertTrue(r['marcar'])
        self.assertEqual(r['motivo'], 'acorde_excede_letra')

    def test_overflow_exacto_umbral_no_marca(self):
        # exactamente 6 de sobrepaso: límite, no marca
        r = evaluar_par('C' + ' ' * 9 + 'D', 'abcd')   # 'D' en col 10, letra len 4 -> over 6
        self.assertFalse(r['marcar'])

if __name__ == '__main__':
    unittest.main()

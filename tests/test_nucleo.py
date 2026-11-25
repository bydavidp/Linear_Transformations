import unittest

import sympy as sp

from transformaciones_lineales import analyze, apply, parse_formula, parse_vector, x, y


class NucleoTests(unittest.TestCase):
    def test_lineal_y_matriz_rectangular(self):
        info = analyze('T(x,y) = (2x+y, x-y, sqrt(2)*x)', 2)
        self.assertTrue(info['linear'])
        self.assertEqual(info['matrix'], sp.Matrix([[2, 1], [1, -1], [sp.sqrt(2), 0]]))
        self.assertEqual(apply(info['expr'], info['vars'], parse_vector('1,2', 2)),
                         sp.Matrix([4, -1, sp.sqrt(2)]))

    def test_no_lineales(self):
        for formula in ('x^2,y', 'x+1,y', 'Abs(x),y', 'sin(x),y'):
            with self.subTest(formula=formula):
                self.assertFalse(analyze(formula, 2)['linear'])

    def test_dominio_antes_de_simplificar(self):
        for formula in ('x/x*x,y', '(x^2-1)/(x-1),y', 'x/(x+y),y'):
            with self.subTest(formula=formula):
                info = analyze(formula, 2)
                self.assertFalse(info['linear'])
                self.assertFalse(info['total'])
        info = analyze('x/x*x,y', 2)
        with self.assertRaises(ValueError):
            apply(info['expr'], info['vars'], sp.Matrix([0, 1]))

    def test_vectores_reales_y_potencias(self):
        self.assertEqual(parse_vector('(2^3, sqrt(2))', 2), sp.Matrix([8, sp.sqrt(2)]))
        for value in ('sqrt(-1),2', '1/0,2', 'log(0),2', 'x,2'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_vector(value, 2)

    def test_entrada_malformada(self):
        for formula in ('', 'x,,y', 'x,y,', '(x,y', 'x],y', 'x,z'):
            with self.subTest(formula=formula), self.assertRaises(ValueError):
                parse_formula(formula, (x, y))
        with self.assertRaises(ValueError):
            parse_vector('1,,2', 2)

    def test_entrada_no_es_codigo_python(self):
        for value in ("__import__('os').system('id'),2", '(1).__class__,2',
                      '[1,2][0],2', '2**1000000,2'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                parse_vector(value, 2)

    def test_dimension_invalida(self):
        with self.assertRaises(ValueError):
            analyze('x,y', 4)
        with self.assertRaises(ValueError):
            apply(sp.Matrix([x]), (x, y), sp.Matrix([1]))


if __name__ == '__main__':
    unittest.main()

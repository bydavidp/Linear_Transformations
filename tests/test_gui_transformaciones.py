import unittest
from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock, patch

from transformaciones_lineales import App


class GuiTests(unittest.TestCase):
    def make_app(self, formula='x, y', vector='1, 2', figure=''):
        app = SimpleNamespace(
            formula=Mock(get=Mock(return_value=formula)),
            dim=Mock(get=Mock(return_value=2)),
            vector=Mock(get=Mock(return_value=vector)),
            figure=Mock(get=Mock(return_value=figure)),
            output=Mock(), graph_frame=Mock(), draw=Mock(),
            last_report='resultado anterior', canvas=object(),
        )
        app.graph_frame.winfo_children.return_value = []
        app.invalidate_results = lambda: App.invalidate_results(cast(App, app))
        return app

    def test_figura_invalida_no_impide_analisis(self):
        app = self.make_app(figure='1, 2; 3')
        App.solve(cast(App, app))
        self.assertIn('EVALUACIÓN DEL VECTOR', app.last_report)
        self.assertIn('No se pudo procesar la figura', app.last_report)
        self.assertIsNone(app.draw.call_args.args[1])

    def test_figura_vacia_es_opcional(self):
        app = self.make_app()
        App.solve(cast(App, app))
        self.assertIn('No se indicó ninguna figura', app.last_report)

    def test_fallo_invalida_resultado_anterior(self):
        app = self.make_app(vector='1')
        with patch('transformaciones_lineales.messagebox.showerror') as error:
            App.solve(cast(App, app))
        self.assertIsNone(app.last_report)
        self.assertIsNone(app.canvas)
        error.assert_called_once()
        app.draw.assert_not_called()

    def test_error_al_guardar(self):
        app = self.make_app()
        with patch('transformaciones_lineales.filedialog.asksaveasfilename', return_value='/no/existe/archivo.txt'), \
             patch('transformaciones_lineales.messagebox.showerror') as error, \
             patch('transformaciones_lineales.messagebox.showinfo') as info:
            App.save_text(cast(App, app))
        error.assert_called_once()
        info.assert_not_called()

    def test_acerca_de_muestra_creditos(self):
        app = self.make_app()
        with patch('transformaciones_lineales.messagebox.showinfo') as info:
            App.mostrar_acerca_de(cast(App, app))
        info.assert_called_once_with(
            'Acerca de',
            'Creado por Jose David Palacios\nEstudiante de Ingeniería en Sistemas — Univalle',
            parent=app,
        )

    def test_interfaz_incluye_creditos_y_boton_acerca_de(self):
        app = self.make_app()
        app.preset = Mock()
        app.load_preset = Mock()
        app.on_dim_change = Mock()
        app.solve = Mock()
        app.save_text = Mock()
        app.mostrar_acerca_de = Mock()
        with patch('transformaciones_lineales.ttk.Style'), \
             patch('transformaciones_lineales.ttk.Frame'), \
             patch('transformaciones_lineales.ttk.Label') as label, \
             patch('transformaciones_lineales.ttk.Button') as button, \
             patch('transformaciones_lineales.ttk.Combobox'), \
             patch('transformaciones_lineales.ttk.Entry'), \
             patch('transformaciones_lineales.ttk.Panedwindow'), \
             patch('transformaciones_lineales.ttk.Scrollbar'), \
             patch('transformaciones_lineales.tk.Text'):
            App._make_ui(cast(App, app))
        self.assertTrue(any(
            call.kwargs.get('text') == 'Creado por Jose David Palacios\nEstudiante de Ingeniería en Sistemas — Univalle'
            for call in label.call_args_list
        ))
        self.assertTrue(any(
            call.kwargs.get('text') == 'Acerca de' and call.kwargs.get('command') == app.mostrar_acerca_de
            for call in button.call_args_list
        ))


if __name__ == '__main__':
    unittest.main()

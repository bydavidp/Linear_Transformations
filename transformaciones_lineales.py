#!/usr/bin/env python3
"""Laboratorio de transformaciones lineales para Álgebra Lineal.

Requisitos: sympy, matplotlib, numpy (Tkinter viene con muchas instalaciones de Python).
Uso: python transformaciones_lineales.py
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Sequence
import io
import tokenize

import sympy as sp
from sympy.calculus.util import continuous_domain

x, y, z = sp.symbols('x y z', real=True)
PARSE_GLOBALS = {'__builtins__': {}, 'Integer':sp.Integer, 'Float':sp.Float,
                 'Rational':sp.Rational, 'Add':sp.Add, 'Mul':sp.Mul, 'Pow':sp.Pow}
ALLOWED = {'x':x, 'y':y, 'z':z, 'sqrt':sp.sqrt, 'sin':sp.sin,
           'cos':sp.cos, 'pi':sp.pi, 'Abs':sp.Abs, 'exp':sp.exp,
           'log':sp.log, 'Rational':sp.Rational}


def _split_top(s: str, sep=','):
    """Divide por 'sep' solo al nivel superior de paréntesis/brackets."""
    bits, stack, cur = [], [], ''
    for ch in s:
        if ch in '([':
            stack.append(ch)
        elif ch in ')]':
            if not stack or stack.pop() != {')': '(', ']': '['}[ch]:
                raise ValueError('Paréntesis desbalanceados.')
        if ch == sep and not stack:
            bits.append(cur); cur = ''
        else:
            cur += ch
    if stack:
        raise ValueError('Paréntesis desbalanceados.')
    bits.append(cur)
    parts = [p.strip() for p in bits]
    if any(not part for part in parts):
        raise ValueError('Falta una componente entre las comas.')
    return parts


def _strip_outer(s: str):
    """Quita SOLO un paréntesis que envuelva toda la cadena, sin romper llamadas como sqrt(2)."""
    s = s.strip()
    while s.startswith('(') and s.endswith(')'):
        depth = 0
        for i, ch in enumerate(s):
            if ch == '(': depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0 and i != len(s) - 1:
                    return s  # el primer paréntesis no envuelve toda la cadena
        s = s[1:-1].strip()
    return s


def _parse_scalar(text, permitted):
    """Analiza solo aritmética y nombres conocidos; no es un sandbox de recursos."""
    from sympy.parsing.sympy_parser import (parse_expr, standard_transformations,
        implicit_multiplication_application, convert_xor)
    if len(text) > 500:
        raise ValueError('La expresión es demasiado larga.')
    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        for tok in tokens:
            if tok.type == tokenize.NAME and tok.string not in permitted:
                raise ValueError('Nombre no permitido: ' + tok.string)
            if tok.type == tokenize.NUMBER and (len(tok.string) > 20 or 'j' in tok.string.lower()):
                raise ValueError('Número no permitido.')
            if tok.type == tokenize.OP and tok.string not in ('+', '-', '*', '/', '**', '^', '(', ')', ','):
                raise ValueError('Operador no permitido: ' + tok.string)
            if tok.type not in (tokenize.NAME, tokenize.NUMBER, tokenize.OP,
                                tokenize.NEWLINE, tokenize.NL, tokenize.ENDMARKER):
                raise ValueError('Entrada no permitida.')
        result = parse_expr(text, local_dict=permitted, global_dict=PARSE_GLOBALS,
                            transformations=standard_transformations+(implicit_multiplication_application, convert_xor),
                            evaluate=False)
        if not isinstance(result, sp.Expr):
            raise ValueError('Se esperaba una expresión escalar.')
        for node in sp.preorder_traversal(result):
            if node.is_Pow and node.exp.is_number:
                exponent = node.exp.evalf()
                if exponent.is_real is not True or abs(exponent) > 1000:
                    raise ValueError('Exponente numérico fuera del límite permitido.')
        return result
    except (SyntaxError, tokenize.TokenError, TypeError, NameError, AttributeError) as exc:
        raise ValueError('Expresión inválida.') from exc


def _formula_parts(formula, variables):
    """Convierte '2*x + y, 3*y' o '(2*x+y,3*y)' en vector simbólico."""
    s = formula.strip()
    if s.startswith('T(') and '=' in s:
        s = s.split('=',1)[1].strip()
    s = _strip_outer(s)
    parts = _split_top(s)
    if not parts:
        raise ValueError('Escribe las componentes de T, separadas por comas.')
    permitted = {k:v for k,v in ALLOWED.items() if k not in ('x','y','z') or v in variables}
    parsed = []
    for part in parts:
        expr = _parse_scalar(part, permitted)
        if expr.free_symbols - set(variables):
            raise ValueError('Usa solamente las variables ' + ', '.join(map(str,variables)))
        if not expr.free_symbols and (expr.is_real is not True or expr.is_finite is not True):
            raise ValueError('Las componentes constantes deben ser números reales finitos.')
        parsed.append(expr)
    return parsed


def parse_formula(formula: str, variables: Sequence[sp.Symbol]):
    """Convierte componentes en un vector simbólico simplificado."""
    return sp.Matrix([sp.simplify(e) for e in _formula_parts(formula, variables)])


def analyze(formula: str, dimension: int):
    """Valida si T:R^n -> R^m es lineal: T(0)=0 y derivadas parciales constantes."""
    if dimension not in (2,3):
        raise ValueError('La entrada debe ser R² o R³.')
    vars_ = (x,y,z)[:dimension]
    original = _formula_parts(formula, vars_)
    # Comprobar antes de simplificar: x/x pierde el agujero en x=0.
    total = True
    for component in original:
        for var in vars_:
            try:
                if continuous_domain(component, var, sp.S.Reals) != sp.S.Reals:
                    total = False
            except (NotImplementedError, ValueError, TypeError):
                total = False
    expr = sp.Matrix(original)
    zero = sp.simplify(expr.subs({v:0 for v in vars_}))
    jac = expr.jacobian(vars_)
    # Teorema: T es lineal <=> T(0)=0 y toda derivada parcial de toda componente es constante.
    # (El método anterior con jac*v fallaba con casos como Abs(x), que sympy simplifica a lo mismo.)
    const_partials = all(sp.simplify(c).free_symbols == set() for row in jac.tolist() for c in row)
    linear = total and bool(const_partials) and all(t == 0 for t in zero) and all(
        c.is_real is True and c.is_finite is True for c in jac)
    return {'vars':vars_, 'expr':expr, 'matrix':jac if linear else None,
            'jacobian':jac,'zero':zero,'linear':linear, 'total':total}


def parse_vector(raw: str, n: int):
    raw = _strip_outer(raw)
    bits = _split_top(raw)
    if len(bits)!=n:
        raise ValueError(f'Escribe {n} coordenadas separadas por comas.')
    values=[]
    for b in bits:
        e = _parse_scalar(b, {k:v for k,v in ALLOWED.items() if k not in ('x','y','z')})
        if e.free_symbols:
            raise ValueError('Las coordenadas deben ser números, no variables.')
        e = sp.simplify(e)
        if e.is_real is not True or e.is_finite is not True:
            raise ValueError('Las coordenadas deben ser números reales finitos.')
        values.append(e)
    return sp.Matrix(values)


def apply(expr, vars_, vector):
    if len(vars_) != len(vector):
        raise ValueError('La dimensión del vector no coincide con la entrada.')
    substitutions = dict(zip(vars_, vector))
    for e in expr:
        for node in sp.preorder_traversal(e):
            if node.is_Pow and node.exp.is_negative is True:
                if sp.simplify(node.base.subs(substitutions, simultaneous=True)) == 0:
                    raise ValueError('La transformación no está definida en este vector.')
    result = [sp.simplify(e.subs(substitutions, simultaneous=True)) for e in expr]
    if any(e.is_real is not True or e.is_finite is not True for e in result):
        raise ValueError('La transformación no produce valores reales finitos en este vector.')
    return sp.Matrix(result)


def format_vec(vec):
    return '(' + ', '.join(str(sp.simplify(t)) for t in vec) + ')'


PRESETS = {
    'Escalamiento (2x, 3y)': ('2*x, 3*y',2),
    'Identidad (x, y)': ('x, y',2),
    'Rotación 90° (-y, x)': ('-y, x',2),
    'Rotación 180° (-x, -y)': ('-x, -y',2),
    'Reflexión eje X (x, -y)': ('x, -y',2),
    'Reflexión eje Y (-x, y)': ('-x, y',2),
    'Intercambiar ejes (y, x)': ('y, x',2),
    'Cizallamiento (x+y, y)': ('x+y, y',2),
    'Proyección eje X (x, 0)': ('x, 0',2),
    'No lineal (x², y)': ('x^2, y',2),
    'No lineal (x+1, y)': ('x+1, y',2),
    'No lineal (Abs(x), y)': ('Abs(x), y',2),
    'R³ a R² (x+z, y-2z)': ('x+z, y-2*z',3),
    'R² a R³ (x, y, x+y)': ('x, y, x+y',2),
}

CREDITOS = 'Creado por Jose David Palacios\nEstudiante de Ingeniería en Sistemas — Univalle'


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Laboratorio de Transformaciones Lineales')
        self.geometry('1130x790')
        self.minsize(850,650)
        self.configure(bg='#f2f5f9')
        self.formula=tk.StringVar(value='2*x, 3*y')
        self.dim=tk.IntVar(value=2)
        self.vector=tk.StringVar(value='2, 3')
        self.figure=tk.StringVar(value='0,0; 2,3; 4,0')
        self.preset=tk.StringVar(value='Escalamiento (2x, 3y)')
        self.plot_mode=tk.BooleanVar(value=True)
        self._make_ui()
        self.last_report=None
        for variable in (self.formula,self.dim,self.vector,self.figure):
            variable.trace_add('write',self.invalidate_results)
        self.solve()

    def _make_ui(self):
        style=ttk.Style(self)
        if 'clam' in style.theme_names(): style.theme_use('clam')
        style.configure('TButton',font=('Arial',10),padding=7)
        style.configure('TLabel',font=('Arial',10))
        style.configure('TEntry',padding=5)
        style.configure('Header.TLabel',font=('Arial',16,'bold'),foreground='#14223b',background='#f2f5f9')
        top=ttk.Frame(self,padding=16)
        top.pack(fill='x')
        ttk.Button(top,text='Acerca de',command=self.mostrar_acerca_de).pack(side='right',anchor='n')
        ttk.Label(top,text='Transformaciones lineales • Laboratorio de Álgebra',style='Header.TLabel').pack(anchor='w')
        ttk.Label(top,text='Analiza T: Rⁿ → Rᵐ, evalúa vectores y representa figuras en R².').pack(anchor='w',pady=(5,0))
        ttk.Label(top,text=CREDITOS,justify='left').pack(anchor='w',pady=(5,0))
        controls=ttk.Frame(self,padding=(16,2,16,10))
        controls.pack(fill='x')
        ttk.Label(controls,text='Ejemplos:').grid(row=0,column=0,sticky='w',pady=5)
        box=ttk.Combobox(controls,textvariable=self.preset,values=list(PRESETS),state='readonly',width=35)
        box.grid(row=0,column=1,columnspan=2,sticky='ew',padx=7)
        box.bind('<<ComboboxSelected>>', self.load_preset)
        ttk.Label(controls,text='Dimensión de entrada:').grid(row=0,column=3,sticky='e',padx=7)
        dimbox=ttk.Combobox(controls,textvariable=self.dim,values=('2','3'),state='readonly',width=4)
        dimbox.grid(row=0,column=4,sticky='w')
        dimbox.bind('<<ComboboxSelected>>', self.on_dim_change)
        ttk.Label(controls,text='T(x,y) o T(x,y,z) =').grid(row=1,column=0,sticky='w',pady=8)
        ttk.Entry(controls,textvariable=self.formula).grid(row=1,column=1,columnspan=4,sticky='ew',padx=7)
        ttk.Label(controls,text='Vector a evaluar:').grid(row=2,column=0,sticky='w',pady=8)
        ttk.Entry(controls,textvariable=self.vector).grid(row=2,column=1,columnspan=2,sticky='ew',padx=7)
        ttk.Label(controls,text='Vértices (separados por ;):').grid(row=2,column=3,sticky='e')
        ttk.Entry(controls,textvariable=self.figure).grid(row=2,column=4,sticky='ew',padx=7)
        ttk.Button(controls,text='Resolver y dibujar',command=self.solve).grid(row=3,column=1,sticky='ew',padx=7,pady=7)
        ttk.Button(controls,text='Guardar explicación TXT',command=self.save_text).grid(row=3,column=2,columnspan=2,sticky='ew',padx=7)
        ttk.Label(controls,text='Ejemplo: x^2, y  |  sqrt(2)*x - 3*sqrt(2)*y/2, sqrt(2)*x + 3*sqrt(2)*y/2').grid(row=4,column=0,columnspan=5,sticky='w',pady=4)
        controls.columnconfigure(1,weight=2)
        controls.columnconfigure(3,weight=2)
        content=ttk.Panedwindow(self,orient=tk.HORIZONTAL)
        content.pack(fill='both',expand=True,padx=16,pady=(0,15))
        result=ttk.Frame(content)
        content.add(result,weight=1)
        self.output=tk.Text(result,wrap='word',font=('Consolas',11),padx=14,pady=12,background='#fff',foreground='#182338')
        scroll=ttk.Scrollbar(result,command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        self.output.pack(side='left',fill='both',expand=True)
        scroll.pack(side='right',fill='y')
        graph=ttk.Frame(content)
        content.add(graph,weight=1)
        self.graph_frame=graph
        self.canvas=None

    def mostrar_acerca_de(self):
        messagebox.showinfo('Acerca de', CREDITOS, parent=self)

    def on_dim_change(self, event=None):
        self.vector.set('2, 3, 5' if self.dim.get()==3 else '2, 3')
        self.solve()

    def load_preset(self, event=None):
        self.formula.set(PRESETS[self.preset.get()][0])
        self.dim.set(PRESETS[self.preset.get()][1])
        self.vector.set('2, 3, 5' if self.dim.get()==3 else '2, 3')
        self.solve()

    def invalidate_results(self, *args):
        self.last_report=None
        self.output.delete('1.0','end')
        for child in self.graph_frame.winfo_children():
            child.destroy()
        self.canvas=None

    def solve(self):
        self.invalidate_results()
        try:
            n=self.dim.get()
            info=analyze(self.formula.get(),n)
            vec=parse_vector(self.vector.get(),n)
            transformed=apply(info['expr'],info['vars'],vec)
            rows=[]
            rows.append('1. TRANSFORMACIÓN PROPUESTA')
            rows.append(f"   T: R^{n} → R^{len(info['expr'])}")
            rows.append('   T(' + ', '.join(map(str,info['vars'])) + ') = ' + format_vec(info['expr']))
            rows.append('\n2. ¿ES LINEAL?')
            rows.append('   T(0) = ' + format_vec(info['zero']))
            rows.append('   Condición 1: T(0) = 0 → ' + ('SÍ' if all(v==0 for v in info['zero']) else 'NO'))
            rows.append('   Condición 2: T(u+v)=T(u)+T(v) y T(ku)=kT(u)')
            if info['linear']:
                rows.append('   Verificación: toda derivada parcial es constante y T(0)=0,')
                rows.append('   por lo que T(v)=A·v para una matriz A constante.')
                rows.append('   RESULTADO: SÍ ES LINEAL ✓')
                rows.append('   MATRIZ ASOCIADA A:')
                for i in range(info['matrix'].rows):
                    rows.append('   [ ' + '  '.join(str(c) for c in info['matrix'].row(i)) + ' ]')
                rows.append('   Por ello se cumplen aditividad y homogeneidad para TODOS los vectores.')
            else:
                if not info['total']:
                    rows.append('   RESULTADO: NO SE PUDO DETERMINAR LA LINEALIDAD EN TODO Rⁿ.')
                    rows.append('   No se ha podido establecer que la fórmula esté definida y sea continua en todo Rⁿ.')
                elif any(v!=0 for v in info['zero']):
                    rows.append('   RESULTADO: NO ES LINEAL ✗')
                    rows.append('   Contraejemplo: T(0) ≠ 0, requisito necesario de linealidad.')
                else:
                    rows.append('   RESULTADO: NO ES LINEAL ✗')
                    rows.append('   Existe al menos una derivada parcial no constante,')
                    rows.append('   así que T no puede escribirse como A·v con A constante.')
                    rows.append('   Esto impide que ambas propiedades se cumplan para todos los vectores.')
            rows.append('\n3. EVALUACIÓN DEL VECTOR')
            rows.append('   v = ' + format_vec(vec))
            rows.append('   T(v) = '+format_vec(transformed))
            rows.append('   Sustitución: ' + ', '.join(f'{var}={vec[i]}' for i,var in enumerate(info['vars'])))
            rows.append('\n4. TRANSFORMACIÓN DE LA FIGURA')
            vertices=None
            if n==2:
                try:
                    vertices=[parse_vector(s.strip(),2) for s in self.figure.get().split(';') if s.strip()]
                    if vertices:
                        figure_rows=[]
                        for i,p in enumerate(vertices):
                            t=apply(info['expr'],info['vars'],p)
                            figure_rows.append(f'   {chr(65+i%26)}: {format_vec(p)} → {format_vec(t)}')
                        rows.extend(figure_rows)
                        if len(info['expr'])!=2:
                            rows.append('   Gráfica no disponible: la salida no es R².')
                    else:
                        rows.append('   No se indicó ninguna figura.')
                except Exception as e:
                    vertices=None
                    rows.append('   No se pudo procesar la figura: ' + str(e))
            else:
                rows.append('   Para graficar figuras, selecciona entrada R² y salida R².')
            self.last_report='\n'.join(rows)
            self.output.delete('1.0','end')
            self.output.insert('1.0',self.last_report)
        except Exception as e:
            messagebox.showerror('Revisa los datos',str(e))
            return
        self.draw(info,vertices)

    def draw(self,info,vertices):
        for child in self.graph_frame.winfo_children():child.destroy()
        if len(info['vars'])!=2 or len(info['expr'])!=2 or not vertices:
            ttk.Label(self.graph_frame,text='La gráfica está disponible para T: R² → R².',padding=18).pack()
            return
        try:
            import matplotlib
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            from matplotlib.figure import Figure
            fig=Figure(figsize=(5,5),dpi=100)
            ax=fig.add_subplot(111)
            orig=[(float(sp.N(p[0])),float(sp.N(p[1]))) for p in vertices]
            dest=[apply(info['expr'],info['vars'],p) for p in vertices]
            targ=[(float(sp.N(p[0])),float(sp.N(p[1]))) for p in dest]
            if len(vertices)>=3:
                orig=orig+[orig[0]]
            ax.plot(*zip(*orig),'-o',color='#64748b',label='Original')
            if len(vertices)>1:
                samples=[]
                for a,b in zip(orig,orig[1:]):
                    for i in range(51):
                        t=i/50
                        point=[a[j]*(1-t)+b[j]*t for j in range(2)]
                        image=apply(info['expr'],info['vars'],point)
                        samples.append(tuple(float(sp.N(v)) for v in image))
                ax.plot(*zip(*samples),'-',color='#0d9488',label='Transformada')
                ax.plot(*zip(*targ),'o',color='#0d9488')
            else:
                ax.plot(*zip(*targ),'o',color='#0d9488',label='Transformada')
            for i,(a,b) in enumerate(targ[:len(vertices)]):
                ax.annotate(chr(65+i%26)+"'",(a,b),xytext=(5,6),textcoords='offset points',color='#087b72')
            ax.axhline(0,color='#555',linewidth=.8)
            ax.axvline(0,color='#555',linewidth=.8)
            ax.grid(alpha=.22)
            ax.set_aspect('equal',adjustable='datalim')
            ax.set_xlabel('x')
            ax.set_ylabel('y')
            ax.set_title('Figura original y transformada')
            ax.legend()
            fig.tight_layout()
            chart=FigureCanvasTkAgg(fig,master=self.graph_frame)
            chart.draw()
            chart.get_tk_widget().pack(fill='both',expand=True)
            self.canvas=chart
        except ImportError:
            ttk.Label(self.graph_frame,text='Instala matplotlib para ver las gráficas:\npip install matplotlib',padding=18).pack()
        except Exception as e:
            ttk.Label(self.graph_frame,text='No se pudo dibujar:\n'+str(e),padding=18).pack()

    def save_text(self):
        report = self.last_report
        if not report: return
        file=filedialog.asksaveasfilename(defaultextension='.txt',filetypes=[('Archivo de texto','*.txt')],initialfile='solucion_transformacion.txt')
        if file:
            try:
                with open(file,'w',encoding='utf8') as f:f.write(report)
            except (OSError, UnicodeError) as e:
                messagebox.showerror('Error al guardar',str(e))
                return
            messagebox.showinfo('Archivo guardado',f'Se guardó la explicación en:\n{file}')


if __name__=='__main__':
    App().mainloop()

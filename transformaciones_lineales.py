#!/usr/bin/env python3
"""Laboratorio de transformaciones lineales para Álgebra Lineal.

Requisitos: sympy, matplotlib, numpy (Tkinter viene con muchas instalaciones de Python).
Uso: python transformaciones_lineales.py
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Sequence

import sympy as sp

x, y, z = sp.symbols('x y z', real=True)
PARSE_GLOBALS = {'__builtins__': {}, 'Integer':sp.Integer, 'Float':sp.Float, 'Rational':sp.Rational, 'Symbol':sp.Symbol, 'factorial':sp.factorial}
ALLOWED = {'x':x, 'y':y, 'z':z, 'sqrt':sp.sqrt, 'sin':sp.sin,
           'cos':sp.cos, 'pi':sp.pi, 'Abs':sp.Abs, 'exp':sp.exp,
           'log':sp.log, 'Rational':sp.Rational}


def _split_top(s: str, sep=','):
    """Divide por 'sep' solo al nivel superior de paréntesis/brackets."""
    bits, depth, cur = [], 0, ''
    for ch in s:
        if ch in '([':
            depth += 1
        elif ch in ')]':
            depth -= 1
        if ch == sep and depth == 0:
            bits.append(cur); cur = ''
        else:
            cur += ch
    bits.append(cur)
    return [b for b in (p.strip() for p in bits) if b]


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


def parse_formula(formula: str, variables: Sequence[sp.Symbol]):
    """Convierte '2*x + y, 3*y' o '(2*x+y,3*y)' en vector simbólico."""
    from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application, convert_xor
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
        expr = parse_expr(part, local_dict=permitted, global_dict=PARSE_GLOBALS,
                          transformations=standard_transformations+(implicit_multiplication_application,convert_xor),
                          evaluate=True)
        if expr.free_symbols - set(variables):
            raise ValueError('Usa solamente las variables ' + ', '.join(map(str,variables)))
        parsed.append(sp.simplify(expr))
    return sp.Matrix(parsed)


def analyze(formula: str, dimension: int):
    """Valida si T:R^n -> R^m es lineal: T(0)=0 y derivadas parciales constantes."""
    if dimension not in (2,3):
        raise ValueError('La entrada debe ser R² o R³.')
    vars_ = (x,y,z)[:dimension]
    expr = parse_formula(formula, vars_)
    zero = sp.simplify(expr.subs({v:0 for v in vars_}))
    jac = expr.jacobian(vars_)
    # Teorema: T es lineal <=> T(0)=0 y toda derivada parcial de toda componente es constante.
    # (El método anterior con jac*v fallaba con casos como Abs(x), que sympy simplifica a lo mismo.)
    const_partials = all(sp.simplify(c).free_symbols == set() for row in jac.tolist() for c in row)
    linear = bool(const_partials) and all(t == 0 for t in zero)
    return {'vars':vars_, 'expr':expr, 'matrix':jac if linear else None,
            'jacobian':jac,'zero':zero,'linear':linear}


def parse_vector(raw: str, n: int):
    raw = _strip_outer(raw)
    bits = _split_top(raw)
    if len(bits)!=n:
        raise ValueError(f'Escribe {n} coordenadas separadas por comas.')
    from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
    values=[]
    for b in bits:
        e = parse_expr(b,local_dict={'sqrt':sp.sqrt,'pi':sp.pi},global_dict=PARSE_GLOBALS,
                       transformations=standard_transformations+(implicit_multiplication_application,))
        if e.free_symbols:
            raise ValueError('Las coordenadas deben ser números, no variables.')
        values.append(sp.simplify(e))
    return sp.Matrix(values)


def apply(expr, vars_, vector):
    return sp.Matrix([sp.simplify(e.subs(dict(zip(vars_,vector)))) for e in expr])


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
        ttk.Label(top,text='Transformaciones lineales • Laboratorio de Álgebra',style='Header.TLabel').pack(anchor='w')
        ttk.Label(top,text='Analiza T: Rⁿ → Rᵐ, evalúa vectores y representa figuras en R².').pack(anchor='w',pady=(5,0))
        controls=ttk.Frame(self,padding=(16,2,16,10))
        controls.pack(fill='x')
        ttk.Label(controls,text='Ejemplos:').grid(row=0,column=0,sticky='w',pady=5)
        box=ttk.Combobox(controls,textvariable=self.preset,values=list(PRESETS),state='readonly',width=35)
        box.grid(row=0,column=1,columnspan=2,sticky='ew',padx=7)
        box.bind('<<ComboboxSelected>>', self.load_preset)
        ttk.Label(controls,text='Dimensión de entrada:').grid(row=0,column=3,sticky='e',padx=7)
        dimbox=ttk.Combobox(controls,textvariable=self.dim,values=(2,3),state='readonly',width=4)
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

    def on_dim_change(self, event=None):
        self.vector.set('2, 3, 5' if self.dim.get()==3 else '2, 3')
        self.solve()

    def load_preset(self, event=None):
        self.formula.set(PRESETS[self.preset.get()][0])
        self.dim.set(PRESETS[self.preset.get()][1])
        self.vector.set('2, 3, 5' if self.dim.get()==3 else '2, 3')
        self.solve()

    def solve(self):
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
                rows.append('   RESULTADO: NO ES LINEAL ✗')
                if any(v!=0 for v in info['zero']):
                    rows.append('   Contraejemplo: T(0) ≠ 0, requisito necesario de linealidad.')
                else:
                    rows.append('   Existe al menos una derivada parcial no constante,')
                    rows.append('   así que T no puede escribirse como A·v con A constante.')
                    rows.append('   Esto impide que ambas propiedades se cumplan para todos los vectores.')
            rows.append('\n3. EVALUACIÓN DEL VECTOR')
            rows.append('   v = ' + format_vec(vec))
            rows.append('   T(v) = '+format_vec(transformed))
            rows.append('   Sustitución: ' + ', '.join(f'{var}={val}' for var,val in zip(info['vars'],vec)))
            rows.append('\n4. TRANSFORMACIÓN DE LA FIGURA')
            vertices=None
            if n==2:
                vertices=[parse_vector(s.strip(),2) for s in self.figure.get().split(';') if s.strip()]
                if not vertices: raise ValueError('Indica al menos un vértice.')
                for i,p in enumerate(vertices):
                    t=apply(info['expr'],info['vars'],p)
                    rows.append(f'   {chr(65+i%26)}: {format_vec(p)} → {format_vec(t)}')
                if len(info['expr'])!=2:
                    rows.append('   Gráfica no disponible: la salida no es R².')
            else:
                rows.append('   Para graficar figuras, selecciona entrada R² y salida R².')
            self.last_report='\n'.join(rows)
            self.output.delete('1.0','end')
            self.output.insert('1.0',self.last_report)
            self.draw(info,vertices)
        except Exception as e:
            messagebox.showerror('Revisa los datos',str(e))

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
                targ=targ+[targ[0]]
            ax.plot(*zip(*orig),'-o',color='#64748b',label='Original')
            ax.plot(*zip(*targ),'-o',color='#0d9488',label='Transformada')
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
        if not getattr(self,'last_report',None): return
        file=filedialog.asksaveasfilename(defaultextension='.txt',filetypes=[('Archivo de texto','*.txt')],initialfile='solucion_transformacion.txt')
        if file:
            with open(file,'w',encoding='utf8') as f:f.write(self.last_report)
            messagebox.showinfo('Archivo guardado',f'Se guardó la explicación en:\n{file}')


if __name__=='__main__':
    App().mainloop()

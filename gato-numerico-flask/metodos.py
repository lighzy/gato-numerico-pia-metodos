"""Generación de datos y cálculo de referencias, con el banco del libro.

Los problemas ya no se inventan: cada reto sale de
"Ejemplos_Gato_Numerico_Libro_Oralia.docx" (Métodos Numéricos, 2.ª ed.,
Zamora / Said / del Ángel), cuyos datos viven en problemas_libro.py.
Cada método tiene 3 plantillas (los 3 problemas del Word) y en el juego
solo se aleatorizan los huecos numéricos dentro de los rangos del libro;
el enunciado, el contexto, las unidades y lo que se pide no cambian.

Interfaz pública (igual que antes): CATALOGO, Reto con correcto()
(tolerancia ±0.001), generar(nombre, dificultad, r=random, variante=0)
y los generadores raices, interpolar, ajuste, integral, edo y sistema.
jugar.py funciona sin cambios.

- r = None devuelve el problema del Word con sus datos originales
  (variante 0, 1 o 2 elige la plantilla 1, 2 o 3); ver original().
- En las raíces se itera hasta la tolerancia del libro (como en el
  documento) y se reportan la primera y la última aproximación; por
  eso el nivel (d) no cambia los problemas de raíces: el nivel sí
  controla la carga en interpolación (puntos), integración (n) y EDO
  (pasos), como antes, y el cronómetro de cada nivel (25, 30 y 60 min
  en la versión Flask).
- "Bisección" se llama "Bisectriz" en el libro (§2.2); es el único
  nombre cambiado.

Extensión Flask (app.py): cada reto lleva además `comprobacion` y
`dato` (ver Reto). La comprobación por método es:
- Raíces: la primera aproximación nueva (x1; en Secante-gas, el Vr2
  del gas A; en Bisectriz, el primer punto medio).
- EDO Euler: y1 tras el primer paso. RK2/RK3/RK4/RK orden superior/
  RK4 por Simpson: k1, el primer incremento (h·f(t0, y0); en orden
  superior, h·y'0).
- Integración: la suma ponderada interior (sin los extremos).
- Interpolación: el primer término de la suma de interpolación
  (s·∆1, s·∇1, D1·(x−x1), y1·cociente de Lagrange); en Interpolación lineal, la
  pendiente (primera diferencia dividida) del inciso a), porque el
  primer término (Ln a1) ya viene escrito en el enunciado.
- Mínimos cuadrados: una suma de la tabla (Σx², Σxy o Σy) que el
  estudiante debe formar a mano para las ecuaciones normales.

Segunda comprobación (solo Difícil, `comprobacion2`): otro paso
intermedio real del MISMO método, distinto del primero, de modo que
los dos valores juntos no se obtienen con otro método:
- Raíces: la segunda aproximación nueva (x2, x3 o el segundo punto
  medio; en el gas, Vr3 del gas A o Vr2 del gas B). Si el método
  converge antes, el error del paso (Є1 o Є2).
- Interpolación: el segundo término de la suma (con ∆2, ∇2, D2, y2·cociente
  o la pendiente del inciso b) en Interpolación lineal).
- Mínimos cuadrados: otra suma de la tabla, distinta de la primera.
- Integración: la suma ponderada completa (con los extremos); en
  Newton-Cotes abierta, cuyos extremos pesan 0, la suma de los
  términos con peso positivo.
- EDO: y2 en Euler (o el predictor en Euler modificado y f(y1, t1)
  en Euler hacia atrás, cuando solo hay un paso); el segundo
  incremento en Runge-Kutta (m1, k2 o l).
"""
from dataclasses import dataclass
from math import prod, factorial, sin, exp, log, sqrt, atan, pi
import html as _html
import random
import re as _re

from problemas_libro import ANCLAS, GAS

CATALOGO = {
    "Ecuaciones no lineales": ["Newton-Raphson", "Secante", "Punto fijo", "Falsa posición", "Bisectriz"],
    "Interpolación": ["Newton hacia adelante", "Newton hacia atrás", "Diferencias divididas", "Lagrange", "Interpolación lineal"],
    "Mínimos cuadrados": ["Línea recta", "Lineal con función", "Cuadrática con función", "Cuadrática", "Cúbica"],
    "Integración": ["Newton-Cotes cerrada", "Newton-Cotes abierta", "Simpson 1/3", "Simpson 3/8", "Regla trapezoidal"],
    "EDO": ["Euler hacia adelante", "Euler modificado", "Euler hacia atrás", "Runge-Kutta de orden superior", "Runge-Kutta de segundo orden", "Runge-Kutta de tercer orden", "Runge-Kutta de cuarto orden", "RK4 por Simpson 1/3", "RK4 por Simpson 3/8"],
}

@dataclass
class Reto:
    texto: str
    campos: tuple
    valores: tuple
    revision: str
    # Comprobación (Flask): (etiqueta, valor). UN valor intermedio del
    # procedimiento a mano que prueba que el estudiante hizo el método y
    # que NUNCA repite ningún valor de `valores`. La API lo sirve como
    # primer campo ("comprobacion") y quita de los resultados el campo
    # que coincidía con él (p. ej. en raíces la "Primera aproximación
    # nueva" ES la comprobación, así que el único resultado que queda
    # es la última aproximación). `dato` es la línea de andamiaje con
    # solo los valores iniciales: nunca contiene la comprobación.
    comprobacion: tuple = ("Comprobación", 0.0)
    dato: str = ""
    # Segunda comprobación (Flask, solo Difícil): OTRO valor intermedio
    # del MISMO método, distinto de la comprobación 1. La API lo sirve
    # como segundo campo ("comprobacion2") solo en Difícil y quita de
    # los resultados el campo que coincidía con él, igual que con la
    # primera. Puede coincidir con un campo original (p. ej. y2 en
    # Euler): en ese caso ese campo deja de pedirse como resultado.
    # Tampoco aparece nunca en el enunciado, los datos ni el "Dato:".
    comprobacion2: tuple = ("Comprobación 2", 0.0)

    def correcto(self, datos):
        return len(datos) == len(self.valores) and all(abs(a-b) <= .001000001 for a,b in zip(datos,self.valores))

# ---------------------------------------------------------------------------
# Utilidades de formato y de aleatorización
# ---------------------------------------------------------------------------

def _g(x):
    """Número corto estilo :g (2.5, 0.3, −1.5)."""
    return f"{x:g}"

def _num(v):
    """Número sin decimales innecesarios (1.0 -> '1', 0.8 -> '0.8')."""
    if v == int(v):
        return str(int(v))
    return f"{v:g}"

def _opcion(r, opciones, ancla):
    """Con r=None devuelve el ancla (problema del Word); si no, elige con r."""
    if r is None:
        return ancla
    return r.choice(opciones)

def _con_signo(v, var="", primero=False):
    """Término con su signo, p. ej. ' + 0.8x²', ' − 3', 'x', '−x²'."""
    if v == 0:
        return ""
    if var and abs(v) == 1:
        nucleo = var
    else:
        nucleo = f"{_num(abs(v))}{var}"
    if primero:
        return ("−" if v < 0 else "") + nucleo
    return (" − " if v < 0 else " + ") + nucleo

def _cuadratica(a, b, c):
    """f(x) = a·x² + b·x + c, como la escribe el libro."""
    s = _con_signo(a, "x²", primero=True)
    s += _con_signo(b, "x")
    s += _con_signo(c, "")
    return s

def _lineal(a, b):
    """f'(x) = a·x + b, como la escribe el libro (la derivada de a·x²+b·x+c)."""
    return _con_signo(a, "x", primero=True) + _con_signo(b, "")

def _ecuacion_edo(A, B, C):
    """A·y' + B·y·t + C = 0, como la escribe el libro."""
    s = f"{_num(A)}y'"
    s += _con_signo(B, "yt")
    s += _con_signo(C, "")
    return s + " = 0"

def _resumen_raiz(seq, tol, etiqueta="x"):
    """seq = [x0, x1, ..., xn]; resume las iteraciones estilo libro."""
    n = len(seq) - 1
    def _item(i):
        return f"{etiqueta}{i} = {seq[i]:.9f} (Є = {abs(seq[i]-seq[i-1]):.9f})"
    if n <= 4:
        cuerpo = "; ".join(_item(i) for i in range(1, n + 1))
    else:
        cuerpo = "; ".join(_item(i) for i in (1, 2, 3)) + "; …; " + _item(n)
    e_fin = abs(seq[-1] - seq[-2])
    return (cuerpo + f". Se termina cuando Є = |{etiqueta}i+1 − {etiqueta}i|"
            f" ≤ {tol:g} (Є final = {e_fin:.9f}).")

def _comp2_secuencia(seq, i_comp, etiqueta_segunda, etiqueta_error, error):
    """Segunda comprobación a partir de una secuencia de iterados.

    seq[i_comp] es la comprobación 1; la segunda es seq[i_comp + 1]
    (la siguiente aproximación nueva) si existe y es distinta de la
    primera y de la última; si no (el método converge antes), el error
    del paso, que también es un valor intermedio real del método.
    """
    if len(seq) > i_comp + 1:
        v = seq[i_comp + 1]
        if v != seq[i_comp] and v != seq[-1]:
            return (etiqueta_segunda, v)
    return (etiqueta_error, error)

# ---------------------------------------------------------------------------
# Ecuaciones no lineales
# ---------------------------------------------------------------------------

def _naca_y(x):
    return 0.2969 * sqrt(x) - 0.126 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1015 * x ** 4

def _naca_yp(x):
    return 0.14845 / sqrt(x) - 0.126 - 0.7032 * x + 0.8529 * x ** 2 - 0.406 * x ** 3

def _newton_iter(f, fp, x0, tol, max_iter=100):
    seq = [x0]
    x = x0
    for _ in range(max_iter):
        xn = x - f(x) / fp(x)
        seq.append(xn)
        if abs(xn - x) <= tol:
            return seq
        x = xn
    return seq

def _newton(d, r, variante):
    tpl = ANCLAS["Newton-Raphson"][variante % 3]
    tol = tpl["tol"]
    x0 = tpl["x0"]
    if "espesor" in tpl:
        espesor = _opcion(r, [0.08, 0.09, 0.1, 0.11, 0.12], tpl["espesor"])
        y_obj = espesor / 2
        f = lambda x: _naca_y(x) - y_obj
        fp = _naca_yp
        texto = ("La configuración superficial de la aeronave NACA 0012 de longitud "
                 "de arco 1 m y con espesor máximo de 0.2 m está dada por: "
                 "y(x) = ±[0.2969√x − 0.126x − 0.3516x² + 0.2843x³ − 0.1015x⁴]. "
                 "Donde los signos más y menos se refieren a las superficies superior "
                 "e inferior, respectivamente. Determine x, donde el espesor del "
                 f"aparato es {_g(espesor)} m. Haga la tolerancia igual a {tol:g}. "
                 f"Empiece en x0 = {_g(x0)}.")
        revision = ("El espesor es 2·y(x); espesor "
                    f"{_g(espesor)} m significa y(x) = {_g(y_obj)}, es decir "
                    "f(x) = 0.2969√x − 0.126x − 0.3516x² + 0.2843x³ − 0.1015x⁴ "
                    f"− {_g(y_obj)} = 0. f'(x) = 0.14845/√x − 0.126 − 0.7032x "
                    "+ 0.8529x² − 0.406x³. ")
    else:
        a = _opcion(r, [0.6, 0.8, 1.0, 1.2], tpl["a"])
        b = _opcion(r, [0.5, 0.8, 1.0, 1.2, 1.5], tpl["b"])
        c = _opcion(r, [-2.0, -3.0, -4.0, -5.0, -6.0], tpl["c"])
        x0 = _opcion(r, [1.0, 2.0], x0)
        f = lambda x: a * x * x + b * x + c
        fp = lambda x: 2 * a * x + b
        texto = (f"Encuentre la raíz real de la ecuación f(x) = {_cuadratica(a, b, c)}, "
                 f"con f'(x) = {_lineal(2 * a, b)}. Empiece en x0 = {_g(x0)}. "
                 f"Itere hasta que Є = |xi+1 − xi| ≤ {tol:g}.")
        revision = (f"Se usa xi+1 = xi − f(xi)/f'(xi) con f(x) = {_cuadratica(a, b, c)} "
                    f"y f'(x) = {_lineal(2 * a, b)}, empezando en x0 = {_g(x0)}. ")
    seq = _newton_iter(f, fp, x0, tol)
    revision += _resumen_raiz(seq, tol)
    # Comprobación: x1, la primera aproximación nueva (se calcula a mano
    # con xi+1 = xi − f(xi)/f'(xi)).
    comp = ("x1 — primera aproximación nueva: x0 − f(x0)/f'(x0)", seq[1])
    # Segunda comprobación: x2, la siguiente aproximación nueva.
    comp2 = _comp2_secuencia(seq, 1, "x2 — segunda aproximación nueva: x1 − f(x1)/f'(x1)",
                             "Є1 — error del primer paso: |x1 − x0|", abs(seq[1] - seq[0]))
    dato = f"Dato: x0 = {_g(x0)}, tolerancia Є ≤ {tol:g}."
    return Reto(texto, ("Primera aproximación nueva", "Última aproximación (la raíz)"),
                (seq[1], seq[-1]), revision, comp, dato, comp2)

def _secante_iter(f, x0, x1, tol, max_iter=100):
    seq = [x0, x1]
    a, b = x0, x1
    for _ in range(max_iter):
        xn = b - f(b) * (b - a) / (f(b) - f(a))
        seq.append(xn)
        if abs(xn - b) <= tol:
            return seq
        a, b = b, xn
    return seq

def _secante(d, r, variante):
    tpl = ANCLAS["Secante"][variante % 3]
    tol = tpl["tol"]
    if "P" in tpl:
        P = _opcion(r, [1.0, 1.25, 1.5, 1.75, 2.0], tpl["P"])
        T = _opcion(r, [280.0, 290.0, 300.0, 310.0], tpl["T"])
        Vr0 = _opcion(r, [0.2, 0.3], tpl["Vr0"])
        Vr1 = _opcion(r, [0.4, 0.5, 0.6], tpl["Vr1"])
        tabla = "\n".join(
            f"Gas {g['gas']}   Pc = {_g(g['Pc'])} atm   Tc = {_g(g['Tc'])} K   "
            f"Vc = {_g(g['Vc'])} m³/kg" for g in GAS)
        texto = ("El estado de un gas se determina mediante sus variables de estado "
                 f"(P, V, T), para la siguiente ecuación de estado, determine el Volumen "
                 f"que ocupa el gas cuando P = {_g(P)} atm y T = {_g(T)} K. Si las "
                 "variables reducidas son resultado de la división del valor actual de "
                 "las variables de estado entre los valores críticos, determine el "
                 "Volumen para los dos gases que se consideran: "
                 "Vr³ − (1/3)(1 + 8Tr/Pr)Vr² + (3/Pr)Vr − 1/Pr = 0, con Vr = V/Vc, "
                 "Pr = P/Pc, Tr = T/Tc.\n" + tabla +
                 f"\nValores iniciales de la secante: Vr0 = {_g(Vr0)}, Vr1 = {_g(Vr1)}. "
                 f"Itere hasta que Є = |xi+1 − xi| ≤ {tol:g}.")
        revision_partes = []
        valores = []
        # Comprobación: la primera aproximación nueva Vr2 del gas A (se
        # calcula con la fórmula de la secante a partir de Vr0 y Vr1);
        # los resultados son los volúmenes V = Vr·Vc, distintos de Vr2.
        comp_vr2 = None
        seqs_gas = []
        for g in GAS:
            Pr = P / g["Pc"]
            Tr = T / g["Tc"]
            f = lambda Vr, Pr=Pr, Tr=Tr: (Vr ** 3 - (1 + 8 * Tr / Pr) / 3 * Vr ** 2
                                          + 3 / Pr * Vr - 1 / Pr)
            seq = _secante_iter(f, Vr0, Vr1, tol)
            seqs_gas.append(seq)
            if comp_vr2 is None:
                comp_vr2 = seq[2]
            Vr = seq[-1]
            V = Vr * g["Vc"]
            valores.append(V)
            revision_partes.append(
                f"Gas {g['gas']}: Pr = {Pr:.9f}, Tr = {Tr:.9f}. "
                + _resumen_raiz(seq, tol, etiqueta="Vr")
                + f" V = Vr·Vc = {Vr:.9f} × {_g(g['Vc'])} = {V:.9f} m³/kg.")
        comp = ("Vr2 — primera aproximación nueva (gas A)", comp_vr2)
        # Segunda comprobación: Vr3 del gas A (segunda iteración nueva);
        # si la secante converge en dos pasos, Vr2 del gas B.
        comp2 = _comp2_secuencia(seqs_gas[0], 2,
                                 "Vr3 — segunda aproximación nueva (gas A)",
                                 "Vr2 — primera aproximación nueva (gas B)",
                                 seqs_gas[1][2])
        dato = (f"Dato: P = {_g(P)} atm, T = {_g(T)} K, "
                f"Vr0 = {_g(Vr0)}, Vr1 = {_g(Vr1)}.")
        return Reto(texto, ("Volumen Gas A (m³/kg)", "Volumen Gas B (m³/kg)"),
                    tuple(valores), " ".join(revision_partes), comp, dato, comp2)
    a = _opcion(r, [0.8, 1.0, 1.2, 1.5, 2.0], tpl["a"])
    x0 = _opcion(r, [0.0, 0.5], tpl["x0"])
    x1 = _opcion(r, [1.0, 1.5], tpl["x1"])
    f = lambda x: exp(-x) - a * x
    texto = (f"Calcule la raíz de f(x) = e^(−x) − {_g(a)}x. "
             f"Empiece con x0 = {_g(x0)} y x1 = {_g(x1)}. "
             f"Itere hasta que Є = |xi+1 − xi| ≤ {tol:g}.")
    seq = _secante_iter(f, x0, x1, tol)
    revision = ("Se usa xi+1 = xi − f(xi)(xi − xi−1)/(f(xi) − f(xi−1)) "
                f"con x0 = {_g(x0)} y x1 = {_g(x1)}. " + _resumen_raiz(seq, tol))
    # Comprobación: x2, la primera aproximación nueva (x0 y x1 son datos;
    # x2 es el primer valor que se calcula).
    comp = ("x2 — primera aproximación nueva", seq[2])
    # Segunda comprobación: x3, la siguiente aproximación nueva.
    comp2 = _comp2_secuencia(seq, 2, "x3 — segunda aproximación nueva",
                             "Є2 — error del segundo paso: |x2 − x1|", abs(seq[2] - seq[1]))
    dato = (f"Dato: x0 = {_g(x0)}, x1 = {_g(x1)}, "
            f"tolerancia Є ≤ {tol:g}.")
    return Reto(texto, ("Primera aproximación nueva", "Última aproximación (la raíz)"),
                (seq[2], seq[-1]), revision, comp, dato, comp2)

def _punto_fijo(d, r, variante):
    tpl = ANCLAS["Punto fijo"][variante % 3]
    k = _opcion(r, [2.0, 2.5, 3.0, 3.5, 4.0], tpl["k"])
    C = _opcion(r, [1.5, 2.0, 2.5, 3.0, 3.5, 4.0], tpl["C"])
    x0 = _opcion(r, [0.0, 0.5, 1.0], tpl["x0"])
    tol = tpl["tol"]
    g = lambda x: (exp(x) - C) / k
    seq = [x0]
    x = x0
    for _ in range(300):
        xn = g(x)
        seq.append(xn)
        if abs(xn - x) <= tol:
            break
        x = xn
    texto = (f"Localizar la raíz de y = {_num(k)}x − e^x + {_num(C)}, la función se "
             "puede separar directamente y expresarse en la forma xi+1 = g(xi). "
             f"Empezar con un valor inicial x0 = {_g(x0)}. "
             f"Itere hasta que Є = |xi+1 − xi| ≤ {tol:g}.")
    revision = (f"Se despeja x = (e^x − {_num(C)})/{_num(k)} y se itera xi+1 = g(xi) "
                f"con x0 = {_g(x0)}. " + _resumen_raiz(seq, tol))
    # Comprobación: x1 = g(x0), la primera aproximación nueva.
    comp = ("x1 — primera aproximación nueva: g(x0)", seq[1])
    # Segunda comprobación: x2, la siguiente aproximación nueva.
    comp2 = _comp2_secuencia(seq, 1, "x2 — segunda aproximación nueva: g(x1)",
                             "Є1 — error del primer paso: |x1 − x0|", abs(seq[1] - seq[0]))
    dato = f"Dato: x0 = {_g(x0)}, tolerancia Є ≤ {tol:g}."
    return Reto(texto, ("Primera aproximación nueva", "Última aproximación (la raíz)"),
                (seq[1], seq[-1]), revision, comp, dato, comp2)

def _falsa_posicion(d, r, variante):
    tpl = ANCLAS["Falsa posición"][variante % 3]
    C = _opcion(r, [8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0,
                    17.0, 18.0, 19.0, 20.0, 22.0, 25.0], tpl["C"])
    tol = tpl["tol"]
    f = lambda x: x * exp(x) - C
    if r is None:
        a, b = tpl["a"], tpl["b"]
    else:
        # El corchete debe encerrar la raíz (f(a) < 0 < f(b)); si no, se adapta.
        a, b = r.choice([(1.0, 2.0), (0.0, 2.0), (1.0, 2.5),
                         (0.5, 2.0), (1.0, 3.0), (0.0, 3.0)])
        if not (f(a) < 0 < f(b)):
            a, b = (1.0, 2.0) if C <= 14 else (1.0, 3.0)
    seq = [a]
    for _ in range(100):
        x = a - f(a) * (b - a) / (f(b) - f(a))
        seq.append(x)
        if len(seq) > 2 and abs(seq[-1] - seq[-2]) <= tol:
            break
        if f(a) * f(x) <= 0:
            b = x
        else:
            a = x
    tabla = "; ".join(f"f({_g(x)}) = {f(x):.9f}" for x in (-2, -1, 0, 1, 2))
    texto = (f"Calcule la raíz para f(x) = x·e^x − {_g(C)}. "
             f"a = {_g(a)}, b = {_g(b)} (b fijo). "
             f"Itere hasta que Є = |xi+1 − xi| ≤ {tol:g}. Valores de apoyo: {tabla}.")
    revision = (f"Se usa x = a − f(a)(b − a)/(f(b) − f(a)) con a = {_g(a)} "
                f"y b = {_g(b)} fijo. " + _resumen_raiz(seq, tol))
    # Comprobación: x1, la primera aproximación nueva.
    comp = ("x1 — primera aproximación nueva", seq[1])
    # Segunda comprobación: x2, la siguiente aproximación nueva.
    comp2 = _comp2_secuencia(seq, 1, "x2 — segunda aproximación nueva",
                             "Є1 — error del primer paso: |x1 − x0|", abs(seq[1] - seq[0]))
    dato = (f"Dato: a = {_g(a)}, b = {_g(b)} (b fijo), "
            f"tolerancia Є ≤ {tol:g}.")
    return Reto(texto, ("Primera aproximación nueva", "Última aproximación (la raíz)"),
                (seq[1], seq[-1]), revision, comp, dato, comp2)

def _bisectriz_iter(f, a, b, tol, max_iter=200):
    seq = []
    for _ in range(max_iter):
        m = (a + b) / 2
        seq.append(m)
        if len(seq) > 1 and abs(seq[-1] - seq[-2]) <= tol:
            return seq
        if f(a) * f(m) <= 0:
            b = m
        else:
            a = m
    return seq

def _bisectriz(d, r, variante):
    tpl = ANCLAS["Bisectriz"][variante % 3]
    tol = tpl["tol"]
    if "p" in tpl:
        p = _opcion(r, [-6.0, -6.25, -6.5, -6.75, -7.0, -7.25, -7.5, -7.75, -8.0],
                    tpl["p"])
        C = _opcion(r, [1.0, 1.25, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0],
                    tpl["C"])
        a, b = tpl["a"], tpl["b"]
        if r is not None:
            b = r.choice([1.0, 1.5])
        f = lambda x: x ** 3 + p * x + C
        tabla = "; ".join(f"f({_g(x)}) = {f(x):.9f}" for x in range(-3, 4))
        texto = (f"En la gráfica de la función y = x³ {_con_signo(p, 'x')} "
                 f"{_con_signo(C, '')}. Cuando el valor entre los dos últimos sea "
                 f"igual a {tol:g} aquí se termina. Buscando x que es el punto medio "
                 f"entre a y b. Intervalo [{_g(a)}, {_g(b)}], Є = {tol:g}. "
                 f"Valores de apoyo: {tabla}.")
        seq = _bisectriz_iter(f, a, b, tol)
        revision = (f"Se usa x = (a + b)/2 en el intervalo [{_g(a)}, {_g(b)}]; "
                    f"f({_g(a)}) = {f(a):.9f} y f({_g(b)}) = {f(b):.9f}, hay cambio "
                    "de signo. " + _resumen_raiz(seq, tol))
        # Comprobación: x1 = (a + b)/2, el primer punto medio.
        comp = ("x1 — primer punto medio: (a + b)/2", seq[0])
        # Segunda comprobación: x2, el segundo punto medio.
        comp2 = _comp2_secuencia(seq, 0, "x2 — segundo punto medio",
                                 "Semi-intervalo inicial: (b − a)/2", (b - a) / 2)
        dato = f"Dato: intervalo [{_g(a)}, {_g(b)}], tolerancia Є = {tol:g}."
        return Reto(texto, ("Primera aproximación nueva", "Última aproximación (la raíz)"),
                    (seq[0], seq[-1]), revision, comp, dato, comp2)
    if "M" in tpl:
        M = _opcion(r, [1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0], tpl["M"])
        g = 9.81
        rhs = M * g / 1000
        f = lambda v: 1.4e-5 * v ** 1.5 + 1.15e-5 * v ** 2 - rhs
        a, b = tpl["a"], tpl["b"]
        while f(b) < 0 and b < 80:
            b += 10
        texto = (f"Un proyectil de M = {_g(M)} gm se ha lanzado en forma vertical al "
                 "aire y está descendiendo a su velocidad terminal. Dicha velocidad "
                 "se determina mediante la ecuación gM = Ddrag donde g es la gravedad "
                 "y M es la masa; esta ecuación se puede escribir después de evaluar "
                 "las constantes como: "
                 f"({_g(M)})(9.81)/1000 = 1.4×10⁻⁵·v^1.5 + 1.15×10⁻⁵·v². Donde v es "
                 "la velocidad terminal en m/seg. El primer término del lado derecho "
                 "representa la fuerza de fricción y el segundo la fuerza de la "
                 "presión. Determine la velocidad terminal mediante el método de "
                 f"bisectriz, con una tolerancia de {tol:g}. Intervalo de bisección "
                 f"[{_g(a)}, {_g(b)}] m/s.")
        seq = _bisectriz_iter(f, a, b, tol)
        revision = (f"Se define f(v) = 1.4×10⁻⁵·v^1.5 + 1.15×10⁻⁵·v² − {rhs:.9f}. "
                    f"f({_g(a)}) = {f(a):.9f} y f({_g(b)}) = {f(b):.9f}: hay cambio "
                    "de signo en [" + _g(a) + ", " + _g(b) + "]. "
                    + _resumen_raiz(seq, tol, etiqueta="v"))
        # Comprobación: v1 = (a + b)/2, el primer punto medio.
        comp = ("v1 — primer punto medio: (a + b)/2", seq[0])
        # Segunda comprobación: v2, el segundo punto medio.
        comp2 = _comp2_secuencia(seq, 0, "v2 — segundo punto medio",
                                 "Semi-intervalo inicial: (b − a)/2", (b - a) / 2)
        dato = (f"Dato: M = {_g(M)} gm, intervalo [{_g(a)}, {_g(b)}] m/s, "
                f"tolerancia = {tol:g}.")
        return Reto(texto, ("Primera aproximación nueva", "Última aproximación (la raíz)"),
                    (seq[0], seq[-1]), revision, comp, dato, comp2)
    V = _opcion(r, [800.0, 1000.0, 1200.0, 1400.0, 1500.0, 1600.0,
                    1800.0, 2000.0, 2200.0, 2500.0, 3000.0], tpl["V"])
    s = tpl["s"]
    Aprima = lambda r_: 4 * pi * (r_ + s) - 2 * V * (r_ + 2 * s) / r_ ** 3
    Area = lambda r_: 2 * pi * (r_ + s) ** 2 + 2 * V * (r_ + s) / r_ ** 2
    a, b = tpl["a"], tpl["b"]
    while Aprima(b) < 0 and b < 12:
        b += 1
    texto = (f"Se debe fabricar una lata en forma cilíndrica circular recta que "
             f"contenga {_g(V)} cm³. Las tapas de la parte superior y del fondo deben "
             f"tener un radio de {_g(s)} cm más que el radio de la lata para que el "
             "sobrante se utilice para sellar con la pared lateral. La hoja de "
             f"material con que se construye la pared lateral también debe ser de "
             f"{_g(s)} cm más grande que la circunferencia de la lata de modo que "
             "pueda hacerse un sello lateral. Calcule la cantidad mínima de material "
             "para fabricar esta lata. Sea h la altura del cilindro, r el radio del "
             f"volumen deseado y r + {_g(s)} el radio necesario para sellar la tapa. "
             f"V = {_g(V)} = πr²h; h = {_g(V)}/(πr²). A(r) = 2π(r + {_g(s)})² + "
             f"{_g(2 * V)}(r + {_g(s)})/r². Para encontrar el material mínimo se "
             "utiliza la derivada de la función a minimizar y se iguala a cero: "
             f"A'(r) = 4π(r + {_g(s)}) − {_g(2 * V)}/r² − {_g(V)}/r³ = 0. Mediante "
             f"el método de bisectriz, intervalo [{_g(a)}, {_g(b)}], tolerancia {tol:g}.")
    seq = _bisectriz_iter(Aprima, a, b, tol)
    # Comprobación: r1 = (a + b)/2, el primer punto medio (los resultados
    # son el radio final y el material mínimo, distintos de r1).
    comp = ("r1 — primer punto medio: (a + b)/2", seq[0])
    # Segunda comprobación: r2, el segundo punto medio.
    comp2 = _comp2_secuencia(seq, 0, "r2 — segundo punto medio",
                             "Semi-intervalo inicial: (b − a)/2", (b - a) / 2)
    dato = (f"Dato: V = {_g(V)} cm³, s = {_g(s)} cm, "
            f"intervalo [{_g(a)}, {_g(b)}], tolerancia = {tol:g}.")
    r_final = seq[-1]
    revision = (f"A'(r) = 4π(r + {_g(s)}) − {_g(2 * V)}/r² − {_g(V)}/r³. "
                f"A'({_g(a)}) = {Aprima(a):.9f} y A'({_g(b)}) = {Aprima(b):.9f}: hay "
                "cambio de signo en [" + _g(a) + ", " + _g(b) + "]. "
                + _resumen_raiz(seq, tol, etiqueta="r")
                + f" A({r_final:.9f}) = 2π({r_final:.9f} + {_g(s)})² + "
                f"{_g(2 * V)}({r_final:.9f} + {_g(s)})/{r_final:.9f}² = "
                f"{Area(r_final):.9f} cm².")
    return Reto(texto, ("Radio r (cm)", "Material mínimo A(r) (cm²)"),
                (r_final, Area(r_final)), revision, comp, dato, comp2)

def raices(m, d, r, variante=0):
    return [_newton, _secante, _punto_fijo, _falsa_posicion, _bisectriz][m](d, r, variante)

# ---------------------------------------------------------------------------
# Interpolación
# ---------------------------------------------------------------------------

def _puntos_str(xs, ys, dec_y=2):
    """Lista de puntos como la escribe el libro: [(x, y), ...]."""
    pares = ", ".join(f"({_g(x)}, {y:.{dec_y}f})" for x, y in zip(xs, ys))
    return f"[{pares}]"

def _lagrange(xs, ys, t):
    total = 0.0
    for i, (x, y) in enumerate(zip(xs, ys)):
        term = y
        for k, xk in enumerate(xs):
            if k != i:
                term *= (t - xk) / (x - xk)
        total += term
    return total

def _dif_divididas(xs, ys):
    """Coeficientes diagonales de la tabla de diferencias divididas."""
    n = len(xs)
    col = list(ys)
    coefs = [col[0]]
    for k in range(1, n):
        col = [(col[i + 1] - col[i]) / (xs[i + k] - xs[i]) for i in range(n - k)]
        coefs.append(col[0])
    return coefs

def _newton_divididas(xs, ys, t):
    coefs = _dif_divididas(xs, ys)
    total = coefs[0]
    term = 1.0
    for k in range(1, len(xs)):
        term *= (t - xs[k - 1])
        total += coefs[k] * term
    return total, coefs

def _dif_adelante(ys):
    col = list(ys)
    difs = [col[0]]
    while len(col) > 1:
        col = [b - a for a, b in zip(col, col[1:])]
        difs.append(col[0])
    return difs

def _newton_adelante_calc(xs, ys, t):
    h = xs[1] - xs[0]
    s = (t - xs[0]) / h
    difs = _dif_adelante(ys)
    total = difs[0]
    comb = 1.0
    for k in range(1, len(ys)):
        comb *= (s - (k - 1)) / k
        total += difs[k] * comb
    return total, s, difs

def _dif_atras(ys):
    col = list(ys)
    difs = [col[-1]]
    while len(col) > 1:
        col = [b - a for a, b in zip(col, col[1:])]
        difs.append(col[-1])
    return difs

def _newton_atras_calc(xs, ys, t):
    h = xs[1] - xs[0]
    s = (t - xs[-1]) / h
    difs = _dif_atras(ys)
    total = difs[0]
    comb = 1.0
    for k in range(1, len(ys)):
        comb *= (s + (k - 1)) / k
        total += difs[k] * comb
    return total, s, difs

def _tabla_creciente(r, ancla):
    """Tabla uniforme con y crecientes, como las del libro (§1.2, §1.3, §1.5)."""
    x1 = ancla["x1"] if r is None else round(r.uniform(0.5, 3.5), 1)
    h = ancla["h"] if r is None else r.choice([0.3, 0.4, 0.5])
    # Con r=None se usa la tabla exacta del Word (3 puntos), sin importar d.
    n = len(ancla["ys"]) if r is None else ancla.get("n_puntos", len(ancla["ys"]))
    if r is None:
        ys = list(ancla["ys"])
    else:
        ys = [round(r.uniform(0.5, 6.0), 2)]
        for _ in range(n - 1):
            ys.append(round(ys[-1] + r.uniform(0.1, 0.9), 2))
    xs = [round(x1 + i * h, 2) for i in range(n)]
    return xs, ys, h

def _newton_adelante_gen(d, r, variante):
    tpl = ANCLAS["Newton hacia adelante"][variante % 3]
    tpl = dict(tpl)
    tpl["n_puntos"] = 3 + d
    xs, ys, h = _tabla_creciente(r, tpl)
    if r is None:
        t = tpl["t"]
    else:
        s = r.choice([1 / 3, 1 / 2, 2 / 3, 5 / 6, 4 / 3, 5 / 3])
        t = round(xs[0] + h * s, 2)
    g, s, difs = _newton_adelante_calc(xs, ys, t)
    texto = (f"Ejemplo.- Obtener g(x) para x = {_g(t)}.\n"
             f"Puntos (x, y): {_puntos_str(xs, ys)}.\n"
             f"Evalúa el interpolante en x = {_g(t)}.")
    # Comprobación: s·∆1, el primer término de la suma de Newton
    # (s se calcula con (x − x1)/h y ∆1 = y2 − y1 a mano). La etiqueta
    # dice en palabras qué es ∆: el libro lo usa para las diferencias
    # hacia adelante, pero en pantalla parece una V o un triángulo.
    comp = ("s·∆1 — primer término: s por la primera diferencia (∆ = diferencia hacia adelante)", s * difs[1])
    # Segunda comprobación: el segundo término de la suma.
    comp2 = ("s·(s−1)·∆2/2 — segundo término: s(s−1)/2 por la segunda diferencia", s * (s - 1) / 2 * difs[2])
    dato = (f"Dato: x1 = {_g(xs[0])}, h = {_g(h)} (intervalos uniformes), "
            f"evalúa en x = {_g(t)}.")
    dif_txt = "; ".join(f"∆{k} = {v:.9f}" for k, v in enumerate(difs) if k >= 1)
    revision = (f"Tabla de diferencias hacia adelante: {dif_txt}. "
                f"s = (x − x1)/h = ({_g(t)} − {_g(xs[0])})/{_g(h)} = {s:.9f}. "
                f"g({_g(t)}) = {ys[0]:.9f} + s·∆1 + s(s−1)/2·∆2"
                + (" + …" if len(difs) > 3 else "") + f" = {g:.9f}.")
    return Reto(texto, (f"Valor interpolado g({_g(t)})",), (g,), revision, comp, dato, comp2)

def _newton_atras_gen(d, r, variante):
    tpl = ANCLAS["Newton hacia atrás"][variante % 3]
    tpl = dict(tpl)
    tpl["n_puntos"] = 3 + d
    xs, ys, h = _tabla_creciente(r, tpl)
    if r is None:
        t = tpl["t"]
    else:
        s = r.choice([-1 / 3, -1 / 2, -2 / 3, -5 / 6, -4 / 3, -5 / 3])
        t = round(xs[-1] + h * s, 2)
    g, s, difs = _newton_atras_calc(xs, ys, t)
    texto = (f"Ejemplo.- Obtener g(x) para x = {_g(t)}.\n"
             f"Puntos (x, y): {_puntos_str(xs, ys)}.\n"
             f"Evalúa el interpolante en x = {_g(t)}.")
    # Comprobación: s·∇1, el primer término de la suma de Newton
    # hacia atrás (s se calcula con (x − xn)/h y ∇1 a mano). La etiqueta
    # dice en palabras qué es ∇: el libro lo usa para las diferencias
    # hacia atrás, pero en pantalla parece una V (es un triángulo
    # invertido). Es el símbolo del libro, no un error.
    comp = ("s·∇1 — primer término: s por la primera diferencia (∇ = diferencia hacia atrás)", s * difs[1])
    # Segunda comprobación: el segundo término de la suma.
    comp2 = ("s·(s+1)·∇2/2 — segundo término: s(s+1)/2 por la segunda diferencia", s * (s + 1) / 2 * difs[2])
    dato = (f"Dato: xn = {_g(xs[-1])}, h = {_g(h)} (intervalos uniformes), "
            f"evalúa en x = {_g(t)}.")
    dif_txt = "; ".join(f"∇{k} = {v:.9f}" for k, v in enumerate(difs) if k >= 1)
    revision = (f"Tabla de diferencias hacia atrás: {dif_txt}. "
                f"s = (x − xn)/h = ({_g(t)} − {_g(xs[-1])})/{_g(h)} = {s:.9f}. "
                f"g({_g(t)}) = {ys[-1]:.9f} + s·∇1 + s(s+1)/2·∇2"
                + (" + …" if len(difs) > 3 else "") + f" = {g:.9f}.")
    return Reto(texto, (f"Valor interpolado g({_g(t)})",), (g,), revision, comp, dato, comp2)

def _diferencias_gen(d, r, variante):
    tpl = ANCLAS["Diferencias divididas"][variante % 3]
    if variante % 3 == 2:
        # Función de Bessel: la tabla del libro es fija; solo cambia el punto.
        xs = list(tpl["xs"])
        ys = list(tpl["ys"])
        if r is None:
            t = tpl["t"]
        else:
            t = round(r.uniform(1.1, 2.1), 2)
        g, coefs = _newton_divididas(xs, ys, t)
        texto = ("Aplicaciones. Las funciones de Bessel tienen forma de armónicos "
                 "cilíndricos y sirven para estudiar y modelar la propagación de "
                 "ondas. La tabla siguiente muestra los valores de la función de "
                 "Bessel de primera clase de orden cero en varios puntos. "
                 "a) Construir la tabla de diferencias divididas hasta orden tres. "
                 "b) Utilizar la información del apartado anterior para construir "
                 "el polinomio interpolador de Newton de la función de Bessel que "
                 "pasa por los puntos anteriores. c) Obtener el valor aproximado de "
                 f"la función de Bessel en el punto {_g(t)}.\n"
                 f"Puntos (x, y): {_puntos_str(xs, ys, dec_y=7)}.\n"
                 f"Evalúa el interpolante en x = {_g(t)}.")
        coef_txt = "; ".join(f"D{k} = {v:.9f}" for k, v in enumerate(coefs))
        revision = (f"Coeficientes (diagonal de la tabla de diferencias divididas): "
                    f"{coef_txt}. p4({_g(t)}) = {g:.9f} (valor real f({_g(t)}) ≈ "
                    f"{_bessel_j0(t):.9f}).")
        # Comprobación: D1·(x − x1), el primer término de la suma de
        # Newton (D1 es la primera diferencia dividida; D0 = y1 ya viene
        # en los datos, así que no serviría como comprobación). El libro
        # escribe g(x) = D0 + D1(x − x1) + D2(x − x1)(x − x2): el primer
        # punto es x1, no x0.
        comp = ("D1·(x − x1) — primer término que se suma a y1", coefs[1] * (t - xs[0]))
        # Segunda comprobación: el segundo término de la suma.
        comp2 = ("D2·(x − x1)(x − x2) — segundo término que se suma a y1",
                 coefs[2] * (t - xs[0]) * (t - xs[1]))
        dato = f"Dato: primer punto x1 = {_g(xs[0])}, evalúa en x = {_g(t)}."
        return Reto(texto, (f"Valor interpolado g({_g(t)})",), (g,), revision, comp, dato, comp2)
    n = 3 + d
    if r is None:
        xs = list(tpl["xs"])
        ys = list(tpl["ys"])
        t = tpl["t"]
    else:
        x1 = round(r.uniform(4.0, 6.0), 1)
        pasos = [r.choice([0.6, 0.7]) for _ in range(n - 1)]
        xs = [x1]
        for h in pasos:
            xs.append(round(xs[-1] - h, 2))
        ys = [round(r.uniform(-2.0, 2.0), 2)]
        for _ in range(n - 1):
            ys.append(round(ys[-1] - r.uniform(0.3, 1.0), 2))
        t = round(r.uniform(xs[-1] + 0.2, xs[0] - 0.2), 1)
    g, coefs = _newton_divididas(xs, ys, t)
    texto = (f"Ejemplo.- Encuentre g(x) para x = {_g(t)}.\n"
             f"Puntos (x, y): {_puntos_str(xs, ys)}.\n"
             f"Evalúa el interpolante en x = {_g(t)}.")
    coef_txt = "; ".join(f"D{k} = {v:.9f}" for k, v in enumerate(coefs))
    revision = (f"Tabla de diferencias divididas (orden decreciente): {coef_txt}. "
                f"g({_g(t)}) = {g:.9f}.")
    # Comprobación: D1·(x − x1), el primer término de la suma de Newton.
    comp = ("D1·(x − x1) — primer término que se suma a y1", coefs[1] * (t - xs[0]))
    # Segunda comprobación: el segundo término de la suma.
    comp2 = ("D2·(x − x1)(x − x2) — segundo término que se suma a y1",
             coefs[2] * (t - xs[0]) * (t - xs[1]))
    dato = (f"Dato: tabla en orden decreciente (intervalos no uniformes), "
            f"evalúa en x = {_g(t)}.")
    return Reto(texto, (f"Valor interpolado g({_g(t)})",), (g,), revision, comp, dato, comp2)

def _bessel_j0(x):
    """J0(x) por su serie (para el valor real de referencia de Bessel)."""
    total = 0.0
    term = 1.0
    for k in range(30):
        if k:
            term *= -(x * x / 4) / (k * k)
        total += term
    return total

def _lagrange_gen(d, r, variante):
    tpl = ANCLAS["Lagrange"][variante % 3]
    # La plantilla de Lagrange guarda la tabla (xs, ys); se deriva x1 y h de ella.
    tpl2 = dict(tpl)
    tpl2["x1"] = tpl["xs"][0]
    tpl2["h"] = tpl["xs"][1] - tpl["xs"][0]
    tpl2["n_puntos"] = 3 + d
    xs, ys, h = _tabla_creciente(r, tpl2)
    if r is None:
        t = tpl["t"]
    else:
        s = r.choice([1 / 3, 1 / 2, 2 / 3, 4 / 3, 5 / 3])
        t = round(xs[0] + h * s, 2)
    g = _lagrange(xs, ys, t)
    texto = (f"Ejemplo.- Obtener g(x) para x = {_g(t)}.\n"
             f"Puntos (x, y): {_puntos_str(xs, ys)}.\n"
             f"Evalúa el interpolante en x = {_g(t)}.")
    def _termino_libro(i):
        # Término i (base 0) con la notación del libro (§1.5, base 1):
        # y_j · Π (x − x_k)/(x_j − x_k), k ≠ j. El libro NO usa la letra
        # L para la base de Lagrange: el término es y_j por el cociente.
        # Se escribe en texto plano y el formateador pone los subíndices
        # y el cociente como fracción apilada.
        j = i + 1
        n = len(xs)
        num = "".join("(x−x%d)" % (k + 1) for k in range(n) if k != i)
        den = "".join("(x%d−x%d)" % (j, k + 1) for k in range(n) if k != i)
        return "y%d·(%s)/(%s)" % (j, num, den)
    terminos = []
    for i, (x, y) in enumerate(zip(xs, ys)):
        li = 1.0
        for k, xk in enumerate(xs):
            if k != i:
                li *= (t - xk) / (x - xk)
        terminos.append(f"{_termino_libro(i)} = {li:.9f}·{y:.9f} = {li * y:.9f}")
    revision = ("Polinomio de Lagrange, término por término: "
                + "; ".join(terminos) + f". g({_g(t)}) = {g:.9f}.")
    # Comprobación: el primer término de la suma de Lagrange, como en
    # el libro: y1 por el producto de cocientes (x − xk)/(x1 − xk).
    _l0 = 1.0
    for _k, _xk in enumerate(xs):
        if _k != 0:
            _l0 *= (t - _xk) / (xs[0] - _xk)
    comp = (_termino_libro(0) + " — primer término: y1 por su fracción", _l0 * ys[0])
    # Segunda comprobación: el segundo término de la suma.
    _l1 = 1.0
    for _k, _xk in enumerate(xs):
        if _k != 1:
            _l1 *= (t - _xk) / (xs[1] - _xk)
    comp2 = (_termino_libro(1) + " — segundo término: y2 por su fracción", _l1 * ys[1])
    dato = (f"Dato: x1 = {_g(xs[0])}, h = {_g(h)} (intervalos uniformes), "
            f"evalúa en x = {_g(t)}.")
    return Reto(texto, (f"Valor interpolado g({_g(t)})",), (g,), revision, comp, dato, comp2)

def _lineal_gen(d, r, variante):
    tpl = ANCLAS["Interpolación lineal"][variante % 3]
    if r is None:
        x, a1, a2, b1, b2 = tpl["x"], tpl["a1"], tpl["a2"], tpl["b1"], tpl["b2"]
    else:
        x = r.choice([4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20])
        while True:
            da1 = r.choice([1, 2, 3])
            da2 = r.choice([1, 2, 3])
            if (da1, da2) != (1, 1) and x - da1 >= 1:
                break
        a1, a2 = x - da1, x + da2
        b1, b2 = x - 1, x + 1
    ga = log(a1) + (log(a2) - log(a1)) / (a2 - a1) * (x - a1)
    gb = log(b1) + (log(b2) - log(b1)) / (b2 - b1) * (x - b1)
    real = log(x)
    ea, eb = abs(real - ga), abs(real - gb)
    texto = (f"Ejemplo. Estimar el Ln de {x} mediante interpolación lineal.\n"
             f"a) Primero realice el cálculo entre Ln {a1} y Ln {a2}.\n"
             f"b) Después desarrolle el procedimiento pero con intervalos menores "
             f"de Ln {b1} y Ln {b2}.\n"
             f"Puntos (x, y) inciso a): [({a1}, {log(a1):.9f}), ({a2}, {log(a2):.9f})].\n"
             f"Puntos (x, y) inciso b): [({b1}, {log(b1):.9f}), ({b2}, {log(b2):.9f})].\n"
             f"Evalúa el interpolante en x = {x}.")
    revision = (f"a) g({x}) = {log(a1):.9f} + [({log(a2):.9f} − {log(a1):.9f})/"
                f"({a2} − {a1})]·({x} − {a1}) = {ga:.9f}; "
                f"Є = |{real:.9f} − {ga:.9f}| = {ea:.9f}. "
                f"b) g({x}) = {log(b1):.9f} + [({log(b2):.9f} − {log(b1):.9f})/"
                f"({b2} − {b1})]·({x} − {b1}) = {gb:.9f}; "
                f"Є = |{real:.9f} − {gb:.9f}| = {eb:.9f}.")
    # Comprobación: la pendiente del inciso a), es decir la primera
    # diferencia dividida (Ln a2 − Ln a1)/(a2 − a1). El primer término de
    # la suma (Ln a1) no sirve: ya viene escrito en los datos.
    comp = (f"Pendiente entre Ln {a1} y Ln {a2}: (Ln {a2} − Ln {a1})/({a2} − {a1})",
            (log(a2) - log(a1)) / (a2 - a1))
    # Segunda comprobación: la pendiente del inciso b), con el
    # intervalo menor (Ln b2 − Ln b1)/(b2 − b1).
    comp2 = (f"Pendiente entre Ln {b1} y Ln {b2}: (Ln {b2} − Ln {b1})/({b2} − {b1})",
             (log(b2) - log(b1)) / (b2 - b1))
    dato = (f"Dato: inciso a) entre Ln {a1} y Ln {a2}; "
            f"inciso b) entre Ln {b1} y Ln {b2}.")
    return Reto(texto, (f"Valor interpolado g({x}) con el intervalo a)",
                        f"Error Є del inciso a): |Ln {x} − g({x})|",
                        f"Valor interpolado g({x}) con el intervalo b)",
                        f"Error Є del inciso b): |Ln {x} − g({x})|"),
                (ga, ea, gb, eb), revision, comp, dato, comp2)

def interpolar(m, d, r, variante=0):
    return [_newton_adelante_gen, _newton_atras_gen, _diferencias_gen,
            _lagrange_gen, _lineal_gen][m](d, r, variante)

# ---------------------------------------------------------------------------
# Mínimos cuadrados
# ---------------------------------------------------------------------------

def sistema(A, b):
    mat = [row[:] + [y] for row, y in zip(A, b)]
    n = len(b)
    for k in range(n):
        j = max(range(k, n), key=lambda i: abs(mat[i][k]))
        mat[k], mat[j] = mat[j], mat[k]
        p = mat[k][k]
        mat[k] = [v / p for v in mat[k]]
        for i in range(n):
            if i != k:
                c = mat[i][k]
                mat[i] = [v - c * w for v, w in zip(mat[i], mat[k])]
    return [row[-1] for row in mat]

# Modelos del libro (§4): bases de cada ajuste, nombre de cada base y su fórmula.
_MODELOS = [
    ("Línea recta", [lambda x: 1.0, lambda x: x], ["1", "x"], "a0 + a1·x"),
    ("Lineal con función", [lambda x: 1.0, lambda x: x, lambda x: exp(x)],
     ["1", "x", "e^x"], "a0 + a1·x + a2·e^x"),
    ("Cuadrática con función", [lambda x: 1.0, lambda x: x, lambda x: x * x,
                                lambda x: log(x)], ["1", "x", "x²", "Ln(x)"],
     "a0 + a1·x + a2·x² + a3·Ln(x)"),
    ("Cuadrática", [lambda x: 1.0, lambda x: x, lambda x: x * x],
     ["1", "x", "x²"], "a0 + a1·x + a2·x²"),
    ("Cúbica", [lambda x: 1.0, lambda x: x, lambda x: x * x, lambda x: x ** 3],
     ["1", "x", "x²", "x³"], "a0 + a1·x + a2·x² + a3·x³"),
]

def _suma_signos(terminos):
    """Une términos (valor, nombre) con su signo: '3.0000·a1 + 10.4792·a2'.
    Un nombre vacío deja solo el número (término independiente)."""
    s = ""
    for i, (valor, nombre) in enumerate(terminos):
        pieza = f"{abs(valor):.4f}" + (f"·{nombre}" if nombre else "")
        if i == 0:
            s += ("−" if valor < 0 else "") + pieza
        else:
            s += (" − " if valor < 0 else " + ") + pieza
    return s

def _puntos_ajuste(r, tpl):
    """Puntos del libro; en juego solo se mueven las y (±0.6, 1 decimal)."""
    xs = list(tpl["xs"])
    if r is None:
        ys = list(tpl["ys"])
    else:
        ys = [round(y + r.uniform(-0.6, 0.6), 1) for y in tpl["ys"]]
    return xs, ys

def ajuste(m, d, r, variante=0):
    nombre, bases, nombres_base, modelo = _MODELOS[m]
    tpl = ANCLAS[nombre][variante % 3]
    xs, ys = _puntos_ajuste(r, tpl)
    n = len(xs)
    cols = [[f(x) for x in xs] for f in bases]
    dot = lambda a, b: sum(x * y for x, y in zip(a, b))
    A = [[dot(ci, cj) for cj in cols] for ci in cols]
    rhs = [dot(ci, ys) for ci in cols]
    coef = sistema(A, rhs)
    if m == 1:
        encabezado = (f"Ajustar una función lineal con función a las siguientes "
                      f"observaciones por puntos (x, y), con función f(x) = e^x.")
    elif m == 2:
        encabezado = (f"Ajustar una función cuadrática con función a las siguientes "
                      f"observaciones por puntos (x, y), con función f(x) = Ln(x), x > 0.")
    elif m == 0:
        encabezado = "Ajustar una línea recta a las siguientes observaciones por puntos (x, y)."
    elif m == 3:
        encabezado = "Ajustar una función cuadrática a las siguientes observaciones por puntos (x, y)."
    else:
        encabezado = "Ajustar una función cúbica a las siguientes observaciones por puntos (x, y)."
    texto = (encabezado + f"\nPuntos (x, y): {_puntos_str(xs, ys, dec_y=1)}.")
    # Revisión estilo libro: tabla de sumas, ecuaciones normales y coeficientes.
    sumas = []
    for j, cj in enumerate(cols):
        sumas.append(f"Σ{nombres_base[j]} = {sum(cj):.4f}")
    sumas.append(f"Σy = {sum(ys):.4f}")
    for j, cj in enumerate(cols):
        sumas.append(f"Σ{nombres_base[j]}·y = {dot(cj, ys):.4f}")
    ecuaciones = []
    for i in range(len(bases)):
        ecuaciones.append(_suma_signos([(A[i][j], f"a{j}") for j in range(len(bases))])
                           + f" = {rhs[i]:.4f}")
    coef_txt = ", ".join(f"a{j} = {c:.9f}" for j, c in enumerate(coef))
    gx = _suma_signos([(coef[0], "")] + [(coef[j], nombres_base[j])
                                         for j in range(1, len(coef))])
    revision = (f"Se forma la tabla con x, y y las columnas auxiliares; n = {n}. "
                + "; ".join(sumas) + ". Ecuaciones normales: "
                + " ; ".join(ecuaciones) + ". Resolviendo el sistema de ecuaciones "
                f"normales (eliminación gaussiana) se obtiene: {coef_txt}. "
                f"La función de ajuste es g(x) = {gx}.")
    # Comprobación: una suma de la tabla que el estudiante debe formar
    # a mano para las ecuaciones normales; nunca es un coeficiente.
    if m == 0:
        comp = ("Σx² — suma de los x al cuadrado", float(dot(cols[1], cols[1])))
    elif m == 1:
        comp = ("Σxy — suma de x por y", float(dot(cols[1], ys)))
    elif m == 2:
        comp = ("Σy — suma de las y", float(sum(ys)))
    elif m == 3:
        comp = ("Σxy — suma de x por y", float(dot(cols[1], ys)))
    else:
        comp = ("Σx² — suma de los x al cuadrado", float(dot(cols[1], cols[1])))
    # Segunda comprobación: otra suma de la tabla, distinta de la
    # primera, que también se forma a mano para las ecuaciones normales.
    if m == 0:
        comp2 = ("Σxy — suma de x por y", float(dot(cols[1], ys)))
    elif m == 1:
        comp2 = ("Σe^x·y — suma de e^x por y", float(dot(cols[2], ys)))
    elif m == 2:
        comp2 = ("Σxy — suma de x por y", float(dot(cols[1], ys)))
    elif m == 3:
        comp2 = ("Σx² — suma de los x al cuadrado", float(dot(cols[1], cols[1])))
    else:
        comp2 = ("Σxy — suma de x por y", float(dot(cols[1], ys)))
    dato = f"Dato: modelo g(x) = {modelo}, n = {n} puntos (x, y)."
    return Reto(texto, ("Coeficiente a (término independiente)",
                        f"Coeficiente b (el que multiplica a {nombres_base[1]})"),
                tuple(coef[:2]), revision, comp, dato, comp2)

# ---------------------------------------------------------------------------
# Integración
# ---------------------------------------------------------------------------

# Constantes de Newton-Cotes del libro (§5.4): n -> (alfa, pesos).
NC_CERRADA_TABLA = {
    4: (2 / 45, [7, 32, 12, 32, 7]),
    5: (5 / 288, [19, 75, 50, 50, 75, 19]),
    6: (1 / 140, [41, 216, 27, 272, 27, 216, 41]),
}
NC_ABIERTA_TABLA = {
    4: (6 / 20, [0, 11, -14, 26, -14, 11, 0]),
    5: (7 / 1440, [0, 611, -453, 562, 562, -453, 611, 0]),
    6: (8 / 945, [0, 460, -954, 2196, -2459, 2196, -954, 460, 0]),
}

def _nc(d, r, variante, cerrada):
    tpl = ANCLAS["Newton-Cotes cerrada" if cerrada else "Newton-Cotes abierta"][variante % 3]
    u = _opcion(r, [2.0, 3.0, 4.0], tpl["u"])
    v = _opcion(r, [-10.0, -8.0, -5.0, -3.0], tpl["v"])
    if r is None:
        a, b = tpl["a"], tpl["b"]
    else:
        a = r.choice([-2.0, -1.0, 0.0, 0.5, 1.0])
        b = a + r.choice([2.0, 3.0, 4.0])
    if r is None:
        n = tpl["n"]
    else:
        n = 4 + d
    tabla = NC_CERRADA_TABLA if cerrada else NC_ABIERTA_TABLA
    alfa, pesos = tabla[n]
    if cerrada:
        h = (b - a) / n
        xs = [a + i * h for i in range(n + 1)]
    else:
        h = (b - a) / (n + 2)
        xs = [a + i * h for i in range(n + 3)]
    f = lambda x: u * x ** 3 + v
    vals = [f(x) for x in xs]
    suma = sum(w * y for w, y in zip(pesos, vals))
    total = alfa * h * suma
    exacto = u * (b ** 4 - a ** 4) / 4 + v * (b - a)
    metodo = "Newton – Cotes Cerradas" if cerrada else "Newton – Cotes Abiertas"
    texto = (f"Calcular la integral de ({_num(u)}x³ {_con_signo(v, '')}) dx "
             f"de {_g(a)} a {_g(b)} por el método de {metodo} con n = {n}.")
    filas = "; ".join(f"x{i} = {x:.9f}, f = {y:.9f}, peso {w}"
                      for i, (x, y, w) in enumerate(zip(xs, vals, pesos)))
    revision = (f"h = ({_g(b)} − ({_g(a)}))/{n if cerrada else n + 2} = {h:.9f}. "
                f"Nodos: {filas}. Suma ponderada: {suma:.9f}. "
                f"I = {alfa:.9f}·{h:.9f}·({suma:.9f}) = {total:.9f}. "
                f"Valor exacto: {exacto:.9f}.")
    # Comprobación: la suma ponderada interior (nodos interiores con sus
    # pesos; los extremos no entran). Es el paso a mano antes de
    # multiplicar por α·h, y nunca es la integral.
    comp = ("Suma ponderada interior (suma de los valores de adentro, "
            "cada uno por su peso, sin los extremos)",
            sum(w * y for w, y in zip(pesos[1:-1], vals[1:-1])))
    # Segunda comprobación: la suma ponderada completa (con los
    # extremos). En la abierta los extremos pesan 0, así que ahí se
    # pide la suma de los términos con peso positivo.
    if cerrada:
        comp2 = ("Suma ponderada completa (todos los valores con su peso, "
                 "con los extremos)", suma)
    else:
        comp2 = ("Suma de los términos con peso positivo "
                 "(solo los de peso mayor que 0)",
                 sum(w * y for w, y in zip(pesos, vals) if w > 0))
    dato = f"Dato: n = {n}, h = {_g(h)}."
    return Reto(texto, (f"Integral aproximada de {_g(a)} a {_g(b)}",),
                (total,), revision, comp, dato, comp2)

def _simpson13(d, r, variante):
    tpl = ANCLAS["Simpson 1/3"][variante % 3]
    if r is None:
        a, b, n = tpl["a"], tpl["b"], tpl["n"]
    else:
        a = r.choice([0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75,
                      2.0, 2.25, 2.5, 2.75, 3.0])
        b = a + r.choice([1.0, 1.5, 2.0])
        n = 6 + 4 * d + (2 if r.random() < 0.5 else 0)
    h = (b - a) / n
    xs = [a + i * h for i in range(n + 1)]
    f = lambda x: 1 / (1 + x * x)
    vals = [f(x) for x in xs]
    suma = vals[0] + vals[-1] + 4 * sum(vals[1:-1:2]) + 2 * sum(vals[2:-1:2])
    total = h / 3 * suma
    exacto = atan(b) - atan(a)
    texto = (f"Calcular la integral de 1/(1+x²) dx de {_g(a)} a {_g(b)} "
             f"por la regla de 1/3 de Simpson con n = {n}.")
    revision = (f"h = ({_g(b)} − {_g(a)})/{n} = {h:.9f}. "
                f"Suma ponderada (1, 4, 2, …, 4, 1): {suma:.9f}. "
                f"I = ({h:.9f}/3)·({suma:.9f}) = {total:.9f}. "
                f"Valor exacto: arctan({_g(b)}) − arctan({_g(a)}) = {exacto:.9f}.")
    # Comprobación: la suma ponderada interior 4·Σ(impares) + 2·Σ(pares),
    # sin los extremos (pesos 1). Es el paso a mano antes de ·h/3.
    comp = ("Suma ponderada interior (4 por los impares + 2 por los pares, "
            "sin los extremos)",
            4 * sum(vals[1:-1:2]) + 2 * sum(vals[2:-1:2]))
    # Segunda comprobación: la suma ponderada completa (con los extremos).
    comp2 = ("Suma ponderada completa (todos los valores con su peso, "
             "con los extremos)", suma)
    dato = f"Dato: n = {n}, h = {_g(h)}."
    return Reto(texto, (f"Integral aproximada de {_g(a)} a {_g(b)}",),
                (total,), revision, comp, dato, comp2)

def _simpson38(d, r, variante):
    tpl = ANCLAS["Simpson 3/8"][variante % 3]
    if r is None:
        a, b, n = tpl["a"], tpl["b"], tpl["n"]
    else:
        a = r.choice([0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0])
        b = a + r.choice([1.0, 1.5, 2.0])
        n = 3 * (d + 1) + (3 if r.random() < 0.5 else 0)
    h = (b - a) / n
    xs = [a + i * h for i in range(n + 1)]
    f = lambda x: x ** 3 * exp(x)
    vals = [f(x) for x in xs]
    suma = vals[0] + vals[-1]
    for i in range(1, n):
        suma += (2 if i % 3 == 0 else 3) * vals[i]
    total = 3 * h / 8 * suma
    def _prim(x):
        return exp(x) * (x ** 3 - 3 * x ** 2 + 6 * x - 6)
    exacto = _prim(b) - _prim(a)
    texto = (f"Calcular la integral de x³·e^x dx de {_g(a)} a {_g(b)} "
             f"por la regla de 3/8 de Simpson con n = {n}.")
    revision = (f"h = ({_g(b)} − {_g(a)})/{n} = {h:.9f}. "
                f"Suma ponderada (1, 3, 3, 2, …, 3, 3, 1): {suma:.9f}. "
                f"I = (3·{h:.9f}/8)·({suma:.9f}) = {total:.9f}. "
                f"Valor exacto: {exacto:.9f}.")
    # Comprobación: la suma ponderada interior (pesos 3, 3, 2, …), sin
    # los extremos (pesos 1). Es el paso a mano antes de ·3h/8.
    _s_int = 0.0
    for _i in range(1, n):
        _s_int += (2 if _i % 3 == 0 else 3) * vals[_i]
    comp = ("Suma ponderada interior (pesos 3, 3 y 2, sin los extremos)", _s_int)
    # Segunda comprobación: la suma ponderada completa (con los extremos).
    comp2 = ("Suma ponderada completa (todos los valores con su peso, "
             "con los extremos)", suma)
    dato = f"Dato: n = {n}, h = {_g(h)}."
    return Reto(texto, (f"Integral aproximada de {_g(a)} a {_g(b)}",),
                (total,), revision, comp, dato, comp2)

def _trapezoidal(d, r, variante):
    tpl = ANCLAS["Regla trapezoidal"][variante % 3]
    if "xs" in tpl:
        xs = list(tpl["xs"])
        if r is None:
            ys = list(tpl["ys"])
        else:
            ys = [round(y + r.uniform(-0.1, 0.1), 1) for y in tpl["ys"]]
        h = 0.5
        area2 = h / 2 * (ys[0] + 2 * sum(ys[1:4]) + ys[4])
        area25 = area2 + h / 2 * (ys[4] + ys[5])
        texto = ("Un agricultor desea conocer la superficie aproximada de un prado "
                 "limitado por una carretera, dos caminos perpendiculares a ella y "
                 "la ribera de un río, de manera que si se colocan unos ejes "
                 "cartesianos sobre la carretera (eje X) y uno de los caminos (eje Y, "
                 "abscisa x = 0). El segundo camino será la recta vertical x = 2 "
                 "(unidades en cientos de metros). Se consideran varias medidas "
                 "desde la carretera hasta la ribera. Obteniéndose las siguientes "
                 "coordenadas para los puntos de la ribera: "
                 + ", ".join(f"({_g(x)}, {_g(y)})" for x, y in zip(xs, ys))
                 + ". Calcular aproximadamente el área de dicho terreno utilizando "
                 "la Regla del Trapecio. Determinar el área si se extiende el "
                 "terreno hasta la abscisa x = 2.5.")
        revision = (f"h = 0.5. Área [0,2] = (0.5/2)·[{ys[0]:.9f} + 2·({ys[1]:.9f} + "
                    f"{ys[2]:.9f} + {ys[3]:.9f}) + {ys[4]:.9f}] = {area2:.9f}. "
                    f"Extensión: último trapecio (0.5/2)·({ys[4]:.9f} + {ys[5]:.9f}) = "
                    f"{h / 2 * (ys[4] + ys[5]):.9f}. Área total = {area25:.9f}. "
                    f"En unidades de (100 m)²: {area2:.9f} × 10 000 = {area2 * 10000:.0f} m²; "
                    f"{area25:.9f} × 10 000 = {area25 * 10000:.0f} m².")
        # Comprobación: la suma ponderada interior 2·(y1 + y2 + y3)
        # del área [0, 2] (sin los extremos). Es el paso a mano antes de
        # ·h/2, y nunca es un área.
        comp = ("Suma ponderada interior (área [0, 2]: 2·(y1 + y2 + y3), "
                "sin los extremos)",
                2 * (ys[1] + ys[2] + ys[3]))
        # Segunda comprobación: la suma ponderada completa del área [0, 2].
        comp2 = ("Suma ponderada completa (área [0, 2], con los extremos)",
                 ys[0] + 2 * (ys[1] + ys[2] + ys[3]) + ys[4])
        dato = "Dato: h = 0.5, unidades en cientos de metros."
        return Reto(texto, ("Área [0, 2]", "Área [0, 2.5]"), (area2, area25),
                    revision, comp, dato, comp2)
    if r is None:
        a, b, n = tpl["a"], tpl["b"], tpl["n"]
    else:
        a = r.choice([0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75,
                      2.0, 2.25, 2.5, 2.75, 3.0])
        b = a + r.choice([1.0, 1.5, 2.0])
        n = 4 + 2 * d + (2 if r.random() < 0.5 else 0)
    h = (b - a) / n
    xs = [a + i * h for i in range(n + 1)]
    f = lambda x: 1 / (1 + x * x)
    vals = [f(x) for x in xs]
    suma = vals[0] + vals[-1] + 2 * sum(vals[1:-1])
    total = h / 2 * suma
    exacto = atan(b) - atan(a)
    texto = (f"Calcular la integral de 1/(1+x²) dx de {_g(a)} a {_g(b)} "
             f"por la regla trapezoidal con n = {n}.")
    revision = (f"h = ({_g(b)} − {_g(a)})/{n} = {h:.9f}. "
                f"Suma (extremos + 2·interiores): {suma:.9f}. "
                f"I = ({h:.9f}/2)·({suma:.9f}) = {total:.9f}. "
                f"Valor exacto: arctan({_g(b)}) − arctan({_g(a)}) = {exacto:.9f}.")
    # Comprobación: la suma ponderada interior 2·Σ(interiores), sin los
    # extremos. Es el paso a mano antes de ·h/2.
    comp = ("Suma ponderada interior (2 por los valores de adentro, "
            "sin los extremos)", 2 * sum(vals[1:-1]))
    # Segunda comprobación: la suma ponderada completa (con los extremos).
    comp2 = ("Suma ponderada completa (todos los valores con su peso, "
             "con los extremos)", suma)
    dato = f"Dato: n = {n}, h = {_g(h)}."
    return Reto(texto, (f"Integral aproximada de {_g(a)} a {_g(b)}",),
                (total,), revision, comp, dato, comp2)

def integral(m, d, r, variante=0):
    if m == 0:
        return _nc(d, r, variante, cerrada=True)
    if m == 1:
        return _nc(d, r, variante, cerrada=False)
    return [_simpson13, _simpson38, _trapezoidal][m - 2](d, r, variante)

# ---------------------------------------------------------------------------
# EDO
# ---------------------------------------------------------------------------

def _f_lineal(u, v, w):
    """y' = (u·y·t + v)/w, la forma despejada de A·y' + B·y·t + C = 0."""
    return lambda y, t: (u * y * t + v) / w

def _ecuacion_edo_y(A, B, D):
    """A·y' + B·y·t + D·y = 0, como la escribe el libro (§6.4)."""
    s = f"{_num(A)}y'"
    s += _con_signo(B, "yt")
    if D == 1:
        s += " + y"
    elif D == -1:
        s += " − y"
    else:
        s += _con_signo(D, "y")
    return s + " = 0"

def _despeje_edo_y(A, B, D):
    """y' = (−B·y·t − D·y)/A."""
    num = _con_signo(-B, "yt", primero=True) + _con_signo(-D, "y")
    return f"y' = ({num})/{_num(A)}"

def _edo_euler_adelante(f, y0, h, n):
    ys, det = [], []
    y, t = y0, 0.0
    for i in range(n):
        k = h * f(y, t)
        det.append(f"Paso {i + 1}: f(y{i}, t{i}) = {f(y, t):.9f}; "
                   f"y{i + 1} = {y:.9f} + {h:g}·{f(y, t):.9f} = {y + k:.9f}")
        y += k
        t += h
        ys.append(y)
    return ys, det

def _edo_euler_modificado(f, y0, h, n, dado=None):
    ys, det = [], []
    y, t = y0, 0.0
    for i in range(n):
        f0 = f(y, t)
        if dado is not None and i == 0:
            # Como el libro (§6.4): el corrector usa el y1 dado en el enunciado.
            f1 = f(dado, t + h)
            det.append(f"Paso {i + 1}: f(y0, t0) = {f0:.9f}; "
                       f"f(y1, t1) = {f1:.9f} (con el y1 dado en el enunciado); "
                       f"y1 = {y:.9f} + ({h:g}/2)·({f0:.9f} + {f1:.9f})")
            y = y + (h / 2) * (f0 + f1)
        else:
            y_pred = y + h * f0
            f1 = f(y_pred, t + h)
            det.append(f"Paso {i + 1}: predictor y{i + 1} = {y:.9f} + {h:g}·{f0:.9f} "
                       f"= {y_pred:.9f}; f(y{i + 1}, t{i + 1}) = {f1:.9f}; "
                       f"corrector y{i + 1} = {y:.9f} + ({h:g}/2)·({f0:.9f} + {f1:.9f})")
            y = y + (h / 2) * (f0 + f1)
        t += h
        ys.append(y)
        det[-1] += f" = {y:.9f}"
    return ys, det

def _edo_euler_atras(u, v, w, y0, h, n):
    ys, det = [], []
    y, t = y0, 0.0
    for i in range(n):
        t1 = t + h
        y1 = (y + h * v / w) / (1 - h * u * t1 / w)
        det.append(f"Paso {i + 1}: y{i + 1} = y{i} + {h:g}·f(y{i + 1}, {t1:g}) "
                   f"= {y:.9f} + {h:g}·({u}·y{i + 1}·{t1:g} + {v})/{w}; "
                   f"despejando y{i + 1} = {y1:.9f}")
        y, t = y1, t1
        ys.append(y)
    return ys, det

def _edo_rk_superior(a, b, y0, v0, h, n):
    ys, vs, det = [], [], []
    y, v, t = y0, v0, 0.0
    for i in range(n):
        k1 = h * v
        m1 = h * (a * v * t - b * y)
        k2 = h * (v + m1)
        m2 = h * (a * (v + m1) * (t + h) - b * (y + k1))
        y1 = y + (k1 + k2) / 2
        v1 = v + (m1 + m2) / 2
        det.append(f"Paso {i + 1}: k1 = {k1:.9f}; m1 = {m1:.9f}; k2 = {k2:.9f}; "
                   f"m2 = {m2:.9f}; y{i + 1} = {y1:.9f}; y'{i + 1} = {v1:.9f}")
        y, v, t = y1, v1, t + h
        ys.append(y)
        vs.append(v)
    return ys, vs, det

def _edo_rk2(f, y0, h, n):
    ys, det = [], []
    y, t = y0, 0.0
    for i in range(n):
        k = h * f(t, y)
        y1 = y + (k + h * f(t + h, y + k)) / 2
        det.append(f"Paso {i + 1}: k = {k:.9f}; "
                   f"y{i + 1} = {y:.9f} + ½({k:.9f} + {h * f(t + h, y + k):.9f}) "
                   f"= {y1:.9f}")
        y, t = y1, t + h
        ys.append(y)
    return ys, det

def _edo_rk3(f, y0, h, n):
    ys, det = [], []
    y, t = y0, 0.0
    for i in range(n):
        k = h * f(t, y)
        l = h * f(t + h / 2, y + k / 2)
        m = h * f(t + h, y - k + 2 * l)
        y1 = y + (k + 4 * l + m) / 6
        det.append(f"Paso {i + 1}: k = {k:.9f}; l = {l:.9f}; m = {m:.9f}; "
                   f"y{i + 1} = {y:.9f} + (k + 4l + m)/6 = {y1:.9f}")
        y, t = y1, t + h
        ys.append(y)
    return ys, det

def _edo_rk4(f, y0, h, n):
    ys, det = [], []
    y, t = y0, 0.0
    for i in range(n):
        k = h * f(t, y)
        l = h * f(t + h / 2, y + k / 2)
        j = h * f(t + h / 2, y + l / 2)
        m = h * f(t + h, y + j)
        y1 = y + (k + 2 * l + 2 * j + m) / 6
        det.append(f"Paso {i + 1}: k = {k:.9f}; l = {l:.9f}; m = {j:.9f}; "
                   f"n = {m:.9f}; y{i + 1} = {y:.9f} + (k + 2l + 2m + n)/6 = {y1:.9f}")
        y, t = y1, t + h
        ys.append(y)
    return ys, det

def _edo_rk4_38(f, y0, h, n):
    ys, det = [], []
    y, t = y0, 0.0
    for i in range(n):
        k = h * f(t, y)
        l = h * f(t + h / 3, y + k / 3)
        j = h * f(t + 2 * h / 3, y - k / 3 + l)
        m = h * f(t + h, y + k - l + j)
        y1 = y + (k + 3 * l + 3 * j + m) / 8
        det.append(f"Paso {i + 1}: k = {k:.9f}; l = {l:.9f}; m = {j:.9f}; "
                   f"n = {m:.9f}; y{i + 1} = {y:.9f} + (k + 3l + 3m + n)/8 = {y1:.9f}")
        y, t = y1, t + h
        ys.append(y)
    return ys, det

def _campos_y(ys):
    return tuple(f"y{i + 1}" for i in range(len(ys)))

def edo(m, d, r, variante=0):
    if m == 0:
        tpl = ANCLAS["Euler hacia adelante"][variante % 3]
        A, B, C = tpl["A"], tpl["B"], tpl["C"]
        if r is None:
            A2, B2, C2, y0, h = A, B, C, tpl["y0"], tpl["h"]
        else:
            A2, B2, C2 = r.choice([(3, -5, 1), (2, 3, 1), (4, -6, 2),
                                   (2, -4, 1), (3, 4, -1), (5, -7, 2)])
            y0 = r.choice([1.0, 1.5, 2.0, 2.5, 3.0])
            h = r.choice([0.2, 0.25, 0.3])
        f = _f_lineal(-B2, -C2, A2)
        n = 2 + d
        ys, det = _edo_euler_adelante(f, y0, h, n)
        texto = (f"Ejemplo. {_ecuacion_edo(A2, B2, C2)}, y0 = {_g(y0)}, h = {_g(h)}. "
                 "Despejar y' y calcular y1. Para encontrar y2 se consideran "
                 f"y0 = y1 y t1 = t0 + h. Realiza {n} pasos con t0 = 0.")
        revision = (f"Despejar y': y' = ({-B2}yt {_con_signo(-C2, '')})/{A2}. "
                    + " ".join(det))
        # Comprobación: y1 tras el primer paso (y0 + h·f(y0, t0)).
        comp = ("y1 — primer paso: y0 + h·f(t0, y0)", ys[0])
        # Segunda comprobación: y2, el segundo paso.
        comp2 = ("y2 — segundo paso: y1 + h·f(t1, y1)", ys[1])
        dato = f"Dato: y0 = {_g(y0)}, h = {_g(h)}, t0 = 0."
        return Reto(texto, _campos_y(ys), tuple(ys), revision, comp, dato, comp2)
    if m == 1:
        tpl = ANCLAS["Euler modificado"][variante % 3]
        if r is None:
            A2, B2, D2, y0, h = tpl["A"], tpl["B"], tpl["D"], tpl["y0"], tpl["h"]
            dado = y0 if tpl["dado"] else None
        else:
            A2, B2, D2 = r.choice([(2, 3, 1), (3, 2, 1), (2, 4, 1),
                                   (4, 3, 2), (3, 4, 1), (2, 3, 2)])
            y0 = r.choice([1.2, 1.5, 2.0, 2.5])
            h = r.choice([0.2, 0.25, 0.3])
            dado = y0 if variante % 3 == 0 else None
        # y' = (−B·y·t − D·y)/A : el último término es D·y, no una constante.
        f = lambda y, t: (-B2 * y * t - D2 * y) / A2
        n = 1 + d
        ys, det = _edo_euler_modificado(f, y0, h, n, dado=dado)
        if dado is not None:
            texto = (f"Ejemplo. {_ecuacion_edo_y(A2, B2, D2)}, y0 = {_g(y0)}, "
                     f"h = {_g(h)}, y1 = {_g(dado)}. Despejar y' y calcular y1.")
            revision = (f"Despejar y': {_despeje_edo_y(A2, B2, D2)}. "
                        "El enunciado da y1 como dato para el corrector. " + " ".join(det))
        else:
            texto = (f"Ejemplo. {_ecuacion_edo_y(A2, B2, D2)}, y0 = {_g(y0)}, "
                     f"h = {_g(h)}. Despejar y' y calcular y1 por el procedimiento "
                     f"predictor–corrector. Realiza {n} paso(s) con t0 = 0.")
            revision = (f"Despejar y': {_despeje_edo_y(A2, B2, D2)}. "
                        + " ".join(det))
        # Comprobación: y1 tras el primer paso (corrector). En la
        # plantilla que da y1 como dato, ese y1 dado es el predictor y
        # la comprobación es el y1 corregido, distinto de él.
        comp = ("y1 — primer paso (corrector: promedio de las dos pendientes)", ys[0])
        # Segunda comprobación: y2, el segundo paso. Si solo hay un
        # paso (Fácil), el predictor del primer paso.
        if len(ys) >= 2:
            comp2 = ("y2 — segundo paso (corrector: promedio de las dos pendientes)", ys[1])
        else:
            comp2 = ("y1 predictor — paso predictor: y0 + h·f(t0, y0)", y0 + h * f(y0, 0.0))
        dato = (f"Dato: y0 = {_g(y0)}, h = {_g(h)}, y1 dado = {_g(dado)}."
                if dado is not None else
                f"Dato: y0 = {_g(y0)}, h = {_g(h)}, t0 = 0.")
        return Reto(texto, _campos_y(ys), tuple(ys), revision, comp, dato, comp2)
    if m == 2:
        tpl = ANCLAS["Euler hacia atrás"][variante % 3]
        if r is None:
            A2, B2, C2, y0, h = tpl["A"], tpl["B"], tpl["C"], tpl["y0"], tpl["h"]
        else:
            A2, B2, C2 = r.choice([(3, -5, 1), (4, -6, 2), (2, -4, 1),
                                   (5, -7, 2), (3, -6, 1)])
            y0 = r.choice([1.0, 1.5, 2.0, 2.5, 3.0])
            h = r.choice([0.2, 0.25, 0.3])
        n = 1 + d
        ys, det = _edo_euler_atras(-B2, -C2, A2, y0, h, n)
        texto = (f"Ejemplo. {_ecuacion_edo(A2, B2, C2)}, y0 = {_g(y0)}, "
                 f"h = {_g(h)}. Despejar y' y calcular y1 por Euler hacia atrás "
                 f"(paso implícito). Realiza {n} paso(s) con t0 = 0.")
        revision = (f"Despejar y': y' = ({-B2}yt {_con_signo(-C2, '')})/{A2}. "
                    + " ".join(det))
        # Comprobación: y1 tras el primer paso (implícito, despejado).
        comp = ("y1 — primer paso: y0 + h·f(t1, y1)", ys[0])
        # Segunda comprobación: y2, el segundo paso. Si solo hay un
        # paso (Fácil), f(y1, t1), la derivada en el punto nuevo.
        if len(ys) >= 2:
            comp2 = ("y2 — segundo paso: y1 + h·f(t1, y1)", ys[1])
        else:
            comp2 = ("f(y1, t1) — derivada en el punto nuevo",
                     (-B2 * ys[0] * h - C2) / A2)
        dato = f"Dato: y0 = {_g(y0)}, h = {_g(h)}, t0 = 0."
        return Reto(texto, _campos_y(ys), tuple(ys), revision, comp, dato, comp2)
    if m == 3:
        tpl = ANCLAS["Runge-Kutta de orden superior"][variante % 3]
        if r is None:
            a, b, y0, v0, h = tpl["a"], tpl["b"], tpl["y0"], tpl["v0"], tpl["h"]
        else:
            a, b = r.choice([(2, 1), (3, 1), (2, 2), (3, 2)])
            y0 = r.choice([1.0, 1.1, 1.2, 1.5])
            v0 = r.choice([0.8, 1.0, 1.2, 1.5])
            h = r.choice([0.2, 0.25])
        n = 1 + d
        ys, vs, det = _edo_rk_superior(a, b, y0, v0, h, n)
        texto = (f"Ejemplo. 2y'' − {_g(2 * a)}y't − {_g(2 * b)}y = 0, y0 = {_g(y0)}, "
                 f"h = {_g(h)}, y'0 = {_g(v0)}. Calcular y1 y y'1. "
                 f"Realiza {n} paso(s) con t0 = 0.")
        revision = (f"Despejar y'': y'' = {a}y't − {b}y; a = {a}, b = {b}, "
                    f"Vn = y'0 = {_g(v0)}, Un = y0 = {_g(y0)}, qn = t0 = 0. "
                    + " ".join(det))
        campos = []
        for i in range(len(ys)):
            campos += [f"y{i + 1}", f"y'{i + 1}"]
        valores = []
        for y, v in zip(ys, vs):
            valores += [y, v]
        # Comprobación: k1 = h·y'0, el primer incremento del sistema
        # (los resultados son y1, y'1, …; k1 no es ninguno de ellos).
        comp = ("k1 — primer incremento: h·y'0", h * v0)
        # Segunda comprobación: m1, el segundo incremento del sistema.
        comp2 = ("m1 — segundo incremento del sistema", -h * b * y0)
        dato = (f"Dato: y0 = {_g(y0)}, y'0 = {_g(v0)}, h = {_g(h)}, "
                "t0 = 0.")
        return Reto(texto, tuple(campos), tuple(valores), revision, comp, dato, comp2)
    if m == 4:
        tpl = ANCLAS["Runge-Kutta de segundo orden"][variante % 3]
        if r is None:
            p, q, y0, h = tpl["p"], tpl["q"], tpl["y0"], tpl["h"]
        else:
            p, q = r.choice([(2, -1), (3, -2), (2, -2), (3, -1), (4, -1)])
            y0 = r.choice([1.0, 1.5, 2.0, 2.5])
            h = r.choice([0.4, 0.5, 0.6])
        f = lambda t, y: p * t * y + q
        n = 1 + d
        # Comprobación: k1 = h·f(t0, y0), el primer incremento de Heun.
        comp = ("k1 — primer incremento: h·f(t0, y0)", h * f(0.0, y0))
        # Segunda comprobación: k2, el segundo incremento de Heun. Si
        # k2 coincide con k1 (el predictor cae en y = 0), se pide y1.
        _k1v = h * f(0.0, y0)
        _k2v = h * f(h, y0 + _k1v)
        if _k2v != _k1v:
            comp2 = ("k2 — segundo incremento: h·f(t1, y0 + k1)", _k2v)
        else:
            comp2 = ("y1 — primer paso: y0 + (k1 + k2)/2", y0 + (_k1v + _k2v) / 2)
        dato = f"Dato: y0 = {_g(y0)}, h = {_g(h)}, t0 = 0."
        ys, det = _edo_rk2(f, y0, h, n)
        texto = (f"Ejemplo. y' − {_g(p)}ty {_con_signo(q, '')} = 0, y0 = {_g(y0)}, "
                 f"h = {_g(h)}. Despejar y' y calcular y1. "
                 f"Realiza {n} paso(s) con t0 = 0.")
        revision = (f"Despejar y': y' = {_g(p)}ty {_con_signo(q, '')}. "
                    "Usa la variante de Heun. " + " ".join(det))
        return Reto(texto, _campos_y(ys), tuple(ys), revision, comp, dato, comp2)
    if m == 5:
        tpl = ANCLAS["Runge-Kutta de tercer orden"][variante % 3]
        if r is None:
            p, q, y0, h = tpl["p"], tpl["q"], tpl["y0"], tpl["h"]
        else:
            p, q = r.choice([(2, 1), (3, 1), (2, 2), (3, 2)])
            y0 = r.choice([1.0, 1.2, 1.5, 2.0])
            h = r.choice([0.2, 0.25, 0.3])
        f = lambda t, y: (p * y * t + q) / (y * y)
        n = 1 + d
        # Comprobación: k1 = h·f(t0, y0), el primer incremento.
        k1 = h * f(0.0, y0)
        comp = ("k1 — primer incremento: h·f(t0, y0)", k1)
        # Segunda comprobación: m, el tercer incremento. Depende de l
        # (m = h·f(h, y0 − k + 2l)), así que pide haber calculado
        # también el segundo incremento. l se descarta: la pendiente
        # cambia poco y quedaba a menos de 0.001 de k1 en algunos casos.
        l2 = h * f(h / 2, y0 + k1 / 2)
        comp2 = ("m — tercer incremento: h·f(h, y0 − k1 + 2·l)",
                 h * f(h, y0 - k1 + 2 * l2))
        dato = f"Dato: y0 = {_g(y0)}, h = {_g(h)}, t0 = 0."
        ys, det = _edo_rk3(f, y0, h, n)
        texto = (f"Ejemplo. y' = ({_g(p)}yt + {_g(q)})/y², y0 = {_g(y0)}, "
                 f"h = {_g(h)}. Calcular y1. Realiza {n} paso(s) con t0 = 0.")
        revision = f"y' = ({_g(p)}yt + {_g(q)})/y². " + " ".join(det)
        return Reto(texto, _campos_y(ys), tuple(ys), revision, comp, dato, comp2)
    if m in (6, 7):
        nombre = ("Runge-Kutta de cuarto orden" if m == 6
                  else "RK4 por Simpson 1/3")
        # La clave interna se queda ("RK4 por Simpson 1/3"); lo que se
        # muestra lleva el nombre completo.
        nombre_visible = ("Runge-Kutta de cuarto orden" if m == 6
                          else "Runge-Kutta de cuarto orden por Simpson 1/3")
        tpl = ANCLAS[nombre][variante % 3]
        if r is None:
            y0, h = tpl["y0"], tpl["h"]
        else:
            y0 = r.choice([0.1, 0.15, 0.2, 0.25, 0.3, 0.35,
                           0.4, 0.45, 0.5, 0.55, 0.6])
            # Con y0 cerca de 1 la solución crece rápido: h pequeño.
            if y0 >= 0.5:
                h = r.choice([0.05, 0.1])
            elif y0 >= 0.4:
                h = r.choice([0.05, 0.1, 0.15])
            else:
                h = r.choice([0.05, 0.075, 0.1, 0.125, 0.15, 0.175, 0.2, 0.25])
        f = lambda t, y: (y + t) ** 2 / (1 - y)
        # Comprobación: k1 = h·f(t0, y0), el primer incremento.
        k1 = h * f(0.0, y0)
        comp = ("k1 — primer incremento: h·f(t0, y0)", k1)
        # Segunda comprobación: la pendiente en el punto medio,
        # f(t0 + h/2, y0 + k/2), de la que sale el segundo incremento l.
        # Los incrementos k, l, j y m quedan a menos de 0.001 entre sí
        # cuando la pendiente cambia poco (1 de cada 25 casos), así que
        # no distinguen; la pendiente sí está separada de k1 (mín.
        # 0.017 en 600 casos) y de y1 (mín. 0.003).
        comp2 = ("f(t0 + h/2, y0 + k/2) — pendiente en el punto medio",
                 f(h / 2, y0 + k1 / 2))
        dato = f"Dato: y0 = {_g(y0)}, h = {_g(h)}, t0 = 0."
        # El libro hace un solo paso para RK4: con más pasos la solución
        # se acerca a la singularidad y = 1 y deja de ser un problema útil.
        ys, det = _edo_rk4(f, y0, h, 1)
        texto = (f"Ejemplo. y' = (y + t)²/(1 − y), y0 = {_g(y0)}, h = {_g(h)}. "
                 f"Calcular y1. Usa {nombre_visible}.")
        revision = "y' = (y + t)²/(1 − y). " + " ".join(det)
        return Reto(texto, ("y1",), tuple(ys), revision, comp, dato, comp2)
    tpl = ANCLAS["RK4 por Simpson 3/8"][variante % 3]
    if r is None:
        y0, h = tpl["y0"], tpl["h"]
    else:
        y0 = r.choice([0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.4,
                       1.5, 1.8, 2.0, 2.5])
        h = r.choice([0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5])
    f = lambda t, y: -y / (y * y + t)
    # Comprobación: k1 = h·f(t0, y0), el primer incremento.
    k1 = h * f(0.0, y0)
    comp = ("k1 — primer incremento: h·f(t0, y0)", k1)
    # Segunda comprobación: la pendiente en el segundo punto,
    # f(t0 + h/3, y0 + k/3), de la que sale el segundo incremento l.
    # Aquí la pendiente cambia tan poco que k y l difieren menos de
    # 0.001 en 1 de cada 3 casos; la pendiente sí está separada de k1
    # (mín. 0.031 en 600 casos) y de y1 (mín. 0.050).
    comp2 = ("f(t0 + h/3, y0 + k/3) — pendiente en el segundo punto",
             f(h / 3, y0 + k1 / 3))
    dato = f"Dato: y0 = {_g(y0)}, h = {_g(h)}, t0 = 0."
    ys, det = _edo_rk4_38(f, y0, h, 1)
    texto = (f"Ejemplo. y' = −y/(y² + t), y0 = {_g(y0)}, h = {_g(h)}. "
             "Calcular y1. Usa Runge-Kutta de cuarto orden por Simpson 3/8.")
    revision = "y' = −y/(y² + t). " + " ".join(det)
    return Reto(texto, ("y1",), tuple(ys), revision, comp, dato, comp2)

# ---------------------------------------------------------------------------
# Despacho público
# ---------------------------------------------------------------------------

GENERADORES = dict(zip(CATALOGO, [raices, interpolar, ajuste, integral, edo]))

def generar(nombre, dificultad, r=random, variante=0):
    for area, lista in CATALOGO.items():
        if nombre in lista:
            return GENERADORES[area](lista.index(nombre), dificultad, r, variante)
    raise ValueError(nombre)

def original(nombre, n):
    """El problema n (1, 2 o 3) del Word, con sus datos originales.

    Sirve para comprobar que el juego muestra los problemas del libro:
    original("Newton-Raphson", 1) es f(x) = 0.8x² + x − 3 con x0 = 1.
    """
    return generar(nombre, 0, None, variante=n - 1)


# ---------------------------------------------------------------------------
# Notación matemática (como el libro)
# ---------------------------------------------------------------------------

def formatear_matematicas(texto):
    """Convierte la notación de texto plano del banco en HTML matemático.

    Solo transforma patrones matemáticos claros; el resto del texto
    (tablas de datos, unidades como m³/kg o m/s, nombres de reglas
    como "Simpson 1/3") se deja igual. El texto ya viene sin el
    prefijo "Ejemplo." (lo quita app.py). Devuelve HTML seguro: se
    escapa primero y solo se insertan las etiquetas que genera esta
    función. Los textos que produce son solo del banco propio.
    """
    if texto is None:
        return ""
    s = _html.escape(str(texto))

    # --- Nombres completos de Runge-Kutta (sin abreviaturas RK2/RK3/RK4) ---
    # Las menciones dentro de un enunciado o revisión ("Usa RK4 por
    # Simpson 1/3.") se muestran con el nombre completo; las claves
    # internas del código no cambian.
    s = s.replace("RK4 por Simpson 1/3",
                  "Runge-Kutta de cuarto orden por Simpson 1/3")
    s = s.replace("RK4 por Simpson 3/8",
                  "Runge-Kutta de cuarto orden por Simpson 3/8")
    s = _re.sub(r"\bRK4\b", "Runge-Kutta de cuarto orden", s)
    s = _re.sub(r"\bRK3\b", "Runge-Kutta de tercer orden", s)
    s = _re.sub(r"\bRK2\b", "Runge-Kutta de segundo orden", s)

    # --- Delta de diferencias hacia adelante: un solo glifo ---
    # El libro usa ∆ (incremento, U+2206); algunos textos traían Δ
    # (delta griega, U+0394) y se veían dos símbolos distintos para lo
    # mismo. Se normaliza a ∆ antes que las demás reglas.
    s = s.replace("Δ", "∆")

    # --- Integrales: "integral de F dx de A a B" -> ∫ con ambos límites ---
    def _integral(m):
        f, a, b = m.group(1), m.group(2), m.group(3)
        return ('<span class="int"><span class="int-sim">∫</span>'
                '<span class="int-lim"><span class="int-sup">%s</span>'
                '<span class="int-inf">%s</span></span></span> %s dx'
                % (b, a, f))
    s = _re.sub(r"integral de\s+(.+?)\s+dx\s+de\s+(-?[0-9]+(?:\.[0-9]+)?)"
                r"\s+a\s+(-?[0-9]+(?:\.[0-9]+)?)", _integral, s)

    # --- Raíces: sqrt(...) -> √(…) con el radicando subrayado ---
    s = _re.sub(r"sqrt\(([^()]*)\)",
                r'√(<span class="rad">\1</span>)', s)

    # --- Fracciones (antes que potencias: su contenido se formatea después) ---
    # (0.25/2): fracción dentro de paréntesis.
    s = _re.sub(r"\((\d[\d.]*)/(\d[\d.]*)\)",
                r'(<span class="frac"><span class="frac-num">\1</span>'
                r'<span class="frac-den">\2</span></span>)', s)
    # 3·0.25/8: un producto dividido entre un número. El denominador es
    # un número con decimales opcionales: el punto final de la frase no
    # entra en la fracción (3·0.25/8. es 8, no "8.").
    s = _re.sub(r"([\d.]+·[\d.]+)/(\d+(?:\.[0-9]+)?)",
                r'<span class="frac"><span class="frac-num">\1</span>'
                r'<span class="frac-den">\2</span></span>', s)
    # (expresión)/denominador, p. ej. (y+t)²/(1−y), (3yt+1)/y², (e^x−3)/2.5.
    # Si el numerador lleva superíndice, se conservan sus paréntesis
    # ((y+t)², no y+t²); el denominador entre paréntesis los pierde,
    # porque la barra de la fracción ya agrupa (1/(1+x²) -> 1 sobre 1+x²).
    def _frac_paren(m):
        pre = m.group(1) or ""
        num = m.group(2)
        sup = m.group(3) or ""
        den = m.group(4)
        if sup:
            num = "(" + num + ")" + sup
        elif pre:
            num = pre + "(" + num + ")"
        if den.startswith("(") and den.endswith(")"):
            den = den[1:-1]
        return ('<span class="frac"><span class="frac-num">%s</span>'
                '<span class="frac-den">%s</span></span>' % (num, den))
    # El numerador puede llevar la función delante: f(xi)/f'(xi) es
    # f(x_i) entre f'(x_i), no una "f" por delante de la fracción. El
    # denominador puede ser una función con prima: f'(xi). La barra de
    # la fracción ya agrupa, así que "·" no forma parte del denominador
    # ((s−1)/2·∆2 es (s−1)/2 por ∆2, no (s−1)/(2·)).
    s = _re.sub(r"(?:\b([A-Za-z]+)(?:&#x27;|′)?)?\(([^()]+)\)([²³⁴])?/"
                r"(\([^()]+\)|[A-Za-z0-9²³⁴\-−]+(?:&#x27;|′)?"
                r"(?:\([^()]*\))?(?:\.[0-9]+)?)",
                _frac_paren, s)
    # Numerador simple / denominador entre paréntesis o símbolo conocido:
    # 1/(1+x²), 1400/(πr²), 1/Pr, 3/Pr, V/Vc. Un dígito entre dígitos
    # ("Simpson 1/3") y las unidades (m³/kg, m/s, m/seg) no entran.
    def _frac_simple(m):
        num = m.group(1)
        den = m.group(2)
        if den.startswith("(") and den.endswith(")"):
            den = den[1:-1]
        return ('<span class="frac"><span class="frac-num">%s</span>'
                '<span class="frac-den">%s</span></span>' % (num, den))
    s = _re.sub(r"([A-Za-z0-9²³⁴·×\-−]+?)/(\([^()]+\)|Pr|Pc|Tr|Tc|Vc)",
                _frac_simple, s)

    # --- Fracciones compuestas (solo en texto plano, fuera de etiquetas) ---
    # Las reglas anteriores no cubren divisiones con paréntesis anidados
    # ((b − a)/(f(b) − f(a)), (3 − (0))/4) ni divisiones simples como
    # 3600/r², 0.14845/√x, h/2 o ∆2/2. "Simpson 1/3", "Simpson 3/8" y las
    # unidades (m³/kg, m/s, m/seg) se quedan como texto.
    def _solo_texto(s, patron, repl):
        partes = _re.split(r"(<[^>]*>)", s)
        for i in range(0, len(partes), 2):
            partes[i] = patron.sub(repl, partes[i])
        return "".join(partes)

    def _frac_doble(m):
        return ('<span class="frac"><span class="frac-num">%s</span>'
                '<span class="frac-den">%s</span></span>'
                % (m.group(1), m.group(2)))
    _ANID = r"[^()]*(?:\([^()]*\)[^()]*)*"
    # (expresión)/(expresión), con un nivel de paréntesis anidados.
    s = _solo_texto(s, _re.compile(
        r"\((%s)\)/\((%s)\)" % (_ANID, _ANID)), _frac_doble)
    # (expresión)/número, p. ej. (3 − (0))/4 (denominador sin punto final).
    s = _solo_texto(s, _re.compile(
        r"\((%s)\)/(\d+(?:\.[0-9]+)?)" % _ANID), _frac_doble)
    # División simple: 3600/r², 0.14845/√x, h/2, ∆2/2. El numerador es
    # un número (con decimales) o un símbolo que empieza por letra, √ o
    # ∆/∇ — nunca por "·", para no meter el operador dentro de la
    # fracción (s·(s−1)·∆2/2 es s·(s−1)·(∆2/2)).
    def _frac_token(m):
        num, den = m.group(1), m.group(2)
        if (num, den) in {("m³", "kg"), ("m", "s"), ("m", "seg"),
                          ("kg", "m"), ("cm", "s")}:
            return m.group(0)
        return ('<span class="frac"><span class="frac-num">%s</span>'
                '<span class="frac-den">%s</span></span>' % (num, den))
    _NUM = (r"(\d+(?:\.[0-9]+)?|[A-Za-zΔ∆∇√]"
            r"[A-Za-z0-9²³⁴·×Δ∆∇√\-−]*)")
    _DEN = (r"(\d+(?:\.[0-9]+)?|[A-Za-zΔ∆∇√]"
            r"[A-Za-z0-9²³⁴Δ∆∇√]*)")
    s = _solo_texto(s, _re.compile(
        r"(?<!Simpson )" + _NUM + r"/" + _DEN + r"(?! de Simpson)"),
        _frac_token)

    # --- Potencias: ^... -> <sup> (incluye exponentes de varios caracteres) ---
    def _potencia(m):
        exp = m.group(1)
        if exp.startswith("(") and exp.endswith(")"):
            exp = exp[1:-1]
        return "<sup>%s</sup>" % exp
    s = _re.sub(r"\^(\([^()]+\)|[A-Za-z0-9.+\-−]+)", _potencia, s)

    # --- Subíndices ---
    # y'0 -> y′ con subíndice 0 (antes que la regla de primas).
    # Ojo: html.escape ya convirtió ' en &#x27;.
    s = _re.sub(r"\by&#x27;(\d)", r"y′<sub>\1</sub>", s)
    # xi+1, vi+1, ri+1 -> x, v, r con subíndice i+1 (antes que xi/vi/ri).
    s = _re.sub(r"\b([xvr])i\+1\b", r"\1<sub>i+1</sub>", s)
    # xi−1, vi−1, ri−1 -> x, v, r con subíndice i−1 (antes que xi/vi/ri).
    s = _re.sub(r"\b([xvr])i([−\-])1\b", r"\1<sub>i\g<2>1</sub>", s)
    # xi, vi, ri -> x, v, r con subíndice i.
    s = _re.sub(r"\b([xvr])i\b", r"\1<sub>i</sub>", s)
    # xn, yn, tn -> x, y, t con subíndice n (último punto, Newton atrás).
    s = _re.sub(r"\b([xyt])n\b", r"\1<sub>n</sub>", s)
    # Vn, Un, qn (sistema de Runge-Kutta de orden superior) -> Vₙ, Uₙ, qₙ.
    # Solo cuando van seguidos de " =": "Un proyectil" no se toca.
    s = _re.sub(r"\b(Vn|Un|qn)(?= =)",
                lambda m: {"Vn": "V", "Un": "U", "qn": "q"}[m.group(1)] + "<sub>n</sub>", s)
    # Tr, Pr, Pc, Tc, Vc -> Tᵣ, Pᵣ, P꜀, T꜀, V꜀ (también tras un número: 8Tr).
    _SUB2 = {"Tr": ("T", "r"), "Pr": ("P", "r"), "Pc": ("P", "c"),
             "Tc": ("T", "c"), "Vc": ("V", "c")}
    s = _re.sub(r"(?<![A-Za-z])(Tr|Pr|Pc|Tc|Vc)\b",
                lambda m: "%s<sub>%s</sub>" % _SUB2[m.group(1)], s)
    # Vr0-Vr3, D0-D3, L0-L3 (también de dos cifras: x10 -> x con 10).
    s = _re.sub(r"\b([Vv]r)([0-9]+)\b", r"\1<sub>\2</sub>", s)
    s = _re.sub(r"\b([DL])([0-9]+)\b", r"\1<sub>\2</sub>", s)
    # a0-a3, k1, l1, m1, n1, x0, y0, y1, x1, t0, v1-v3, r1-r3, p4
    # (también x10). El (?<!&#) protege la entidad &#x27; (apóstrofe
    # escapado): sin él, la "x27" de la entidad se volvería subíndice
    # y la rompería.
    s = _re.sub(r"\b(?<!&#)([aklmnprtvxy])([0-9]+)\b", r"\1<sub>\2</sub>", s)
    # ∆1-∆4, ∇1-∇4 (diferencias de interpolación).
    s = _re.sub(r"([∆∇])([0-9]+)", r"\1<sub>\2</sub>", s)

    # --- Primas: y'' -> y″, f'(x) -> f′(x), A'(r) -> A′(r) ---
    # (el apóstrofe llega escapado como &#x27;).
    s = _re.sub(r"([A-Za-z])&#x27;&#x27;", r"\1″", s)
    s = _re.sub(r"([A-Za-z])&#x27;", r"\1′", s)

    # --- Símbolos y funciones ---
    s = s.replace("Є", "ε")
    s = _re.sub(r"ε([0-9]+)", r"ε<sub>\1</sub>", s)
    s = _re.sub(r"(\d)[eE]-0*(\d+)", r"\1×10<sup>−\2</sup>", s)
    s = _re.sub(r"\b(arctan|sen|cos|tan|log|[Ll]n)\b",
                r'<span class="fn">\1</span>', s)
    s = s.replace("-&gt;", "→").replace("&lt;=", "≤").replace("&gt;=", "≥")
    s = _re.sub(r"(\w)\*(\w)", r"\1·\2", s)
    s = _re.sub(r"\bpi\b", "π", s)
    return s

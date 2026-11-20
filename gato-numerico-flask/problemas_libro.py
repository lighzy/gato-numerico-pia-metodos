"""Banco de problemas del libro para el Gato Numérico.

Fuente: Métodos Numéricos, 2.ª edición (2020), Zamora / Said / del Ángel,
el libro de la ingeniera Oralia Zamora. Los 87 problemas (29 métodos × 3)
son los del documento "Ejemplos_Gato_Numerico_Libro_Oralia.docx" (v2):
enunciados copiados textualmente del libro y variantes que solo cambian
los datos numéricos. Las respuestas del documento se verificaron con
Python y se reproducen al llamar a metodos.generar(nombre, d, None,
variante=k), que usa los datos originales sin aleatorizar.

ANCLAS[metodo] = [plantilla 1, plantilla 2, plantilla 3]. Cada plantilla
guarda los datos EXACTOS del problema del Word. Cuando metodos.py genera
un reto en modo de juego (con una fuente aleatoria r), toma la plantilla
como base y solo cambia los huecos numéricos dentro de los rangos del
libro; el enunciado, el contexto físico, las unidades y lo que se pide
no cambian.

Notas del libro que el juego respeta:
- "Bisección" se llama "Bisectriz" en el libro (§2.2). En metodos.CATALOGO
  el método se renombró a "Bisectriz".
- En §6.11 el libro despeja y'' = 2y't − y (a = 2, b = 1) y con eso calcula
  y1 = 1.318, y'1 = 0.9952; el juego sigue ese despeje del libro.
- En §6.4 el libro da y1 = 1.2 como dato para el corrector del Euler
  modificado y con él obtiene y1 = 0.939; el juego reproduce ese
  procedimiento para la plantilla 1 de Euler modificado.
- En §5.4 las constantes de Newton-Cotes cerradas y abiertas son las del
  libro (cerradas n=4: α=2/45, pesos 7,32,12,32,7; abiertas n=4: α=6/20,
  pesos 0,11,−14,26,−14,11,0).
"""

# ---------------------------------------------------------------------------
# Ecuaciones no lineales
# ---------------------------------------------------------------------------

# Newton-Raphson. Plantillas 1 y 2: f(x) = a·x^2 + b·x + c, f'(x) = 2a·x + b.
# Plantilla 3: perfil NACA 0012; el espesor es 2·y(x) con
# y(x) = 0.2969·sqrt(x) − 0.126·x − 0.3516·x^2 + 0.2843·x^3 − 0.1015·x^4,
# y se busca x tal que el espesor sea el indicado (y(x) = espesor/2).
NEWTON = [
    {"a": 0.8, "b": 1.0, "c": -3.0, "x0": 1.0, "tol": 1e-6,
     "fuente": "libro §2.4 Newton – Raphson, Ejemplo"},
    {"a": 0.8, "b": 1.0, "c": -4.0, "x0": 1.0, "tol": 1e-6,
     "fuente": "libro §2.4 Newton – Raphson, Ejemplo (variante)"},
    {"espesor": 0.1, "x0": 0.05, "tol": 1e-5,
     "fuente": "libro §2, Ejercicios, ejercicio 2 (NACA 0012)"},
]

# Secante. Plantillas 1 y 2: f(x) = e^(−x) − a·x.
# Plantilla 3: estado de un gas (ecuación reducida de van der Waals).
SECANTE = [
    {"a": 1.0, "x0": 0.0, "x1": 1.0, "tol": 1e-3,
     "fuente": "libro §2.6 Secante, Ejemplo"},
    {"a": 1.2, "x0": 0.0, "x1": 1.0, "tol": 1e-3,
     "fuente": "libro §2.6 Secante, Ejemplo (variante)"},
    {"P": 1.5, "T": 290.0, "Vr0": 0.3, "Vr1": 0.5, "tol": 1e-3,
     "fuente": "libro §2, Ejercicios, ejercicio 3 (estado del gas)"},
]

# Datos críticos de los dos gases del ejercicio del libro.
GAS = [
    {"gas": "A", "Pc": 17.0, "Tc": 812.0, "Vc": 3.8},
    {"gas": "B", "Pc": 9.0, "Tc": 931.0, "Vc": 5.0},
]

# Punto fijo. y = k·x − e^x + C = 0, despeje g(x) = (e^x − C)/k.
PUNTO_FIJO = [
    {"k": 2.0, "C": 2.0, "x0": 0.0, "tol": 1e-8,
     "fuente": "libro §2.3 Punto Fijo, Ejemplo"},
    {"k": 2.0, "C": 3.0, "x0": 0.0, "tol": 1e-8,
     "fuente": "libro §2.3 Punto Fijo, Ejemplo (variante)"},
    {"k": 3.0, "C": 2.0, "x0": 0.0, "tol": 1e-8,
     "fuente": "libro §2.3 Punto Fijo, Ejemplo (variante)"},
]

# Falsa posición. f(x) = x·e^x − C, intervalo [a, b], b fijo.
FALSA_POSICION = [
    {"C": 10.0, "a": 1.0, "b": 2.0, "tol": 1e-3,
     "fuente": "libro §2.5 Falsa Posición, Ejemplo"},
    {"C": 8.0, "a": 1.0, "b": 2.0, "tol": 1e-3,
     "fuente": "libro §2.5 Falsa Posición, Ejemplo (variante)"},
    {"C": 12.0, "a": 1.0, "b": 2.0, "tol": 1e-3,
     "fuente": "libro §2.5 Falsa Posición, Ejemplo (variante)"},
]

# Bisectriz. Plantilla 1: f(x) = x^3 + p·x + C en [a, b].
# Plantilla 2: proyectil a velocidad terminal, f(v) = 1.4e-5·v^1.5
#   + 1.15e-5·v^2 − M·g/1000, g = 9.81 m/s^2.
# Plantilla 3: lata cilíndrica, A(r) = 2π(r+s)^2 + 2V(r+s)/r^2,
#   A'(r) = 4π(r+s) − 2V(r+2s)/r^3 = 0.
BISECTRIZ = [
    {"p": -6.5, "C": 2.0, "a": 0.0, "b": 1.0, "tol": 1e-3,
     "fuente": "libro §2.2 Bisectriz, Ejemplo"},
    {"M": 2.0, "a": 30.0, "b": 40.0, "tol": 1e-3,
     "fuente": "libro §2, Ejercicios, ejercicio 1 (proyectil)"},
    {"V": 1200.0, "s": 0.25, "a": 5.0, "b": 6.0, "tol": 1e-3,
     "fuente": "libro §2, Aplicaciones (lata cilíndrica)"},
]

# ---------------------------------------------------------------------------
# Interpolación
# ---------------------------------------------------------------------------

# Interpolación lineal (Ln). x es el valor a estimar; (a1,a2) es el
# intervalo del inciso a) y (b1,b2) el del inciso b).
LINEAL = [
    {"x": 4, "a1": 2, "a2": 5, "b1": 3, "b2": 5,
     "fuente": "libro §1.1 Interpolación Lineal, Ejemplo"},
    {"x": 6, "a1": 5, "a2": 8, "b1": 5, "b2": 7,
     "fuente": "libro §1.1 Interpolación Lineal, Ejemplo (variante)"},
    {"x": 10, "a1": 8, "a2": 12, "b1": 9, "b2": 11,
     "fuente": "libro §1.1 Interpolación Lineal, Ejemplo (variante)"},
]

# Newton hacia adelante. Tabla uniforme de paso h, evaluar en t.
NEWTON_ADELANTE = [
    {"x1": 2.2, "h": 0.3, "ys": [2.54, 2.82, 3.21], "t": 2.4,
     "fuente": "libro §1.2 Newton hacia Adelante, Ejemplo"},
    {"x1": 1.0, "h": 0.3, "ys": [1.20, 1.55, 1.98], "t": 1.5,
     "fuente": "libro §1.2 Newton hacia Adelante, Ejemplo (variante)"},
    {"x1": 3.0, "h": 0.4, "ys": [4.10, 4.65, 5.40], "t": 3.2,
     "fuente": "libro §1.2 Newton hacia Adelante, Ejemplo (variante)"},
]

# Newton hacia atrás. Tabla uniforme de paso h, evaluar en t (cerca del final).
NEWTON_ATRAS = [
    {"x1": 2.0, "h": 0.4, "ys": [3.10, 3.55, 4.18], "t": 2.6,
     "fuente": "libro §1.3 Newton hacia Atrás, Ejemplo"},
    {"x1": 0.5, "h": 0.4, "ys": [0.80, 1.25, 1.90], "t": 1.1,
     "fuente": "libro §1.3 Newton hacia Atrás, Ejemplo (variante)"},
    {"x1": 4.0, "h": 0.5, "ys": [5.20, 5.85, 6.70], "t": 4.7,
     "fuente": "libro §1.3 Newton hacia Atrás, Ejemplo (variante)"},
]

# Diferencias divididas. Plantillas 1 y 2: tabla en orden decreciente,
# intervalos no uniformes. Plantilla 3: función de Bessel de primera
# clase de orden cero (tabla fija del libro, 5 puntos).
DIFERENCIAS = [
    {"xs": [4.4, 3.7, 3.1], "ys": [-0.68, -1.59, -1.82], "t": 3.5,
     "fuente": "libro §1.4 Newton con Diferencias Divididas, Ejemplo"},
    {"xs": [5.2, 4.6, 3.9], "ys": [1.40, 0.85, 0.30], "t": 4.3,
     "fuente": "libro §1.4 Newton con Diferencias Divididas, Ejemplo (variante)"},
    {"xs": [1.0, 1.3, 1.6, 1.9, 2.2],
     "ys": [0.7651977, 0.620086, 0.4554022, 0.2818186, 0.1103623], "t": 1.5,
     "fuente": "libro Aplicaciones (función de Bessel)"},
]

# Lagrange.
LAGRANGE = [
    {"xs": [1.5, 1.8, 2.1], "ys": [2.10, 2.45, 2.95], "t": 1.9,
     "fuente": "libro §1.5 Lagrange, Ejemplo"},
    {"xs": [0.0, 0.5, 1.0], "ys": [1.00, 1.40, 2.10], "t": 0.7,
     "fuente": "libro §1.5 Lagrange, Ejemplo (variante)"},
    {"xs": [3.5, 4.0, 4.5], "ys": [6.00, 6.80, 7.90], "t": 4.2,
     "fuente": "libro §1.5 Lagrange, Ejemplo (variante)"},
]

# ---------------------------------------------------------------------------
# Mínimos cuadrados (puntos (x, y) del libro, formato del Ejemplo §4.1)
# ---------------------------------------------------------------------------

LINEA_RECTA = [
    {"xs": [1.1, 1.9, 2.4, 4.8, 5.1, 10.5], "ys": [2.5, 2.7, 3.7, 5.2, 6.0, 8.3],
     "fuente": "libro §4.1, Ejemplo (Línea Recta)"},
    {"xs": [0.5, 1.5, 2.5, 3.5, 5.0, 7.0], "ys": [1.8, 2.3, 3.4, 4.0, 5.1, 6.9],
     "fuente": "libro §4.1, Ejemplo (Línea Recta)"},
    {"xs": [2.0, 3.0, 4.0, 6.0, 8.0, 9.0], "ys": [3.1, 4.2, 4.6, 6.5, 7.8, 9.0],
     "fuente": "libro §4.1, Ejemplo (Línea Recta)"},
]

LINEAL_FUNCION = [
    {"xs": [0.0, 0.2, 0.4, 0.6, 0.8, 1.0], "ys": [1.5, 1.9, 2.2, 2.5, 2.9, 3.4],
     "fuente": "libro §4.4 (modelo y ecuaciones normales)"},
    {"xs": [0.1, 0.3, 0.5, 0.7, 0.9, 1.1], "ys": [2.0, 2.4, 2.9, 3.5, 4.2, 5.1],
     "fuente": "libro §4.4 (modelo y ecuaciones normales)"},
    {"xs": [0.0, 0.25, 0.5, 0.75, 1.0, 1.25], "ys": [1.2, 1.6, 2.1, 2.7, 3.4, 4.3],
     "fuente": "libro §4.4 (modelo y ecuaciones normales)"},
]

CUADRATICA_FUNCION = [
    {"xs": [1, 2, 3, 4, 5, 6], "ys": [1.8, 3.8, 6.1, 8.9, 12.3, 16.2],
     "fuente": "libro §4.5 (modelo y ecuaciones normales)"},
    {"xs": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0], "ys": [1.9, 3.2, 4.4, 5.5, 6.7, 7.9],
     "fuente": "libro §4.5 (modelo y ecuaciones normales)"},
    {"xs": [1, 1.5, 2, 3, 4, 5], "ys": [2.5, 3.6, 4.8, 7.2, 10.1, 13.5],
     "fuente": "libro §4.5 (modelo y ecuaciones normales)"},
]

CUADRATICA = [
    {"xs": [1, 2, 3, 4, 5, 6], "ys": [1.9, 3.1, 5.0, 7.4, 10.6, 14.3],
     "fuente": "libro §4.2 (modelo y ecuaciones normales)"},
    {"xs": [0.5, 1.5, 2.5, 3.5, 4.5, 5.5], "ys": [2.2, 2.9, 4.3, 6.2, 8.9, 12.1],
     "fuente": "libro §4.2 (modelo y ecuaciones normales)"},
    {"xs": [1, 2, 3, 4, 5], "ys": [3.0, 4.5, 7.2, 11.0, 16.1],
     "fuente": "libro §4.2 (modelo y ecuaciones normales)"},
]

CUBICA = [
    {"xs": [1, 2, 3, 4, 5, 6], "ys": [0.9, 1.6, 2.8, 5.0, 8.3, 13.2],
     "fuente": "libro §4.3 (modelo y ecuaciones normales)"},
    {"xs": [0, 1, 2, 3, 4, 5], "ys": [1.0, 1.8, 3.2, 5.6, 9.4, 15.0],
     "fuente": "libro §4.3 (modelo y ecuaciones normales)"},
    {"xs": [0.5, 1.0, 1.5, 2.0, 2.5, 3.0], "ys": [2.1, 2.6, 3.5, 5.0, 7.3, 10.6],
     "fuente": "libro §4.3 (modelo y ecuaciones normales)"},
]

# ---------------------------------------------------------------------------
# Integración
# ---------------------------------------------------------------------------

# Newton-Cotes cerrada y abierta. f(x) = u·x^3 + v en [a, b], n = 4 en el libro.
NC_CERRADA = [
    {"u": 3.0, "v": -10.0, "a": -2.0, "b": 2.0, "n": 4,
     "fuente": "libro §5.2, nota al Ejemplo de §5.3"},
    {"u": 3.0, "v": -10.0, "a": 0.0, "b": 2.0, "n": 4,
     "fuente": "libro §5.2, nota al Ejemplo de §5.3 (variante)"},
    {"u": 2.0, "v": -5.0, "a": -2.0, "b": 2.0, "n": 4,
     "fuente": "libro §5.2, nota al Ejemplo de §5.3 (variante)"},
]

NC_ABIERTA = [
    {"u": 3.0, "v": -10.0, "a": -2.0, "b": 2.0, "n": 4,
     "fuente": "libro §5.3, Ejemplo"},
    {"u": 3.0, "v": -10.0, "a": -1.0, "b": 1.0, "n": 4,
     "fuente": "libro §5.3, Ejemplo (variante)"},
    {"u": 2.0, "v": -5.0, "a": -2.0, "b": 2.0, "n": 4,
     "fuente": "libro §5.3, Ejemplo (variante)"},
]

# Simpson 1/3. f(x) = 1/(1+x^2) en [a, b], n = 10 (par) en el libro.
SIMPSON_13 = [
    {"a": 2.0, "b": 3.0, "n": 10, "fuente": "libro §5.5, Ejemplo"},
    {"a": 1.0, "b": 2.0, "n": 10, "fuente": "libro §5.5, Ejemplo (variante)"},
    {"a": 0.0, "b": 1.0, "n": 10, "fuente": "libro §5.5, Ejemplo (variante)"},
]

# Simpson 3/8. f(x) = x^3·e^x en [a, b], n múltiplo de 3.
SIMPSON_38 = [
    {"a": 0.0, "b": 1.0, "n": 3, "fuente": "libro §5.6, Ejemplo"},
    {"a": 0.0, "b": 1.0, "n": 6, "fuente": "libro §5.6, Ejemplo (variante)"},
    {"a": 0.0, "b": 2.0, "n": 3, "fuente": "libro §5.6, Ejemplo (variante)"},
]

# Regla trapezoidal. Plantillas 1 y 3: f(x) = 1/(1+x^2) en [a, b].
# Plantilla 2: prado del agricultor (ancho de la ribera en cada x, h = 0.5,
# unidades en cientos de metros; se piden el área en [0, 2] y hasta x = 2.5).
TRAPEZOIDAL = [
    {"a": 2.0, "b": 3.0, "n": 4, "fuente": "libro §5.1, Ejemplo"},
    {"xs": [0, 0.5, 1.0, 1.5, 2.0, 2.5], "ys": [1.5, 1.8, 2.1, 1.75, 1.3, 1.1],
     "fuente": "libro §5.1, Aplicaciones (prado del agricultor)"},
    {"a": 1.0, "b": 2.0, "n": 4, "fuente": "libro §5.1, Ejemplo (variante)"},
]

# ---------------------------------------------------------------------------
# EDO
# ---------------------------------------------------------------------------

# Euler hacia adelante. A·y' + B·y·t + C = 0  ->  y' = (−B·y·t − C)/A.
# El libro pide y1 y y2.
EULER_ADELANTE = [
    {"A": 3, "B": -5, "C": 1, "y0": 2.0, "h": 0.2,
     "fuente": "libro §6.2, Ejemplo"},
    {"A": 3, "B": -5, "C": 1, "y0": 3.0, "h": 0.2,
     "fuente": "libro §6.2, Ejemplo (variante)"},
    {"A": 4, "B": -6, "C": 2, "y0": 1.0, "h": 0.25,
     "fuente": "libro §6.2, Ejemplo (variante)"},
]

# Euler modificado. A·y' + B·y·t + D·y = 0  ->  y' = (−B·y·t − D·y)/A.
# Ojo: el último término es D·y (no una constante). "dado" indica la
# plantilla 1 del libro: el enunciado da y1 = y0 y el corrector usa ese valor.
EULER_MODIFICADO = [
    {"A": 2, "B": 3, "D": 1, "y0": 1.2, "h": 0.3, "dado": True,
     "fuente": "libro §6.4, Ejemplo"},
    {"A": 2, "B": 3, "D": 1, "y0": 2.0, "h": 0.3, "dado": False,
     "fuente": "libro §6.4, Ejemplo (variante)"},
    {"A": 3, "B": 2, "D": 1, "y0": 1.5, "h": 0.2, "dado": False,
     "fuente": "libro §6.4, Ejemplo (variante)"},
]

# Euler hacia atrás (paso implícito). A·y' + B·y·t + C = 0.
EULER_ATRAS = [
    {"A": 3, "B": -5, "C": 1, "y0": 2.0, "h": 0.2,
     "fuente": "libro §6.3 con la estructura del Ejemplo §6.2"},
    {"A": 3, "B": -5, "C": 1, "y0": 1.0, "h": 0.25,
     "fuente": "libro §6.3 con la estructura del Ejemplo §6.2 (variante)"},
    {"A": 4, "B": -6, "C": 2, "y0": 1.5, "h": 0.2,
     "fuente": "libro §6.3 con la estructura del Ejemplo §6.2 (variante)"},
]

# Runge-Kutta de orden superior. El libro despeja y'' = a·y'·t − b·y
# (a = 2, b = 1 en el ejemplo) y usa Heun sobre el sistema (y, y').
RK_SUPERIOR = [
    {"a": 2, "b": 1, "y0": 1.1, "v0": 1.2, "h": 0.2,
     "fuente": "libro §6.11, Ejemplo"},
    {"a": 2, "b": 1, "y0": 1.0, "v0": 1.0, "h": 0.25,
     "fuente": "libro §6.11, Ejemplo (variante)"},
    {"a": 3, "b": 1, "y0": 1.2, "v0": 0.8, "h": 0.2,
     "fuente": "libro §6.11, Ejemplo (variante)"},
]

# Runge-Kutta de segundo orden (Heun). y' = p·t·y + q.
RK2 = [
    {"p": 2, "q": -1, "y0": 1.0, "h": 0.6, "fuente": "libro §6.6, Ejemplo"},
    {"p": 2, "q": -1, "y0": 2.0, "h": 0.5,
     "fuente": "libro §6.6, Ejemplo (variante)"},
    {"p": 3, "q": -2, "y0": 1.0, "h": 0.4,
     "fuente": "libro §6.6, Ejemplo (variante)"},
]

# Runge-Kutta de tercer orden. y' = (p·y·t + q)/y^2.
RK3 = [
    {"p": 2, "q": 1, "y0": 1.0, "h": 0.25, "fuente": "libro §6.7, Ejemplo"},
    {"p": 2, "q": 1, "y0": 1.0, "h": 0.2,
     "fuente": "libro §6.7, Ejemplo (variante)"},
    {"p": 2, "q": 1, "y0": 2.0, "h": 0.25,
     "fuente": "libro §6.7, Ejemplo (variante)"},
]

# Runge-Kutta de cuarto orden. y' = (y + t)^2/(1 − y).
RK4 = [
    {"y0": 0.4, "h": 0.2, "fuente": "libro §6.9, Ejemplo"},
    {"y0": 0.5, "h": 0.2, "fuente": "libro §6.9, Ejemplo (variante)"},
    {"y0": 0.3, "h": 0.25, "fuente": "libro §6.9, Ejemplo (variante)"},
]

# RK4 por Simpson 1/3. Misma fórmula que RK4 clásico (el libro usa el
# mismo esquema de pesos); cambian los datos.
RK4_S13 = [
    {"y0": 0.6, "h": 0.1, "fuente": "libro §6.9, Ejemplo (variante)"},
    {"y0": 0.2, "h": 0.2, "fuente": "libro §6.9, Ejemplo (variante)"},
    {"y0": 0.5, "h": 0.1, "fuente": "libro §6.9, Ejemplo (variante)"},
]

# RK4 por Simpson 3/8. y' = −y/(y^2 + t).
RK4_S38 = [
    {"y0": 1.0, "h": 0.5, "fuente": "libro §6.10, Ejemplo"},
    {"y0": 1.0, "h": 0.4, "fuente": "libro §6.10, Ejemplo (variante)"},
    {"y0": 2.0, "h": 0.5, "fuente": "libro §6.10, Ejemplo (variante)"},
]

# Índice completo: nombre del método en el juego -> sus 3 plantillas.
ANCLAS = {
    "Newton-Raphson": NEWTON,
    "Secante": SECANTE,
    "Punto fijo": PUNTO_FIJO,
    "Falsa posición": FALSA_POSICION,
    "Bisectriz": BISECTRIZ,
    "Newton hacia adelante": NEWTON_ADELANTE,
    "Newton hacia atrás": NEWTON_ATRAS,
    "Diferencias divididas": DIFERENCIAS,
    "Lagrange": LAGRANGE,
    "Interpolación lineal": LINEAL,
    "Línea recta": LINEA_RECTA,
    "Lineal con función": LINEAL_FUNCION,
    "Cuadrática con función": CUADRATICA_FUNCION,
    "Cuadrática": CUADRATICA,
    "Cúbica": CUBICA,
    "Newton-Cotes cerrada": NC_CERRADA,
    "Newton-Cotes abierta": NC_ABIERTA,
    "Simpson 1/3": SIMPSON_13,
    "Simpson 3/8": SIMPSON_38,
    "Regla trapezoidal": TRAPEZOIDAL,
    "Euler hacia adelante": EULER_ADELANTE,
    "Euler modificado": EULER_MODIFICADO,
    "Euler hacia atrás": EULER_ATRAS,
    "Runge-Kutta de orden superior": RK_SUPERIOR,
    "Runge-Kutta de segundo orden": RK2,
    "Runge-Kutta de tercer orden": RK3,
    "Runge-Kutta de cuarto orden": RK4,
    "RK4 por Simpson 1/3": RK4_S13,
    "RK4 por Simpson 3/8": RK4_S38,
}

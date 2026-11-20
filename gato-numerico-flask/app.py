"""Backend Flask de "Gato Numérico".

Migración a Flask del juego v9 (un solo HTML). La lógica de los
problemas vive en metodos.py (banco de problemas en problemas_libro.py);
aquí solo está la API HTTP que el frontend consume.

Contrato:
- GET  /            -> templates/index.html (el frontend).
- GET  /api/reto?metodo=<nombre exacto del CATALOGO>
                   &dificultad=facil|medio|dificil
                   &variante=0|1|2&semilla=<int>
                   -> 200 JSON con enunciado/datos/dato/se_pide/parte/campos.
                   NO contiene ningún valor de respuesta.
- POST /api/validar {"metodo","dificultad","variante","semilla",
                     "respuestas":{"comprobacion":"1.234","r1":"..."}}
                   -> 200 JSON {"correcto","por_campo","revision"}.
                   Regenera el reto de forma determinista y compara cada
                   campo con tolerancia ±0.001 (se acepta coma o punto).
                   Método/dificultad inválidos o respuestas no numéricas
                   -> 400 JSON {"error": "..."}.

Dificultad: facil -> d=0, medio -> d=1, dificil -> d=2 (los mismos
valores que generar() ya usaba en el juego de escritorio).

Campos por dificultad (la comprobación va siempre primera):
- Fácil:     comprobación + 1 resultado   ("PARTE 1 DE 3")
- Medio:     comprobación + 2 resultados  ("PARTE 2 DE 3")
- Difícil:   comprobación 1 + comprobación 2 + todos los resultados
             ("PROBLEMA COMPLETO")

Los "resultados" son los campos originales de generar() MENOS el campo
que coincide exactamente con una comprobación (p. ej. en raíces la
"Primera aproximación nueva" ES la comprobación 1, así que el único
resultado que queda es la última aproximación; en Euler la "y1" ES la
comprobación 1 y la "y2" ES la comprobación 2, así que quedan y3, y4,
…). La exclusión es por igualdad exacta del número: dos valores
distintos que por casualidad quedan a menos de 0.001 (p. ej. x1 y la
raíz final en la plantilla NACA, que difieren en 0.0005) siguen siendo
dos campos distintos, igual que en el juego original. Si todos los
resultados coincidieran exactamente con las comprobaciones (un
problema degenerado que converge en un paso), se conserva el último
valor para no dejar el reto sin resultados.

La validación devuelve además "valores" (los valores correctos de
cada campo pedido): el alumno ya respondió, y la revisión de fin de
ronda los muestra de todos modos. El frontend los usa para el
reporte de partida.

El texto que se sirve nunca muestra respuestas: el "dato" es solo la
línea de andamiaje con los valores iniciales, y el prefijo "Ejemplo."
de los enunciados del juego de escritorio se quita aquí.
"""
import math
import random
import re

from flask import Flask, jsonify, render_template, request

from metodos import CATALOGO, generar, formatear_matematicas

app = Flask(__name__)

TOLERANCIA = 0.001000001
DIFICULTAD_D = {"facil": 0, "medio": 1, "dificil": 2}
PARTE = {
    "facil": "PARTE 1 DE 3",
    "medio": "PARTE 2 DE 3",
    "dificil": "PROBLEMA COMPLETO",
}
TODOS_METODOS = [m for lista in CATALOGO.values() for m in lista]


# ---------------------------------------------------------------------------
# División del texto del reto en enunciado / datos
# ---------------------------------------------------------------------------
_EJEMPLO_RE = re.compile(r"^Ejemplo\.\s*-?\s*")
_PRADO_RE = re.compile(
    r"Obteniéndose las siguientes coordenadas para los puntos de la "
    r"ribera: (.*?)\. Calcular"
)


def _dividir_texto(texto):
    """Separa el texto del reto en (enunciado, datos).

    - Quita el prefijo "Ejemplo." / "Ejemplo.-" del juego de escritorio.
    - Las líneas "Puntos (x, y)", "Gas …" y "Valores iniciales …" son
      datos; la línea "Evalúa el interpolante…" se quita (lo cubre
      "Se pide").
    - "Valores de apoyo: …" (Falsa posición, Bisectriz) pasa a datos.
    - En el prado del agricultor las coordenadas van en línea: se
      extraen a datos con una expresión regular.
    Si no hay líneas de datos, datos es "".
    """
    t = _EJEMPLO_RE.sub("", texto.strip())
    datos = ""
    m = _PRADO_RE.search(t)
    if m:
        datos = "Puntos de la ribera (x, y): " + m.group(1)
        t = t[: m.start()] + "Calcular" + t[m.end():]
    if "Valores de apoyo:" in t:
        antes, despues = t.split("Valores de apoyo:", 1)
        return antes.strip(), "Valores de apoyo: " + despues.strip()
    enunciado = []
    datos_lineas = []
    for linea in (ln.strip() for ln in t.split("\n")):
        if not linea:
            continue
        if linea.startswith("Valores iniciales") and "Itere hasta que" in linea:
            # Los valores iniciales ya están en el Dato; solo queda la
            # condición de parada, que pertenece al enunciado.
            enunciado.append(linea[linea.index("Itere hasta que"):])
            continue
        if (linea.startswith("Puntos (x, y)") or linea.startswith("Gas ")
                or linea.startswith("Valores iniciales")):
            datos_lineas.append(linea)
        elif linea.startswith("Evalúa el interpolante"):
            continue
        else:
            enunciado.append(linea)
    if datos_lineas:
        datos = "\n".join(datos_lineas)
    enunciado_txt = " ".join(enunciado) if enunciado else t
    return enunciado_txt, datos


# ---------------------------------------------------------------------------
# Campos que se piden según la dificultad
# ---------------------------------------------------------------------------
def _campos_para(reto, dificultad):
    """Devuelve (campos, valores, calcula) para la dificultad pedida.

    campos: lista de dicts {"id","etiqueta","tipo"}; los primeros son
    las comprobaciones. valores: dict id -> valor de referencia.
    calcula: texto "Calcula: …" con lo que se pide en cada campo (la
    descripción de cada comprobación + las etiquetas de los
    resultados), para que el alumno vea QUÉ paso debe hacer a mano
    antes de responder (antes la etiqueta solo decía "Comprobación
    (hazlo a mano)" sin decir cuál).
    En Difícil se piden DOS comprobaciones: la segunda es otro paso
    intermedio real del mismo método (reto.comprobacion2) y el pool de
    resultados excluye los campos que coinciden exactamente con
    cualquiera de las dos. En Fácil y Medio solo hay una comprobación.
    """
    etiqueta_comp, valor_comp = reto.comprobacion
    if dificultad == "dificil":
        etiqueta_comp2, valor_comp2 = reto.comprobacion2
        pool = [(et, v) for et, v in zip(reto.campos, reto.valores)
                if v != valor_comp and v != valor_comp2]
        if not pool:  # problema degenerado: converge en un paso
            pool = [(reto.campos[-1], reto.valores[-1])]
        campos = [{"id": "comprobacion",
                   "etiqueta": "Comprobación 1 (hazlo a mano): " + etiqueta_comp,
                   "tipo": "comprobacion"},
                  {"id": "comprobacion2",
                   "etiqueta": "Comprobación 2 (hazlo a mano): " + etiqueta_comp2,
                   "tipo": "comprobacion2"}]
        valores = {"comprobacion": valor_comp,
                   "comprobacion2": valor_comp2}
        for i, (etiqueta, valor) in enumerate(pool, 1):
            campos.append({"id": "r%d" % i, "etiqueta": etiqueta,
                           "tipo": "resultado"})
            valores["r%d" % i] = valor
        calcula = ", ".join([etiqueta_comp, etiqueta_comp2] +
                            [et for et, _v in pool])
        return campos, valores, calcula
    pool = [(et, v) for et, v in zip(reto.campos, reto.valores)
            if v != valor_comp]
    if not pool:  # problema degenerado: converge en un paso
        pool = [(reto.campos[-1], reto.valores[-1])]
    if dificultad == "facil":
        elegidos = pool[:1]
    else:  # medio (dificil ya se devolvió arriba)
        elegidos = pool[:2]
    campos = [{"id": "comprobacion",
               "etiqueta": "Comprobación (hazlo a mano): " + etiqueta_comp,
               "tipo": "comprobacion"}]
    valores = {"comprobacion": valor_comp}
    for i, (etiqueta, valor) in enumerate(elegidos, 1):
        campos.append({"id": "r%d" % i, "etiqueta": etiqueta,
                       "tipo": "resultado"})
        valores["r%d" % i] = valor
    calcula = ", ".join([etiqueta_comp] + [et for et, _v in elegidos])
    return campos, valores, calcula


def _se_pide(campos):
    return "Se pide: " + ", ".join(c["etiqueta"] for c in campos) + "."


def _generar_reto(metodo, dificultad, variante, semilla):
    return generar(metodo, DIFICULTAD_D[dificultad],
                   random.Random(semilla), variante)


# ---------------------------------------------------------------------------
# Validación de parámetros
# ---------------------------------------------------------------------------
def _error(mensaje, codigo=400):
    return jsonify({"error": mensaje}), codigo


def _leer_params():
    """Lee y valida metodo/dificultad/variante/semilla del query string."""
    metodo = (request.args.get("metodo") or "").strip()
    if metodo not in TODOS_METODOS:
        return None, _error("Método no válido: %r." % metodo)
    dificultad = (request.args.get("dificultad") or "").strip().lower()
    dificultad = {"fácil": "facil", "difícil": "dificil"}.get(
        dificultad, dificultad)
    if dificultad not in DIFICULTAD_D:
        return None, _error(
            "Dificultad no válida: %r (usa facil, medio o dificil)."
            % dificultad)
    variante_raw = (request.args.get("variante") or "0").strip()
    try:
        variante = int(variante_raw)
    except ValueError:
        return None, _error("Variante no válida: %r (usa 0, 1 o 2)."
                            % variante_raw)
    if variante not in (0, 1, 2):
        return None, _error("Variante no válida: %d (usa 0, 1 o 2)."
                            % variante)
    semilla_raw = request.args.get("semilla")
    if semilla_raw is None or semilla_raw.strip() == "":
        semilla = random.randint(0, 2 ** 31 - 1)
    else:
        try:
            semilla = int(semilla_raw.strip())
        except ValueError:
            return None, _error("Semilla no válida: %r (usa un entero)."
                                % semilla_raw)
    return (metodo, dificultad, variante, semilla), None


def _parse_num(raw):
    """Acepta números con punto o coma decimal ("1.234" o "1,234").

    También acepta el signo menos Unicode (−) que usa el juego al
    mostrar números. Devuelve float o lanza ValueError.
    """
    if isinstance(raw, bool):
        raise ValueError("no es un número")
    if isinstance(raw, (int, float)):
        valor = float(raw)
    elif isinstance(raw, str):
        s = raw.strip().replace("\u2212", "-").replace(",", ".")
        if not s:
            raise ValueError("vacío")
        valor = float(s)
    else:
        raise ValueError("no es un número")
    if not math.isfinite(valor):
        raise ValueError("no es un número finito")
    return valor


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/reto")
def api_reto():
    params, err = _leer_params()
    if err is not None:
        return err
    metodo, dificultad, variante, semilla = params
    # Modo demo (?demo=1): el servidor incluye los valores correctos
    # para que el cliente los escriba y los valide. En el modo normal
    # el navegador nunca recibe las respuestas.
    demo = (request.args.get("demo") or "").strip() == "1"
    reto = _generar_reto(metodo, dificultad, variante, semilla)
    enunciado, datos = _dividir_texto(reto.texto)
    campos, valores, calcula = _campos_para(reto, dificultad)
    se_pide = formatear_matematicas(_se_pide(campos))
    campos_fmt = [{"id": c["id"],
                   "etiqueta": formatear_matematicas(c["etiqueta"]),
                   "tipo": c["tipo"]} for c in campos]
    respuesta = {
        "metodo": metodo,
        "dificultad": dificultad,
        "variante": variante,
        "semilla": semilla,
        "enunciado": formatear_matematicas(enunciado),
        "datos": formatear_matematicas(datos),
        "dato": formatear_matematicas(reto.dato) if reto.dato else None,
        "se_pide": se_pide,
        "calcula": formatear_matematicas(calcula),
        "parte": PARTE[dificultad],
        "campos": campos_fmt,
    }
    if demo:
        respuesta["demo_valores"] = valores
    return jsonify(respuesta)


@app.route("/api/validar", methods=["POST"])
def api_validar():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return _error("El cuerpo debe ser un JSON con metodo, dificultad, "
                      "variante, semilla y respuestas.")
    metodo = str(body.get("metodo") or "").strip()
    if metodo not in TODOS_METODOS:
        return _error("Método no válido: %r." % metodo)
    dificultad = str(body.get("dificultad") or "").strip().lower()
    dificultad = {"fácil": "facil", "difícil": "dificil"}.get(
        dificultad, dificultad)
    if dificultad not in DIFICULTAD_D:
        return _error("Dificultad no válida: %r (usa facil, medio o dificil)."
                      % dificultad)
    try:
        variante = int(body.get("variante", 0))
    except (TypeError, ValueError):
        return _error("Variante no válida (usa 0, 1 o 2).")
    if variante not in (0, 1, 2):
        return _error("Variante no válida: %d (usa 0, 1 o 2)." % variante)
    try:
        semilla = int(body.get("semilla", 0))
    except (TypeError, ValueError):
        return _error("Semilla no válida (usa un entero).")
    respuestas = body.get("respuestas")
    if not isinstance(respuestas, dict):
        return _error("Faltan las respuestas (objeto con comprobacion, "
                      "r1, …).")
    reto = _generar_reto(metodo, dificultad, variante, semilla)
    campos, valores, _calcula = _campos_para(reto, dificultad)
    por_campo = {}
    for campo in campos:
        cid = campo["id"]
        if cid not in respuestas:
            return _error("Falta la respuesta del campo %r." % cid)
        try:
            dado = _parse_num(respuestas[cid])
        except (ValueError, TypeError):
            return _error("La respuesta del campo %r no es un número: %r."
                          % (cid, respuestas[cid]))
        por_campo[cid] = abs(dado - valores[cid]) <= TOLERANCIA
    correcto = all(por_campo.values())
    etiqueta_comp, valor_comp = reto.comprobacion
    referencias = "; ".join(
        "%s = %.9f" % (c["etiqueta"], valores[c["id"]]) for c in campos)
    if dificultad == "dificil":
        etiqueta_comp2, valor_comp2 = reto.comprobacion2
        revision = formatear_matematicas(
            "Comprobación 1: %s = %.9f.\nComprobación 2: %s = %.9f.\n%s\n"
            "Valores de referencia: %s."
            % (etiqueta_comp, valor_comp, etiqueta_comp2, valor_comp2,
               reto.revision, referencias))
    else:
        revision = formatear_matematicas(
            "Comprobación: %s = %.9f.\n%s\nValores de referencia: %s."
            % (etiqueta_comp, valor_comp, reto.revision, referencias))
    return jsonify({
        "correcto": correcto,
        "por_campo": por_campo,
        "revision": revision,
        # Valores correctos de cada campo pedido (el alumno ya respondió;
        # la revisión los muestra de todos modos). El frontend los usa
        # para el reporte de partida.
        "valores": valores,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)

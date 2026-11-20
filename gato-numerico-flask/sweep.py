"""Barrido de verificación del backend Flask de Gato Numérico.

Para CADA método (29) x dificultad (3) x variante (0,1,2) x semilla
(1, 42) — 522 retos — comprueba vía el test client de Flask:

- /api/reto devuelve 200 con JSON válido y los campos del contrato.
- campos[0] es la comprobación y el número de resultados es 1 (Fácil),
  2 (Medio) o todos (Difícil), del pool de resultados sin la
  comprobación. En Difícil hay DOS comprobaciones (campos[1] es la
  comprobación 2) y el pool excluye los campos que coinciden con
  cualquiera de las dos.
- Todos los valores de referencia son numéricos y finitos; la
  comprobación 2 es distinta de la 1 y no aparece en los textos del
  reto; los valores pedidos en Difícil no se repiten entre sí.
- La comprobación 2 puede coincidir con un campo original (p. ej. y2
  en Euler, o y1 en el respaldo de RK2): en ese caso ese campo sale
  del pool en Difícil (se registra como aviso, no como fallo).
- En enunciado/datos/dato/se_pide no hay "Ejemplo.", ni mención al
  libro ni a Oralia/Zamora.
- La notación matemática llega formateada (∫ con límites, fracciones
  apiladas, superíndices y subíndices reales): no queda ningún "^"
  ni ningún "integral de" sin formatear en los textos.
- El modo normal NUNCA recibe los valores correctos (sin
  "demo_valores" en la respuesta); con ?demo=1 sí los recibe y son
  los valores de referencia.
- La comprobación y cada resultado NO aparecen como subcadena en los
  textos del reto (formatos a 3 y 6 decimales).
- /api/validar acepta los valores exactos de referencia (correcto=true,
  todo por_campo true), también con coma decimal, y rechaza una
  comprobación incorrecta y un resultado incorrecto (correcto=false y
  el campo correspondiente en false, sin afectar a los demás).
  En Difícil rechaza además una comprobación 2 incorrecta, rechaza
  intercambiar las dos comprobaciones entre sí, rechaza usar el valor
  de un resultado como comprobación y rechaza la comprobación de OTRO
  método para el mismo problema (validación cruzada entre métodos).
  La respuesta incluye "valores" con los valores correctos de cada
  campo pedido.
- El mismo reto pedido dos veces devuelve el mismo JSON (determinismo).
- Casos 400: método/dificultad/variante no válidos, respuesta no
  numérica, campo faltante, cuerpo no JSON.
- GET / devuelve 200.

Además comprueba los 87 anclas originales (r=None): valores finitos.

Uso:  python sweep.py   (sale con código 0 si todo pasa, 1 si algo falla)
"""
import json
import math
import random
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0] or ".")

from app import app  # noqa: E402
from metodos import CATALOGO, generar, original, formatear_matematicas  # noqa: E402

METODOS = [m for lista in CATALOGO.values() for m in lista]
DIFICULTADES = ["facil", "medio", "dificil"]
VARIANTES = [0, 1, 2]
SEMILLAS = [1, 42]
TEXTO_PROHIBIDO = ["ejemplo.", "oralia", "zamora", "libro"]

fallos = []
avisos = []
contadores = {"retos": 0, "validar_ok": 0, "validar_rechazos": 0}


def check(cond, mensaje):
    if not cond:
        fallos.append(mensaje)
        print("FALLO:", mensaje)


def pool_esperado(reto, dificultad):
    """Pool de resultados: campos originales menos los que coinciden
    exactamente con una comprobación (igual que app._campos_para).
    En Difícil se excluyen los que coinciden con la comprobación 1 o
    con la 2; en Fácil/Medio, solo con la 1."""
    _, valor_comp = reto.comprobacion
    if dificultad == "dificil":
        _, valor_comp2 = reto.comprobacion2
        pool = [(et, v) for et, v in zip(reto.campos, reto.valores)
                if v != valor_comp and v != valor_comp2]
    else:
        pool = [(et, v) for et, v in zip(reto.campos, reto.valores)
                if v != valor_comp]
    if not pool:
        pool = [(reto.campos[-1], reto.valores[-1])]
    return pool


def n_resultados_esperados(dificultad, pool):
    if dificultad == "facil":
        return min(1, len(pool))
    if dificultad == "medio":
        return min(2, len(pool))
    return len(pool)


def valores_referencia(reto, dificultad):
    pool = pool_esperado(reto, dificultad)
    n = n_resultados_esperados(dificultad, pool)
    refs = {"comprobacion": reto.comprobacion[1]}
    if dificultad == "dificil":
        refs["comprobacion2"] = reto.comprobacion2[1]
    for i, (_et, v) in enumerate(pool[:n], 1):
        refs["r%d" % i] = v
    return refs


def _validar(client, metodo, dificultad, variante, semilla, respuestas):
    return client.post("/api/validar", json={
        "metodo": metodo, "dificultad": dificultad,
        "variante": variante, "semilla": semilla,
        "respuestas": respuestas})


def main():
    client = app.test_client()

    # GET / (placeholder)
    r = client.get("/")
    check(r.status_code == 200, "GET / no devuelve 200")

    for metodo in METODOS:
        for dificultad in DIFICULTADES:
            for variante in VARIANTES:
                for semilla in SEMILLAS:
                    _un_reto(client, metodo, dificultad, variante, semilla)

    # Casos 400
    _casos_400(client)

    # 87 anclas originales (r=None): valores finitos
    for metodo in METODOS:
        for n in (1, 2, 3):
            q = original(metodo, n)
            check(all(math.isfinite(v) for v in q.valores),
                  "ancla no finita: %s #%d %r" % (metodo, n, q.valores))
            check(q.comprobacion[1] == q.comprobacion[1]
                  and math.isfinite(q.comprobacion[1]),
                  "ancla sin comprobación finita: %s #%d" % (metodo, n))
            check(q.comprobacion2[1] == q.comprobacion2[1]
                  and math.isfinite(q.comprobacion2[1]),
                  "ancla sin comprobación 2 finita: %s #%d" % (metodo, n))
            check(q.comprobacion2[1] != q.comprobacion[1],
                  "ancla con comprobación 2 igual a la 1: %s #%d"
                  % (metodo, n))

    print()
    print("Retos verificados: %d" % contadores["retos"])
    print("Validaciones correctas: %d" % contadores["validar_ok"])
    print("Rechazos verificados: %d" % contadores["validar_rechazos"])
    print("Avisos (valores a <0.001 sin ser iguales): %d" % len(avisos))
    for a in avisos[:20]:
        print("  aviso:", a)
    if fallos:
        print("FALLOS: %d" % len(fallos))
        for f in fallos[:30]:
            print(" -", f)
        return 1
    print("TODO OK")
    return 0


def _un_reto(client, metodo, dificultad, variante, semilla):
    contadores["retos"] += 1
    tag = "%s/%s/v%d/s%d" % (metodo, dificultad, variante, semilla)
    url = ("/api/reto?metodo=%s&dificultad=%s&variante=%d&semilla=%d"
           % (metodo, dificultad, variante, semilla))
    r = client.get(url)
    check(r.status_code == 200, "%s: /api/reto %d" % (tag, r.status_code))
    if r.status_code != 200:
        return
    data = r.get_json()
    for campo in ("metodo", "dificultad", "variante", "semilla",
                  "enunciado", "datos", "se_pide", "parte", "campos"):
        check(campo in data, "%s: falta %s en /api/reto" % (tag, campo))
    check(data.get("metodo") == metodo, "%s: metodo distinto" % tag)
    check(data.get("dificultad") == dificultad, "%s: dificultad distinta" % tag)
    check(data.get("variante") == variante, "%s: variante distinta" % tag)
    check(data.get("semilla") == semilla, "%s: semilla distinta" % tag)
    check(data.get("parte") in ("PARTE 1 DE 3", "PARTE 2 DE 3",
                                "PROBLEMA COMPLETO"),
          "%s: parte inválida %r" % (tag, data.get("parte")))
    check("dato" in data, "%s: falta dato" % tag)

    # Referencia directa (misma semilla): debe coincidir con la API.
    reto = generar(metodo, {"facil": 0, "medio": 1, "dificil": 2}[dificultad],
                   random.Random(semilla), variante)
    refs = valores_referencia(reto, dificultad)
    for v in refs.values():
        check(isinstance(v, float) and math.isfinite(v),
              "%s: valor de referencia no numérico %r" % (tag, v))

    # Campos: comprobación primera (+ comprobación 2 en Difícil) y nº
    # de resultados esperado. La etiqueta de cada comprobación lleva
    # su descripción (qué paso hacer a mano) tras ": ".
    campos = data.get("campos") or []
    etiqueta_comp_esp = ("Comprobación 1 (hazlo a mano)" if dificultad == "dificil"
                         else "Comprobación (hazlo a mano)")
    check(len(campos) >= 1 and campos[0].get("id") == "comprobacion"
          and campos[0].get("tipo") == "comprobacion"
          and campos[0].get("etiqueta") == etiqueta_comp_esp + ": "
          + formatear_matematicas(reto.comprobacion[0]),
          "%s: primer campo no es la comprobación: %r" % (tag, campos[:1]))
    if dificultad == "dificil":
        check(len(campos) >= 2 and campos[1].get("id") == "comprobacion2"
              and campos[1].get("tipo") == "comprobacion2"
              and campos[1].get("etiqueta") == "Comprobación 2 (hazlo a mano): "
              + formatear_matematicas(reto.comprobacion2[0]),
              "%s: segundo campo no es la comprobación 2: %r" % (tag, campos[:2]))
    else:
        check(all(c.get("id") != "comprobacion2" for c in campos),
              "%s: hay comprobación 2 en %s" % (tag, dificultad))
    # "Calcula:" trae la descripción de cada comprobación (qué paso
    # hacer a mano) + las etiquetas de los resultados.
    check("calcula" in data and isinstance(data.get("calcula"), str)
          and formatear_matematicas(reto.comprobacion[0]) in data["calcula"],
          "%s: calcula no trae la comprobación: %r" % (tag, data.get("calcula")))
    if dificultad == "dificil":
        check(formatear_matematicas(reto.comprobacion2[0]) in data["calcula"],
              "%s: calcula no trae la comprobación 2" % tag)
    # Comprobación 2: finita, distinta de la 1, y sin filtrarse en los
    # textos del reto (en ninguna dificultad).
    _e2, v2 = reto.comprobacion2
    check(isinstance(v2, float) and math.isfinite(v2),
          "%s: comprobación 2 no numérica %r" % (tag, v2))
    check(v2 != reto.comprobacion[1],
          "%s: comprobación 2 igual a la 1 (%r)" % (tag, v2))
    if v2 in reto.valores:
        avisos.append("%s: comprobación 2 %r coincide con un campo "
                      "original (sale del pool en Difícil)" % (tag, v2))
    pool = pool_esperado(reto, dificultad)
    n_esp = n_resultados_esperados(dificultad, pool)
    res_campos = [c for c in campos if c.get("tipo") == "resultado"]
    check(len(res_campos) == n_esp,
          "%s: %d resultados, se esperaban %d" % (tag, len(res_campos), n_esp))
    check([c.get("id") for c in res_campos]
          == ["r%d" % i for i in range(1, n_esp + 1)],
          "%s: ids de resultados raros: %r" % (tag, res_campos))
    # Las etiquetas de resultado son las de generar(), formateadas.
    check([c.get("etiqueta") for c in res_campos]
          == [formatear_matematicas(et) for et, _v in pool[:n_esp]],
          "%s: etiquetas de resultado distintas de generar()" % tag)
    check(data.get("se_pide", "").startswith("Se pide: "),
          "%s: se_pide no empieza con 'Se pide: '" % tag)
    # El modo normal nunca recibe los valores correctos.
    check("demo_valores" not in data,
          "%s: el modo normal expone demo_valores" % tag)

    # Textos: sin "Ejemplo.", sin libro/Oralia; sin valores de respuesta;
    # notación matemática formateada (sin ^ ni "integral de" sin formatear).
    textos = {k: (data.get(k) or "") for k in
              ("enunciado", "datos", "dato", "se_pide")}
    for k, txt in textos.items():
        bajo = txt.casefold()
        for prohibido in TEXTO_PROHIBIDO:
            check(prohibido not in bajo,
                  "%s: %s contiene %r: %r" % (tag, k, prohibido, txt[:160]))
        check("^" not in txt,
              "%s: %s tiene un ^ sin formatear: %r" % (tag, k, txt[:160]))
        check("integral de" not in bajo,
              "%s: %s tiene 'integral de' sin formatear: %r"
              % (tag, k, txt[:160]))
        for _nombre, v in refs.items():
            for fmt in ("%.3f", "%.6f"):
                check(fmt % v not in txt,
                      "%s: %s contiene el valor %s (%s)"
                      % (tag, k, fmt % v, txt[:160]))
    # La comprobación 2 tampoco se filtra en los textos (en ninguna
    # dificultad, aunque en Fácil/Medio no se pida).
    for k, txt in textos.items():
        for fmt in ("%.3f", "%.6f"):
            check(fmt % v2 not in txt,
                  "%s: %s contiene la comprobación 2 (%s)"
                  % (tag, k, fmt % v2))
    # Modo demo (?demo=1): sí recibe los valores correctos (muestra
    # representativa: variante 0, semilla 1 de cada método/dificultad).
    if variante == 0 and semilla == 1:
        rd = client.get(url + "&demo=1")
        check(rd.status_code == 200, "%s: /api/reto?demo=1 %d"
              % (tag, rd.status_code))
        if rd.status_code == 200:
            dd = rd.get_json()
            check("demo_valores" in dd,
                  "%s: demo=1 no trae demo_valores" % tag)
            if "demo_valores" in dd:
                for cid, v in refs.items():
                    check(abs(dd["demo_valores"].get(cid, float("nan")) - v)
                          < 1e-12,
                          "%s: demo_valores[%s] distinto de la referencia"
                          % (tag, cid))
    # Aviso (no fallo): comprobación o resultado a <0.001 de otro valor
    # sin ser el mismo número exacto.
    _, cv = reto.comprobacion
    for et, v in zip(reto.campos, reto.valores):
        if v != cv and abs(v - cv) <= 0.001:
            avisos.append("%s: comprobación %.9f a %.6f de %s=%.9f"
                          % (tag, cv, abs(v - cv), et, v))

    # Determinismo: mismo reto dos veces -> mismo JSON.
    r2 = client.get(url)
    check(r2.status_code == 200 and r2.get_json() == data,
          "%s: el reto no es determinista" % tag)

    # /api/validar con los valores exactos (comprobación con coma decimal).
    respuestas_ok = {}
    for cid, v in refs.items():
        s = "%.9f" % v
        respuestas_ok[cid] = s.replace(".", ",") if cid == "comprobacion" else s
    rv = client.post("/api/validar", json={
        "metodo": metodo, "dificultad": dificultad,
        "variante": variante, "semilla": semilla,
        "respuestas": respuestas_ok})
    check(rv.status_code == 200,
          "%s: validar correcto devolvió %d" % (tag, rv.status_code))
    if rv.status_code == 200:
        d = rv.get_json()
        check(d.get("correcto") is True, "%s: validar correcto=false" % tag)
        check(all(d.get("por_campo", {}).get(cid) is True
                  for cid in refs),
              "%s: por_campo no todo true: %r" % (tag, d.get("por_campo")))
        check(isinstance(d.get("valores"), dict)
              and all(abs(d["valores"].get(cid, float("nan")) - v) < 1e-12
                      for cid, v in refs.items()),
              "%s: 'valores' no trae los valores correctos: %r"
              % (tag, d.get("valores")))
        revision = d.get("revision") or ""
        check("%.9f" % refs["comprobacion"] in revision,
              "%s: la revisión no incluye la comprobación" % tag)
        for cid, v in refs.items():
            check(("%.9f" % v) in revision,
                  "%s: la revisión no incluye el valor de %s" % (tag, cid))
        contadores["validar_ok"] += 1

    # Rechazo: comprobación incorrecta (+1.0).
    malas = dict(respuestas_ok)
    malas["comprobacion"] = "%.9f" % (refs["comprobacion"] + 1.0)
    rv = client.post("/api/validar", json={
        "metodo": metodo, "dificultad": dificultad,
        "variante": variante, "semilla": semilla, "respuestas": malas})
    check(rv.status_code == 200, "%s: validar mala comp %d" % (tag, rv.status_code))
    if rv.status_code == 200:
        d = rv.get_json()
        check(d.get("correcto") is False,
              "%s: comprobación incorrecta aceptada" % tag)
        check(d.get("por_campo", {}).get("comprobacion") is False,
              "%s: por_campo.comprobacion no es false" % tag)
        check(all(d.get("por_campo", {}).get(cid) is True
                  for cid in refs if cid != "comprobacion"),
              "%s: un campo correcto se marcó false al fallar la comp" % tag)
        contadores["validar_rechazos"] += 1

    # Rechazo: primer resultado incorrecto (+1.0).
    if "r1" in refs:
        malas = dict(respuestas_ok)
        malas["r1"] = "%.9f" % (refs["r1"] + 1.0)
        rv = client.post("/api/validar", json={
            "metodo": metodo, "dificultad": dificultad,
            "variante": variante, "semilla": semilla, "respuestas": malas})
        check(rv.status_code == 200,
              "%s: validar mal r1 %d" % (tag, rv.status_code))
        if rv.status_code == 200:
            d = rv.get_json()
            check(d.get("correcto") is False,
                  "%s: resultado incorrecto aceptado" % tag)
            check(d.get("por_campo", {}).get("r1") is False,
                  "%s: por_campo.r1 no es false" % tag)
            check(d.get("por_campo", {}).get("comprobacion") is True,
                  "%s: la comprobación se marcó false al fallar r1" % tag)
            contadores["validar_rechazos"] += 1

    # Rechazo: usar el valor de un resultado como comprobación (el
    # alumno que solo sabe el resultado final no pasa). Se salta si el
    # reto degenerado pide el mismo número en ambos campos.
    if "r1" in refs and abs(refs["r1"] - refs["comprobacion"]) > 0.001:
        malas = dict(respuestas_ok)
        malas["comprobacion"] = "%.9f" % refs["r1"]
        rv = _validar(client, metodo, dificultad, variante, semilla, malas)
        check(rv.status_code == 200,
              "%s: validar r1-como-comp %d" % (tag, rv.status_code))
        if rv.status_code == 200:
            d = rv.get_json()
            check(d.get("correcto") is False,
                  "%s: valor de resultado aceptado como comprobación" % tag)
            check(d.get("por_campo", {}).get("comprobacion") is False,
                  "%s: por_campo.comprobacion no es false" % tag)
            contadores["validar_rechazos"] += 1

    # Rechazo cruzado entre métodos: la comprobación de OTRO método
    # para el mismo problema (misma dificultad/variante/semilla) no
    # debe validar. Se busca otro método cuya comprobación difiera
    # en más de 0.01 de la correcta.
    otro_valor = None
    for otro in METODOS:
        if otro == metodo:
            continue
        otro_reto = generar(otro, {"facil": 0, "medio": 1, "dificil": 2}[dificultad],
                            random.Random(semilla), variante)
        if abs(otro_reto.comprobacion[1] - refs["comprobacion"]) > 0.01:
            otro_valor = otro_reto.comprobacion[1]
            break
    if otro_valor is not None:
        malas = dict(respuestas_ok)
        malas["comprobacion"] = "%.9f" % otro_valor
        rv = _validar(client, metodo, dificultad, variante, semilla, malas)
        check(rv.status_code == 200,
              "%s: validar comp-de-otro-método %d" % (tag, rv.status_code))
        if rv.status_code == 200:
            d = rv.get_json()
            check(d.get("correcto") is False,
                  "%s: comprobación de otro método aceptada" % tag)
            check(d.get("por_campo", {}).get("comprobacion") is False,
                  "%s: por_campo.comprobacion no es false" % tag)
            contadores["validar_rechazos"] += 1

    # Rechazos propios de Difícil (dos comprobaciones).
    if dificultad == "dificil":
        # Comprobación 2 incorrecta (+1.0).
        malas = dict(respuestas_ok)
        malas["comprobacion2"] = "%.9f" % (refs["comprobacion2"] + 1.0)
        rv = _validar(client, metodo, dificultad, variante, semilla, malas)
        check(rv.status_code == 200,
              "%s: validar mala comp2 %d" % (tag, rv.status_code))
        if rv.status_code == 200:
            d = rv.get_json()
            check(d.get("correcto") is False,
                  "%s: comprobación 2 incorrecta aceptada" % tag)
            check(d.get("por_campo", {}).get("comprobacion2") is False,
                  "%s: por_campo.comprobacion2 no es false" % tag)
            check(d.get("por_campo", {}).get("comprobacion") is True,
                  "%s: la comprobación 1 se marcó false al fallar la 2" % tag)
            contadores["validar_rechazos"] += 1
        # Intercambiar las dos comprobaciones: ninguna debe validar.
        malas = dict(respuestas_ok)
        malas["comprobacion"] = "%.9f" % refs["comprobacion2"]
        malas["comprobacion2"] = "%.9f" % refs["comprobacion"]
        rv = _validar(client, metodo, dificultad, variante, semilla, malas)
        check(rv.status_code == 200,
              "%s: validar comps-intercambiadas %d" % (tag, rv.status_code))
        if rv.status_code == 200:
            d = rv.get_json()
            check(d.get("correcto") is False,
                  "%s: comprobaciones intercambiadas aceptadas" % tag)
            check(d.get("por_campo", {}).get("comprobacion") is False
                  and d.get("por_campo", {}).get("comprobacion2") is False,
                  "%s: por_campo no marca false las dos al intercambiar"
                  % tag)
            contadores["validar_rechazos"] += 1


def _casos_400(client):
    base = "/api/reto?metodo=%s&dificultad=%s&variante=%s&semilla=%s"
    casos = [
        ("método inexistente", base % ("No existe", "facil", "0", "1")),
        ("dificultad mala", base % ("Newton-Raphson", "extremo", "0", "1")),
        ("variante 3", base % ("Newton-Raphson", "facil", "3", "1")),
        ("variante no numérica", base % ("Newton-Raphson", "facil", "x", "1")),
        ("semilla no numérica", base % ("Newton-Raphson", "facil", "0", "x")),
        ("sin método", "/api/reto?dificultad=facil"),
    ]
    for nombre, url in casos:
        r = client.get(url)
        check(r.status_code == 400, "400 %s: devolvió %d" % (nombre, r.status_code))
        check(isinstance(r.get_json(), dict) and "error" in r.get_json(),
              "400 %s: sin JSON {error}" % nombre)

    bueno = {"metodo": "Newton-Raphson", "dificultad": "facil",
             "variante": 0, "semilla": 1,
             "respuestas": {"comprobacion": "1", "r1": "1"}}
    bueno_dificil = {"metodo": "Newton-Raphson", "dificultad": "dificil",
                     "variante": 0, "semilla": 1,
                     "respuestas": {"comprobacion": "1", "r1": "1"}}
    for nombre, body in [
        ("validar método malo", dict(bueno, metodo="No existe")),
        ("validar dificultad mala", dict(bueno, dificultad="extremo")),
        ("validar variante mala", dict(bueno, variante=5)),
        ("validar respuesta no numérica",
         dict(bueno, respuestas={"comprobacion": "abc", "r1": "1"})),
        ("validar respuesta vacía",
         dict(bueno, respuestas={"comprobacion": "", "r1": "1"})),
        ("validar campo faltante",
         dict(bueno, respuestas={"comprobacion": "1"})),
        ("validar sin respuestas", {k: v for k, v in bueno.items()
                                    if k != "respuestas"}),
        ("validar dificil sin comprobacion2",
         dict(bueno_dificil, respuestas={"comprobacion": "1", "r1": "1"})),
    ]:
        r = client.post("/api/validar", json=body)
        check(r.status_code == 400, "400 %s: devolvió %d" % (nombre, r.status_code))
        check(isinstance(r.get_json(), dict) and "error" in r.get_json(),
              "400 %s: sin JSON {error}" % nombre)
    r = client.post("/api/validar", data="esto no es json",
                    content_type="application/json")
    check(r.status_code == 400, "400 cuerpo no JSON: devolvió %d" % r.status_code)


if __name__ == "__main__":
    sys.exit(main())

"use strict";
/* ==========================================================================
   GATO NUMÉRICO v9 — versión web (un solo archivo)
   Problemas de métodos numéricos con variantes que cambian solo los datos.
   El enunciado, el contexto, las unidades y lo que se pide no cambian.
   Tolerancia ±0.001.
   ========================================================================== */

/* ---------------- Catálogo de métodos ---------------- */
const CATALOGO = {
  "Ecuaciones no lineales": ["Newton-Raphson", "Secante", "Punto fijo", "Falsa posición", "Bisectriz"],
  "Interpolación": ["Newton hacia adelante", "Newton hacia atrás", "Diferencias divididas", "Lagrange", "Interpolación lineal"],
  "Mínimos cuadrados": ["Línea recta", "Lineal con función", "Cuadrática con función", "Cuadrática", "Cúbica"],
  "Integración": ["Newton-Cotes cerrada", "Newton-Cotes abierta", "Simpson 1/3", "Simpson 3/8", "Regla trapezoidal"],
  "EDO": ["Euler hacia adelante", "Euler modificado", "Euler hacia atrás", "Runge-Kutta de orden superior", "Runge-Kutta de segundo orden", "Runge-Kutta de tercer orden", "Runge-Kutta de cuarto orden", "RK4 por Simpson 1/3", "RK4 por Simpson 3/8"]
};
const NOMBRES = Object.values(CATALOGO).flat();
const NIVELES = ["Inicial", "Intermedio", "Avanzado"];
/* Nombres originales de cada método (sección + nombre), para el catálogo. */
const LIBRO = {
  "Newton-Raphson": "§2.4 Newton–Raphson",
  "Secante": "§2.6 Secante",
  "Punto fijo": "§2.3 Punto Fijo",
  "Falsa posición": "§2.5 Falsa Posición",
  "Bisectriz": "§2.2 Bisectriz",
  "Newton hacia adelante": "§1.2 Newton hacia Adelante",
  "Newton hacia atrás": "§1.3 Newton hacia Atrás",
  "Diferencias divididas": "§1.4 Newton con Diferencias Divididas",
  "Lagrange": "§1.5 Lagrange",
  "Interpolación lineal": "§1.1 Lineal",
  "Línea recta": "§4.1 Línea Recta",
  "Lineal con función": "§4.4 Lineal con Función",
  "Cuadrática con función": "§4.5 Cuadrática con Función",
  "Cuadrática": "§4.2 Cuadrática",
  "Cúbica": "§4.3 Cúbica",
  "Newton-Cotes cerrada": "§5.2 Newton–Cotes Cerradas",
  "Newton-Cotes abierta": "§5.3 Newton–Cotes Abiertas",
  "Simpson 1/3": "§5.5 Simpson 1/3",
  "Simpson 3/8": "§5.6 Simpson 3/8",
  "Regla trapezoidal": "§5.1 Regla Trapezoidal",
  "Euler hacia adelante": "§6.2 Euler Adelante",
  "Euler modificado": "§6.4 Euler Modificado",
  "Euler hacia atrás": "§6.3 Euler Atrás",
  "Runge-Kutta de orden superior": "§6.11 Runge-Kutta de orden superior",
  "Runge-Kutta de segundo orden": "§6.6 Runge-Kutta de segundo orden",
  "Runge-Kutta de tercer orden": "§6.7 Runge-Kutta de tercer orden",
  "Runge-Kutta de cuarto orden": "§6.8 Runge-Kutta de cuarto orden",
  "RK4 por Simpson 1/3": "§6.9 Runge-Kutta de cuarto orden por Simpson 1/3",
  "RK4 por Simpson 3/8": "§6.10 Runge-Kutta de cuarto orden por Simpson 3/8"
};
/* Nombre que se muestra en la pantalla (sin abreviaturas RK): las claves
   internas se quedan ("RK4 por Simpson 1/3") porque el servidor las usa
   para generar el reto. */
const NOMBRE_VISIBLE = {
  "RK4 por Simpson 1/3": "Runge-Kutta de cuarto orden por Simpson 1/3",
  "RK4 por Simpson 3/8": "Runge-Kutta de cuarto orden por Simpson 3/8"
};
function nombreVisible(n) { return NOMBRE_VISIBLE[n] || n; }
/* Tiempos por defecto (min) y penalización por error (min), por nivel. */
const TIEMPOS_DEFECTO = [25, 30, 60];
const PENALIZACION = [2, 3, 4];
function fmtG(x) {
  if (!isFinite(x)) return String(x);
  if (x === 0) return "0";
  const ax = Math.abs(x);
  if (ax >= 1e-4 && ax < 1e6) return String(Number(x.toPrecision(6)));
  const e = Math.floor(Math.log10(ax));
  const m = x / Math.pow(10, e);
  const ms = String(Number(m.toPrecision(6)));
  const es = (e < 0 ? "-" : "+") + String(Math.abs(e)).padStart(2, "0");
  return ms + "e" + es;
}
/* ---------------- API del servidor (Flask) ----------------
   Los problemas se generan en el servidor: este archivo ya no
   contiene el motor local de problemas. Cada reto se pide con
   GET /api/reto y se valida con POST /api/validar. */
const DIFICULTAD_API = ["facil", "medio", "dificil"];
const PARTE_CLASE = { "PARTE 1 DE 3": "facil", "PARTE 2 DE 3": "medio", "PROBLEMA COMPLETO": "dificil" };
async function pedirReto(nombre, variante, semilla) {
  let url = "/api/reto?metodo=" + encodeURIComponent(nombre) + "&dificultad=" + DIFICULTAD_API[nivel] + "&variante=" + variante + "&semilla=" + semilla;
  if (demoActivo) url += "&demo=1";
  const resp = await fetch(url);
  if (!resp.ok) throw new Error("reto " + resp.status);
  const data = await resp.json();
  return {
    metodo: data.metodo,
    dificultad: data.dificultad,
    variante: data.variante,
    semilla: data.semilla,
    enunciado: data.enunciado,
    datos: data.datos || "",
    dato: data.dato || null,
    andamio: data.dato || null,
    se_pide: data.se_pide,
    pide: data.se_pide,
    pideNivel: data.se_pide,
    calcula: data.calcula || null,
    parte: { etiqueta: data.parte, clase: PARTE_CLASE[data.parte] || "facil", nota: "Responde lo que se pide." },
    campos: data.campos,
    demo_valores: data.demo_valores || null,
    revision: null
  };
}
/* ==========================================================================
   JUEGO
   ========================================================================== */
const LS_KEY = "gato_numerico_html_v1";
const SKINS = {
  "Clásica": { slug: "clasica", x: "#FCEE0A", o: "#00F0FF", tile: "#15152E", regla: "Disponible", siempre: true },
  "Neón": { slug: "neon", x: "#00F0FF", o: "#FF003C", tile: "#0B0B26", regla: "3 victorias" },
  "Circuito": { slug: "circuito", x: "#2BFF88", o: "#B6FF2E", tile: "#04140B", regla: "Una categoría completa" },
  "Dorada": { slug: "dorada", x: "#FFC400", o: "#FF7A00", tile: "#171106", regla: "Gana una partida en Difícil" },
  "Campeón": { slug: "campeon", x: "#FF2EA6", o: "#00F0FF", tile: "#150826", regla: "Las cinco categorías completas" }
};
const LINEAS = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]];

function cargarProgreso() {
  try {
    const raw = localStorage.getItem(LS_KEY);
    if (raw) {
      const p = JSON.parse(raw);
      let tiempos = p.tiempos || TIEMPOS_DEFECTO.slice();
      /* Migración v8: quien tenía los tiempos viejos por defecto (13/10/8) recibe los nuevos. */
      if (JSON.stringify(tiempos) === "[13,10,8]") tiempos = TIEMPOS_DEFECTO.slice();
      return {
        acreditados: p.acreditados || [],
        victorias: p.victorias || 0,
        racha: p.racha || 0,
        skin: p.skin || "Clásica",
        tiempos,
        victoriaAvanzada: !!p.victoriaAvanzada,
        /* Récords personales (migración: los guardados viejos no los
           tienen; partidas parte de las victorias ya logradas y la
           mejor racha parte de la racha actual — mínimos reales, no
           datos inventados; el resto empieza en cero a partir de ahora). */
        partidas: (p.partidas === undefined || p.partidas === null) ? (p.victorias || 0) : p.partidas,
        derrotas: p.derrotas || 0,
        mejorRacha: (p.mejorRacha === undefined || p.mejorRacha === null) ? (p.racha || 0) : p.mejorRacha,
        mejorTiempo: (p.mejorTiempo && typeof p.mejorTiempo.segundos === "number" && typeof p.mejorTiempo.nivel === "number")
          ? { segundos: p.mejorTiempo.segundos, nivel: p.mejorTiempo.nivel } : null,
        tiempoTotal: p.tiempoTotal || 0
      };
    }
  } catch (e) {}
  return { acreditados: [], victorias: 0, racha: 0, skin: "Clásica", tiempos: TIEMPOS_DEFECTO.slice(), victoriaAvanzada: false, partidas: 0, derrotas: 0, mejorRacha: 0, mejorTiempo: null, tiempoTotal: 0 };
}
function guardarProgreso() {
  try { localStorage.setItem(LS_KEY, JSON.stringify(progreso)); } catch (e) {}
}
let progreso = cargarProgreso();

/* Estado de la partida en curso */
let nivel = 0, activo = false, tablero = ["", "", "", "", "", "", "", "", ""];
let ultimoMovimiento = -1;
let jugador = "X", libre = false, actual = null, deadline = 0, timerId = null;
let selCelda = -1, procesando = false;
let retoFallido = false, validando = false, retoToken = 0;
let vista = [], rondaLog = [], rondaInicio = 0, tiempoPerdido = 0;
let reportePartida = null; /* Snapshot del reporte: rondaLog se vacía al iniciar otra partida. */

function $(id) { return document.getElementById(id); }
function esc(s) {
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
function mostrar(id) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("activo"));
  $(id).classList.add("activo");
  window.scrollTo(0, 0);
}
function aplicarSkin() {
  const s = SKINS[progreso.skin] || SKINS["Clásica"];
  const root = document.documentElement.style;
  root.setProperty("--xcolor", s.x);
  root.setProperty("--ocolor", s.o);
  root.setProperty("--tilebg", s.tile);
  document.body.classList.remove("skin-clasica", "skin-neon", "skin-circuito", "skin-dorada", "skin-campeon");
  document.body.classList.add("skin-" + (s.slug || "clasica"));
  document.body.classList.remove("skin-cambio");
  void document.body.offsetWidth;
  document.body.classList.add("skin-cambio");
}
function acreditadosSet() { return new Set(progreso.acreditados); }
function stats() {
  const res = [];
  return res;
}
function actualizarInicio() {
  $("stat-acreditados").textContent = progreso.acreditados.length;
  $("stat-victorias").textContent = progreso.victorias;
  $("stat-racha").textContent = progreso.racha;
  [0, 1, 2].forEach(i => { $("min-" + i).textContent = progreso.tiempos[i] + " min"; });
  document.querySelectorAll(".nivel").forEach(el => {
    el.classList.toggle("sel", parseInt(el.dataset.nivel, 10) === nivel);
  });
  renderHomeSkins();
}
function mmss(seg) {
  seg = Math.max(0, Math.ceil(seg));
  return String(Math.floor(seg / 60)).padStart(2, "0") + ":" + String(seg % 60).padStart(2, "0");
}
function tick() {
  if (!activo) return;
  const queda = (deadline - Date.now()) / 1000;
  $("reloj").textContent = mmss(queda);
  $("reloj").classList.toggle("urgente", queda <= 60 && queda > 0);
  const rm = $("reloj-modal");
  if (rm) { rm.textContent = mmss(queda); rm.classList.toggle("urgente", queda <= 60 && queda > 0); }
  if (queda <= 0) { terminar("Tiempo agotado"); return; }
}
function gana(t, ficha) {
  return LINEAS.some(l => l.every(i => t[i] === ficha));
}
function jugadaCPU(t, cpu, jug) {
  const libres = [];
  t.forEach((v, i) => { if (!v) libres.push(i); });
  for (let i = libres.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    const tmp = libres[i]; libres[i] = libres[j]; libres[j] = tmp;
  }
  for (const ficha of [cpu, jug]) {
    for (const i of libres) {
      const copia = t.slice(); copia[i] = ficha;
      if (gana(copia, ficha)) return i;
    }
  }
  return libres[0];
}
function cpu() { return jugador === "X" ? "O" : "X"; }

function iniciarPartida(esDemo) {
  ocultarSmasher();
  demoActivo = !!esDemo;
  if (!demoActivo) salirDemoSilencioso();
  activo = true;
  tablero = ["", "", "", "", "", "", "", "", ""];
  jugador = "X";
  libre = false;
  vista = [];
  rondaLog = [];
  tiempoPerdido = 0;
  retoFallido = false;
  retoToken++;
  procesando = false;
  selCelda = -1;
  rondaInicio = Date.now();
  deadline = Date.now() + progreso.tiempos[nivel] * 60 * 1000;
  $("nivel-tablero").textContent = NIVELES[nivel].toUpperCase() + "   /   CAMPEONATO";
  $("fichas").textContent = "Tu ficha X      ·      Computadora O";
  $("modal-reto").classList.add("sin-reto");
  $("modal-reto").classList.remove("activo");
  $("reto-espera-txt").textContent = "Resuelve el reto de apertura.";
  mostrar("pantalla-tablero");
  dibujarTablero("Resuelve el reto de apertura.");
  if (timerId) clearInterval(timerId);
  if (!demoActivo) {
    timerId = setInterval(tick, 200);
    tick();
  } else {
    // En la demo el reloj no corre: queda fijo en el tiempo del nivel.
    const fijo = mmss(progreso.tiempos[nivel] * 60);
    $("reloj").textContent = fijo;
    const rm = $("reloj-modal");
    if (rm) rm.textContent = fijo;
  }
  retoApertura();
}
function dibujarTablero(msg) {
  $("mensaje-tablero").textContent = msg;
  const grid = $("grid");
  grid.innerHTML = "";
  tablero.forEach((v, i) => {
    const b = document.createElement("button");
    b.className = "celda" + (v === "X" ? " x" : v === "O" ? " o" : "") + (i === ultimoMovimiento ? " pop" : "") + (actual && i === selCelda ? " sel" : "");
    b.textContent = v || " ";
    if (!v && !actual && activo) { b.setAttribute("data-ghost", jugador); b.classList.add(jugador === "X" ? "gx" : "go"); }
    b.disabled = !!v || !!actual;
    b.addEventListener("click", () => casilla(i));
    grid.appendChild(b);
  });
  ultimoMovimiento = -1;
  $("fichas").textContent = "Tu ficha " + jugador + " · Computadora " + cpu();
  const llenas = tablero.filter(v => v).length;
  const rt2 = $("ronda-txt"); if (rt2) rt2.textContent = "CASILLAS " + llenas + "/9";
  const rc2 = $("racha-chip"); if (rc2) rc2.textContent = "RACHA " + progreso.racha;
  const pips = $("pips");
  if (pips) { Array.prototype.forEach.call(pips.children, (p, i) => { p.className = "pip" + (tablero[i] === "X" ? " x" : tablero[i] === "O" ? " o" : ""); }); }
}
function casilla(i) {
  if (!activo || procesando || tablero[i] || actual) return;
  if (libre) { libre = false; mover(i, true); return; }
  abrirReto(i);
}
function elegirMetodo() {
  const acr = acreditadosSet();
  let pool = NOMBRES.filter(n => !acr.has(n) && vista.indexOf(n) < 0);
  if (!pool.length) pool = NOMBRES.filter(n => vista.indexOf(n) < 0);
  if (!pool.length) { vista = []; pool = NOMBRES.slice(); }
  return pool[Math.floor(Math.random() * pool.length)];
}
async function abrirReto(objetivo) {
  if (procesando) return;
  procesando = true;
  const nombre = elegirMetodo();
  vista.push(nombre);
  const titulo = objetivo === "inicio" ? "RETO DE APERTURA" : objetivo === "empate" ? "DESEMPATE" : "CASILLA " + (objetivo + 1);
  $("reto-titulo").textContent = titulo;
  $("reto-metodo").textContent = nombreVisible(nombre);
  $("reto-dificultad").textContent = nivel === 0 ? "FÁCIL · 2 valores" : nivel === 1 ? "MEDIO · 3 valores" : "DIFÍCIL · problema completo";
  $("reto-dificultad").className = "dificultad-badge " + (nivel === 0 ? "facil" : nivel === 1 ? "medio" : "dificil");
  const miToken = retoToken;
  let retoObj = null, intentos = 0;
  do {
    try {
      retoObj = await pedirReto(nombre, Math.floor(Math.random() * 3), Math.floor(Math.random() * 2147483647));
    } catch (e) {
      retoObj = null;
      break;
    }
    intentos++;
  } while (intentos < 50 && retoObj && rondaLog.some(e => e.firma === firmaDe(retoObj)));
  if (miToken !== retoToken || !activo) { procesando = false; return; }
  if (!retoObj) {
    actual = null;
    retoFallido = true;
    $("reto-problema").innerHTML = "";
    $("reto-campos").innerHTML = "";
    $("reto-error").textContent = "No se pudo cargar el reto. Revisa que el servidor esté prendido.";
    selCelda = -1;
    $("modal-reto").classList.add("activo");
    $("modal-reto").classList.remove("sin-reto");
    procesando = false;
    dibujarTablero($("mensaje-tablero").textContent);
    return;
  }
  retoFallido = false;
  actual = { nombre, reto: retoObj, objetivo, inicio: Date.now() };
  renderProblema(retoObj);
  const campos = $("reto-campos");
  campos.innerHTML = "";
  let h3CompPuesto = false, h3Puesto = false;
  retoObj.campos.forEach((c, i) => {
    if ((c.tipo === "comprobacion" || c.tipo === "comprobacion2") && !h3CompPuesto) {
      const h = document.createElement("h3");
      h.textContent = "Comprobación";
      campos.appendChild(h);
      h3CompPuesto = true;
    }
    if (c.tipo === "resultado" && !h3Puesto) {
      const h = document.createElement("h3");
      h.textContent = "Resultado";
      campos.appendChild(h);
      h3Puesto = true;
    }
    const div = document.createElement("div");
    div.className = "campo";
    const lab = document.createElement("label");
    lab.innerHTML = c.etiqueta;
    const inp = document.createElement("input");
    inp.type = "text";
    inp.inputMode = "decimal";
    inp.autocomplete = "off";
    inp.id = "campo-" + i;
    div.appendChild(lab);
    div.appendChild(inp);
    campos.appendChild(div);
  });
  $("reto-error").textContent = "";
  selCelda = (typeof objetivo === "number") ? objetivo : -1;
  $("modal-reto").classList.add("activo");
  $("modal-reto").classList.remove("sin-reto");
  const first = $("campo-0");
  if (first) first.focus();
  procesando = false;
  dibujarTablero($("mensaje-tablero").textContent);
}
function renderProblema(retoObj) {
  const box = $("reto-problema");
  let html = "";
  if (retoObj.parte) {
    html += '<div class="parte-banner parte-' + esc(retoObj.parte.clase) + '"><div class="parte-titulo">' + esc(retoObj.parte.etiqueta) + '</div><div class="parte-nota">' + esc(retoObj.parte.nota) + "</div></div>";
  }
  // Los textos vienen formateados del servidor (HTML matemático propio),
  // así que se insertan tal cual; las etiquetas de los campos, igual.
  html += '<p class="enunciado">' + retoObj.enunciado + "</p>";
  const d = retoObj.datos;
  const tieneDatos = (typeof d === "string" && d.trim() !== "") || (d && (d.kind === "puntos" || (d.lines && d.lines.length)));
  if (tieneDatos) {
    html += '<div class="datos"><span class="etiqueta">DATOS</span>';
    if (typeof d === "string") {
      d.split("\n").forEach(l => { if (l.trim()) html += "<div>" + l + "</div>"; });
    } else if (d.kind === "puntos") {
      html += '<table class="datos-tabla"><tr><th>x</th><th>y</th></tr>';
      d.xs.forEach((x, i) => {
        html += "<tr><td>" + esc(fmtG(x)) + "</td><td>" + esc(Number(d.ys[i]).toFixed(d.ydec)) + "</td></tr>";
      });
      html += "</table>";
      if (d.extra) d.extra.forEach(l => { html += "<div>" + esc(l) + "</div>"; });
    } else {
      d.lines.forEach(l => { html += "<div>" + esc(l) + "</div>"; });
    }
    html += "</div>";
  }
  if (retoObj.andamio) {
    html += '<p class="dato-dado">' + retoObj.andamio + "</p>";
  }
  // "Calcula:" dice en palabras qué paso a mano se pide en cada campo
  // (la comprobación con su fórmula y los resultados), para que el
  // alumno lo vea antes de responder.
  if (retoObj.calcula) {
    html += '<p class="calcula"><strong>Calcula:</strong> ' + retoObj.calcula + "</p>";
  }
  box.innerHTML = html;
}
function retoApertura() { abrirReto("inicio"); }
/* Adam Smasher aparece SOLO con una respuesta incorrecta (no al ceder el turno). */
function aplicarPenalizacion() {
  const mins = PENALIZACION[nivel];
  deadline -= mins * 60 * 1000; tiempoPerdido += mins;
  const sp = $("smasher-penal");
  if (sp) sp.textContent = "−" + mins + " MIN DE TU TIEMPO";
  const aviso = $("penal-aviso");
  if (aviso) {
    aviso.textContent = "ERROR: −" + mins + " MIN";
    aviso.classList.remove("show"); void aviso.offsetWidth; aviso.classList.add("show");
    setTimeout(() => aviso.classList.remove("show"), 2600);
  }
  [$("reloj"), $("reloj-modal")].forEach(r => {
    if (!r) return;
    r.classList.remove("penalizado"); void r.offsetWidth; r.classList.add("penalizado");
    setTimeout(() => r.classList.remove("penalizado"), 1500);
  });
  tick();
}
function mostrarSmasher() {
  const ov = $("smasher-overlay");
  if (ov) { ov.classList.remove("activo"); void ov.offsetWidth; ov.classList.add("activo"); }
  document.body.classList.remove("smasher-shake");
  void document.body.offsetWidth;
  document.body.classList.add("smasher-shake");
}
function ocultarSmasher() {
  const ov = $("smasher-overlay");
  if (ov) ov.classList.remove("activo");
  document.body.classList.remove("smasher-shake");
}
async function validar(omitido) {
  if (!actual) return;
  if (validando) return;
  const entradas = [];
  let valido = true;
  actual.reto.campos.forEach((_, i) => {
    const el = $("campo-" + i);
    const txt = el ? el.value.trim().replace(",", ".") : "";
    const num = txt === "" ? NaN : Number(txt);
    entradas.push({ txt, num });
    if (!omitido && (!isFinite(num))) valido = false;
  });
  if (!omitido && !valido) { $("reto-error").textContent = "Escribe un número válido en cada campo."; return; }
  const nums = omitido ? [] : entradas.map(e => e.num);
  let ok, data = null;
  if (omitido) {
    ok = false;
  } else {
    validando = true;
    const miToken = retoToken;
    const retoActual = actual.reto;
    const respuestas = {};
    actual.reto.campos.forEach((c, i) => { respuestas[c.id] = entradas[i].num; });
    try {
      const resp = await fetch("/api/validar", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ metodo: actual.nombre, dificultad: DIFICULTAD_API[nivel], variante: retoActual.variante, semilla: retoActual.semilla, respuestas })
      });
      if (!resp.ok) throw new Error("validar " + resp.status);
      data = await resp.json();
    } catch (e) {
      validando = false;
      $("reto-error").textContent = "No se pudo validar la respuesta. Revisa que el servidor esté prendido.";
      return;
    }
    validando = false;
    if (!activo || !actual || miToken !== retoToken) return;
    ok = data.correcto === true;
    if (data.revision) actual.reto.revision = data.revision;
    if (demoActivo && ok) demoEstado("¡Correcto! Comprobación y resultado bien.");
  }
  const crudo = omitido ? "Omitido" : entradas.map(e => e.txt).join(" | ");
  /* Detalle por campo para el reporte de partida: lo que se escribió,
     el valor correcto del servidor y si cada campo estuvo bien. */
  const detalle = actual.reto.campos.map((c, i) => ({
    id: c.id,
    etiqueta: c.etiqueta,
    tipo: c.tipo,
    dado: omitido ? null : (isFinite(entradas[i].num) ? entradas[i].num : null),
    correcto: (!omitido && data && data.valores && data.valores[c.id] !== undefined && data.valores[c.id] !== null) ? data.valores[c.id] : null,
    ok: (!omitido && data && data.por_campo) ? data.por_campo[c.id] === true : false
  }));
  registrar(actual, crudo, ok, detalle, omitido);
  const objetivo = actual.objetivo;
  actual = null;
  procesando = true;
  const panel = $("modal-reto");
  const incorrecto = !omitido && !ok;
  if (!omitido) panel.classList.add(ok ? "flash-ok" : "flash-mal");
  if (incorrecto) { aplicarPenalizacion(); mostrarSmasher(); }
  const reducido = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  /* En la demo la pausa tras un acierto es más larga (1.5 s) para que
     se lea el "¡Correcto!" y se vea el flash verde. */
  const espera = omitido ? 250 : ok ? (demoActivo ? 4000 : 480) : (reducido ? 1100 : 2300);
  setTimeout(() => {
    if (incorrecto) ocultarSmasher();
    panel.classList.remove("flash-ok", "flash-mal", "activo");
    panel.classList.add("sin-reto");
    procesando = false;
    selCelda = -1;
    if (!activo) return;
    if (objetivo === "empate") { terminar(ok ? "Victoria" : "Derrota"); return; }
    if (objetivo === "inicio" && ok) {
      $("modal-ficha").classList.add("activo");
      dibujarTablero("¡Correcto! Elige tu ficha.");
      return;
    }
    mover(objetivo, ok);
  }, espera);
}
function firmaDe(retoObj) { return retoObj.enunciado + " | " + JSON.stringify(retoObj.datos); }
function registrar(act, crudo, ok, detalle, cedido) {
  const segundos = (Date.now() - act.inicio) / 1000;
  /* Sin detalle (reto pendiente al acabar la partida): todo en null. */
  const det = detalle || act.reto.campos.map(c => ({
    id: c.id, etiqueta: c.etiqueta, tipo: c.tipo, dado: null, correcto: null, ok: false
  }));
  rondaLog.push({
    metodo: act.nombre,
    texto: act.reto.enunciado,
    firma: firmaDe(act.reto),
    segundos,
    respuesta: crudo,
    ok,
    referencia: act.reto.valores ? act.reto.campos.map((c, i) => (c.etiqueta || c) + " = " + act.reto.valores[i].toFixed(6)).join(", ") : "",
    revision: act.reto.revision,
    objetivo: act.objetivo,
    nivel,
    detalle: det,
    cedido: !!cedido
  });
  if (ok && progreso.acreditados.indexOf(act.nombre) < 0 && !demoActivo) {
    progreso.acreditados.push(act.nombre);
    guardarProgreso();
    mostrarToast("Método acreditado: " + nombreVisible(act.nombre) + " · " + progreso.acreditados.length + "/29");
  }
}
function mover(celda, ok) {
  if (ok) { tablero[celda] = jugador; ultimoMovimiento = celda; }
  if (gana(tablero, jugador)) { terminar("Victoria"); return; }
  if (tablero.indexOf("") >= 0) {
    let j;
    if (demoActivo) {
      // En la demo la computadora sigue una secuencia fija y sencilla.
      j = demoMovsCPU.length ? demoMovsCPU.shift() : undefined;
      if (j !== undefined) demoEstado("La computadora responde colocando su O…");
    } else {
      j = jugadaCPU(tablero, cpu(), jugador);
    }
    if (j !== undefined) { tablero[j] = cpu(); ultimoMovimiento = j; }
  }
  if (gana(tablero, cpu())) { terminar("Derrota"); return; }
  $("reto-espera-txt").textContent = "Toca una casilla libre para abrir su reto.";
  dibujarTablero(ok ? "Elige una casilla libre." : "Perdiste el turno. La computadora jugó. Elige otra casilla.");
  if (tablero.indexOf("") < 0) abrirReto("empate");
}
function terminar(resultado) {
  if (!activo) return;
  ocultarSmasher();
  activo = false;
  if (timerId) { clearInterval(timerId); timerId = null; }
  if (actual) { registrar(actual, resultado, false); actual = null; }
  /* Snapshot del reporte de partida, antes de que rondaLog se vacíe. */
  reportePartida = {
    resultado,
    nivel,
    tiempoSegundos: (Date.now() - rondaInicio) / 1000,
    tiempoPerdido,
    entradas: rondaLog.map(e => Object.assign({}, e, { detalle: (e.detalle || []).map(d => Object.assign({}, d)) }))
  };
  $("modal-reto").classList.remove("activo");
  $("modal-reto").classList.add("sin-reto");
  procesando = false;
  $("modal-ficha").classList.remove("activo");
  const skinsAntes = Object.keys(SKINS).filter(n => skinDesbloqueado(n));
  /* Récords personales: solo partidas reales (la demo no cuenta).
     Toda partida que no termina en victoria cuenta como derrota, así
     partidas = victorias + derrotas siempre. */
  if (!demoActivo) {
    const duracion = reportePartida.tiempoSegundos;
    progreso.partidas += 1;
    progreso.tiempoTotal += duracion;
    if (resultado === "Victoria") {
      progreso.victorias += 1;
      progreso.racha += 1;
      if (progreso.racha > progreso.mejorRacha) progreso.mejorRacha = progreso.racha;
      if (nivel === 2) progreso.victoriaAvanzada = true;
      if (!progreso.mejorTiempo || duracion < progreso.mejorTiempo.segundos) {
        progreso.mejorTiempo = { segundos: duracion, nivel };
      }
    } else {
      progreso.derrotas += 1;
      progreso.racha = 0;
    }
    guardarProgreso();
  }
  const skinsNuevas = demoActivo ? [] : Object.keys(SKINS).filter(n => skinsAntes.indexOf(n) < 0 && skinDesbloqueado(n));
  if (skinsNuevas.length) mostrarToast("¡Nueva skin desbloqueada: " + skinsNuevas.join(", ") + "!");
  $("resultado-titulo").textContent = demoActivo ? "Fin de la demo" : resultado;
  $("resultado-titulo").classList.toggle("gana", resultado === "Victoria");
  const bOtra = $("btn-otra-vez");
  if (bOtra) bOtra.textContent = demoActivo ? "Jugar de verdad" : "Jugar otra vez";
  const conf = $("confetti");
  if (conf) {
    conf.innerHTML = "";
    if (resultado === "Victoria") {
      const colores = ["#FCEE0A", "#FF003C", "#00F0FF", "#FFFFFF", "#2BFF88"];
      for (let i = 0; i < 90; i++) {
        const p = document.createElement("i");
        if (i % 3 === 0) p.className = "redonda";
        p.style.left = (Math.random() * 100) + "%";
        p.style.background = colores[i % colores.length];
        p.style.animationDelay = (Math.random() * 0.9) + "s";
        p.style.animationDuration = (2.4 + Math.random() * 1.1) + "s";
        p.style.width = (7 + Math.random() * 7) + "px";
        p.style.height = (10 + Math.random() * 8) + "px";
        conf.appendChild(p);
      }
    }
  }
  const lineaGanadora = LINEAS.find(l => { const f = tablero[l[0]]; return f && l.every(i => tablero[i] === f); }) || [];
  let tfHtml = "";
  for (let f = 0; f < 3; f++) {
    tfHtml += "<div class='tf-fila'>";
    for (let c = 0; c < 3; c++) {
      const i = f * 3 + c, v = tablero[i];
      tfHtml += "<div class='tf-celda" + (v === "X" ? " x" : v === "O" ? " o" : "") + (lineaGanadora.indexOf(i) >= 0 ? " gana" : "") + "'>" + (v || "·") + "</div>";
    }
    tfHtml += "</div>";
  }
  $("tablero-final").innerHTML = tfHtml;
  /* Resumen primero: resultado, nivel, tiempo y totales de la
     partida (lo mismo que mostraba el reporte, sin duplicarlo). */
  const aciertos = rondaLog.filter(e => e.ok).length;
  const metodosAcr = metodosAcreditadosPartida({ entradas: rondaLog });
  let resHtml = "<div class='revision-item fin-resumen'>";
  if (demoActivo) resHtml += "<div class='fin-demo'>Demostración · No se guardó progreso ni se acreditó ningún método.</div>";
  resHtml += "<div class='fin-titulo'>" + esc(resultado) + " · " + esc(NIVELES[nivel]) + " · " + mmss(reportePartida.tiempoSegundos) + "</div>";
  resHtml += "<div class='fin-datos'>Retos correctos: " + aciertos + "/" + rondaLog.length +
    " · Métodos acreditados en la partida: " + metodosAcr.length +
    (metodosAcr.length ? " (" + metodosAcr.map(m => esc(nombreVisible(m))).join(", ") + ")" : "") + "</div>";
  if (tiempoPerdido > 0) resHtml += "<div class='fin-datos'>Tiempo perdido por errores: " + tiempoPerdido + " min</div>";
  if (skinsNuevas.length) resHtml += "<div class='fin-datos'>¡Nueva skin desbloqueada: " + skinsNuevas.map(esc).join(", ") + "!</div>";
  resHtml += "</div>";
  $("fin-resumen").innerHTML = resHtml;
  /* Una sola lista, en orden de juego: por casilla, lo dado contra lo
     correcto (comprobaciones y resultados) y, plegados, el problema
     con sus pasos. "Tu respuesta" y "Referencia" ya no se repiten:
     cada campo muestra su dado contra su correcto. */
  const lista = $("lista-revision");
  lista.innerHTML = "";
  if (!rondaLog.length) {
    lista.innerHTML = "<div class='revision-item'>No se jugó ningún reto en esta partida.</div>";
  }
  rondaLog.forEach(e => {
    const det = e.detalle || [];
    const comp1 = det.find(d => d.tipo === "comprobacion" || d.id === "comprobacion");
    const comp2 = det.find(d => d.tipo === "comprobacion2" || d.id === "comprobacion2");
    const resultados = det.filter(d => d.tipo === "resultado");
    const div = document.createElement("div");
    div.className = "revision-item";
    let h = "<b>" + esc(etiquetaObjetivo(e.objetivo)) + "</b> · " + esc(LIBRO[e.metodo] || e.metodo) +
      " · <span class='" + (e.ok ? "ok" : "mal") + "'>" + (e.ok ? "✓" : "✗") + "</span>" +
      (e.cedido ? " · Cedido" : "") + " · " + e.segundos.toFixed(1) + " s";
    h += "<div class='reporte-detalle'>Comprobación 1: " + marcaDetalle(comp1) + "</div>";
    if (nivel === 2) h += "<div class='reporte-detalle'>Comprobación 2: " + marcaDetalle(comp2) + "</div>";
    if (resultados.length) {
      h += "<div class='reporte-detalle'>Resultados: " + resultados.map(r => r.etiqueta + ": " + marcaDetalle(r)).join("; ") + "</div>";
    }
    h += "<details class='rev-detalles'><summary>Ver problema y pasos</summary>" +
      "<div class='rev-problema'>" + e.texto + "</div>" +
      "<div class='pasos'>" + (e.revision || "") + "</div></details>";
    div.innerHTML = h;
    lista.appendChild(div);
  });
  mostrar("pantalla-fin");
  actualizarInicio();
}
/* ---------------- Reporte de partida ---------------- */
function etiquetaObjetivo(o) {
  if (o === "inicio") return "Apertura";
  if (o === "empate") return "Desempate";
  return "Casilla " + (o + 1);
}
function marcaDetalle(d) {
  if (!d || d.dado === null || d.dado === undefined || d.correcto === null || d.correcto === undefined) return "— vs — ✗";
  return fmtG(d.dado) + " vs " + fmtG(d.correcto) + " " + (d.ok ? "✓" : "✗");
}
function textoPlano(html) {
  const tmp = document.createElement("div");
  tmp.innerHTML = html;
  return tmp.textContent;
}
function metodosAcreditadosPartida(rep) {
  const lista = [];
  rep.entradas.forEach(e => { if (e.ok && lista.indexOf(e.metodo) < 0) lista.push(e.metodo); });
  return lista;
}
function textoReporte() {
  const rep = reportePartida;
  if (!rep) return "";
  const aciertos = rep.entradas.filter(e => e.ok).length;
  const metodosAcr = metodosAcreditadosPartida(rep);
  const lineas = [];
  lineas.push("Reporte de partida — Gato Numérico");
  let enc = "Nivel: " + NIVELES[rep.nivel] + " · Resultado: " + rep.resultado + " · Tiempo usado: " + mmss(rep.tiempoSegundos);
  if (rep.tiempoPerdido > 0) enc += " · Tiempo perdido por errores: " + rep.tiempoPerdido + " min";
  lineas.push(enc);
  lineas.push("Retos correctos: " + aciertos + "/" + rep.entradas.length + " · Métodos acreditados en la partida: " + metodosAcr.length + (metodosAcr.length ? " (" + metodosAcr.map(nombreVisible).join(", ") + ")" : ""));
  lineas.push("");
  if (!rep.entradas.length) {
    lineas.push("No se jugó ningún reto en esta partida.");
    return lineas.join("\n");
  }
  rep.entradas.forEach(e => {
    const det = e.detalle || [];
    const comp1 = det.find(d => d.tipo === "comprobacion" || d.id === "comprobacion");
    const comp2 = det.find(d => d.tipo === "comprobacion2" || d.id === "comprobacion2");
    const resultados = det.filter(d => d.tipo === "resultado");
    let l = etiquetaObjetivo(e.objetivo) + " · " + (LIBRO[e.metodo] || e.metodo) + ": Comp. 1: " + marcaDetalle(comp1);
    if (rep.nivel === 2) l += "; Comp. 2: " + marcaDetalle(comp2);
    if (resultados.length) l += "; Resultados: " + resultados.map(r => textoPlano(r.etiqueta) + ": " + marcaDetalle(r)).join("; ");
    l += "; " + (e.ok ? "✓" : "✗") + "; " + e.segundos.toFixed(1) + " s";
    lineas.push(l);
  });
  return lineas.join("\n");
}
function copiarReporte() {
  const texto = textoReporte();
  if (!texto) return;
  const hecho = () => mostrarToast("Reporte copiado");
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(texto).then(hecho, () => copiarReporteFallback(texto, hecho));
  } else {
    copiarReporteFallback(texto, hecho);
  }
}
function copiarReporteFallback(texto, hecho) {
  const ta = document.createElement("textarea");
  ta.value = texto;
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.select();
  try { document.execCommand("copy"); hecho(); }
  catch (err) { mostrarToast("No se pudo copiar el reporte"); }
  document.body.removeChild(ta);
}
let toastTimer = null;
function mostrarToast(msg) {
  const t = $("toast");
  if (!t) return;
  t.textContent = msg;
  t.classList.add("show");
  if (toastTimer) clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.remove("show"), 3400);
}
function renderHomeSkins() {
  const cont = $("home-skins");
  if (!cont) return;
  cont.innerHTML = "";
  Object.keys(SKINS).forEach(nombre => {
    const sk = SKINS[nombre];
    const activa = progreso.skin === nombre;
    const wrap = document.createElement("button");
    wrap.className = "home-skin" + (activa ? " activa" : "");
    wrap.type = "button";
    wrap.appendChild(crearMiniTableroSkin(sk.slug, true));
    const nom = document.createElement("span");
    nom.className = "home-skin-nombre";
    nom.textContent = activa ? nombre + " ✓" : nombre;
    wrap.appendChild(nom);
    wrap.addEventListener("click", () => { renderRecompensas(); mostrar("pantalla-recompensas"); });
    cont.appendChild(wrap);
  });
}
/* ---------------- Recompensas ---------------- */
function skinDesbloqueado(nombre) {
  const s = SKINS[nombre];
  if (s.siempre) return true;
  const acr = acreditadosSet();
  if (nombre === "Neón") return progreso.victorias >= 3;
  if (nombre === "Circuito") return Object.values(CATALOGO).some(v => v.every(m => acr.has(m)));
  if (nombre === "Dorada") return progreso.victoriaAvanzada;
  if (nombre === "Campeón") return acr.size === NOMBRES.length;
  return false;
}
function renderRecompensas() {
  const lista = $("lista-skins");
  lista.innerHTML = "";
  Object.keys(SKINS).forEach(nombre => {
    const s = SKINS[nombre];
    const ok = skinDesbloqueado(nombre);
    const enUso = progreso.skin === nombre;
    const div = document.createElement("div");
    div.className = "skin-card" + (ok ? "" : " bloqueada") + (enUso ? " en-uso" : "");
    const preview = crearMiniTableroSkin(s.slug, false);
    const info = document.createElement("div");
    info.className = "skin-info";
    info.innerHTML = "<div class='nombre'>" + esc(nombre) + (enUso ? " · en uso" : "") + "</div>" +
      "<div class='regla'>" + esc(s.regla) + "</div>" +
      (ok ? "" : "<span class='etiqueta-bloq'>Bloqueada</span>");
    const btn = document.createElement("button");
    btn.className = "btn secundario";
    btn.textContent = enUso ? "En uso" : "Usar";
    btn.disabled = !ok || enUso;
    btn.addEventListener("click", () => {
      progreso.skin = nombre;
      guardarProgreso();
      aplicarSkin();
      renderRecompensas();
    });
    div.appendChild(preview);
    div.appendChild(info);
    div.appendChild(btn);
    lista.appendChild(div);
  });
  const prog = $("progreso-categorias");
  prog.innerHTML = "";
  Object.keys(CATALOGO).forEach(cat => {
    const v = CATALOGO[cat];
    const n = v.filter(m => acreditadosSet().has(m)).length;
    const div = document.createElement("div");
    div.className = "skin-card";
    div.innerHTML = "<div class='skin-info'><div class='nombre'>" + esc(cat) + "</div><div class='regla'>" + n + " / " + v.length + " métodos acreditados</div><div class='barra'><i style='width:" + Math.round(n / v.length * 100) + "%'></i></div></div>";
    prog.appendChild(div);
  });
}
/* ---------------- Catálogo de métodos ---------------- */
function renderMetodos() {
  const cont = $("lista-metodos");
  if (!cont) return;
  cont.innerHTML = "";
  const acr = acreditadosSet();
  Object.keys(CATALOGO).forEach(cat => {
    const v = CATALOGO[cat];
    const n = v.filter(m => acr.has(m)).length;
    const bloque = document.createElement("div");
    bloque.className = "metodo-cat";
    const cab = document.createElement("button");
    cab.className = "metodo-cat-cab";
    cab.type = "button";
    cab.innerHTML = "<span class='metodo-cat-nombre'>" + esc(cat) + "</span>" +
      "<span class='metodo-cat-cuenta'>" + n + "/" + v.length + " acreditados</span>" +
      "<span class='metodo-cat-flecha'>▸</span>";
    const lista = document.createElement("div");
    lista.className = "metodo-lista";
    v.forEach(m => {
      const ok = acr.has(m);
      const fila = document.createElement("div");
      fila.className = "metodo-fila";
      fila.innerHTML = "<span class='metodo-nombre'>" + esc(LIBRO[m] || m) + "</span>" +
        "<span class='metodo-estado " + (ok ? "acr" : "pend") + "'>" + (ok ? "✓ Acreditado" : "Pendiente") + "</span>";
      lista.appendChild(fila);
    });
    cab.addEventListener("click", () => {
      const abierto = bloque.classList.toggle("abierto");
      cab.querySelector(".metodo-cat-flecha").textContent = abierto ? "▾" : "▸";
    });
    bloque.appendChild(cab);
    bloque.appendChild(lista);
    cont.appendChild(bloque);
  });
}
/* ---------------- Mis récords ----------------
   Récords personales calculados del progreso guardado. Se actualizan
   solos al terminar cada partida real (la demo no cuenta) y persisten
   como el resto del progreso. Sin partidas, ceros y guiones limpios. */
function fmtTiempoTotal(seg) {
  seg = Math.max(0, Math.round(seg));
  const h = Math.floor(seg / 3600), m = Math.floor(seg % 3600 / 60), s = seg % 60;
  if (h > 0) return h + ":" + String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
  return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
}
function renderRecords() {
  const cont = $("lista-records");
  if (!cont) return;
  const p = progreso;
  const porc = p.partidas > 0 ? Math.round(p.victorias / p.partidas * 100) + "%" : "—";
  const mejor = p.mejorTiempo ? mmss(p.mejorTiempo.segundos) : "—";
  const mejorSub = p.mejorTiempo ? ("Nivel " + NIVELES[p.mejorTiempo.nivel]) : "sin victorias aún";
  const acr = acreditadosSet();
  const skinsOk = Object.keys(SKINS).filter(n => skinDesbloqueado(n));
  const tiles = [
    ["Partidas jugadas", p.partidas],
    ["Victorias", p.victorias],
    ["Derrotas", p.derrotas],
    ["% de victorias", porc],
    ["Mejor tiempo de victoria", mejor, mejorSub],
    ["Racha actual", p.racha],
    ["Mejor racha", p.mejorRacha],
    ["Tiempo total jugado", fmtTiempoTotal(p.tiempoTotal)]
  ];
  let h = "<div class='records-grid'>";
  tiles.forEach(t => {
    h += "<div class='record'><b>" + t[1] + "</b><span>" + t[0] + "</span>" + (t[2] ? "<small>" + esc(t[2]) + "</small>" : "") + "</div>";
  });
  h += "</div>";
  h += "<h3>Métodos acreditados · " + acr.size + " / 29</h3>";
  Object.keys(CATALOGO).forEach(cat => {
    const v = CATALOGO[cat];
    const n = v.filter(m => acr.has(m)).length;
    h += "<div class='skin-card'><div class='skin-info'><div class='nombre'>" + esc(cat) + "</div><div class='regla'>" + n + " / " + v.length + " métodos acreditados</div><div class='barra'><i style='width:" + Math.round(n / v.length * 100) + "%'></i></div></div></div>";
  });
  h += "<h3>Skins desbloqueadas · " + skinsOk.length + " / 5</h3>";
  Object.keys(SKINS).forEach(nombre => {
    const ok = skinsOk.indexOf(nombre) >= 0;
    h += "<div class='skin-card'><div class='skin-info'><div class='nombre'>" + esc(nombre) + "</div><div class='regla'>" + (ok ? "✓ Desbloqueada" : "Bloqueada · " + esc(SKINS[nombre].regla)) + "</div></div></div>";
  });
  cont.innerHTML = h;
}
/* Mini tableros de vista previa por skin: juegan solos, en bucle.
   Cada tablero muestra SU propia skin (sus colores y efectos): la X
   y la O se colocan solas con la misma jugada de muestra y la X gana
   la diagonal. Un solo temporizador mueve todos los tableros a la vez. */
let previewBoards = [];
let previewPaso = 0;
let previewTimer = null;
function crearMiniTableroSkin(slug, compacto) {
  previewBoards = previewBoards.filter(b => b.isConnected);
  const b = document.createElement("div");
  b.className = "skin-board skin-" + slug + (compacto ? " compacto" : "");
  for (let i = 0; i < 9; i++) {
    const c = document.createElement("div");
    c.className = "sb-celda";
    b.appendChild(c);
  }
  previewBoards.push(b);
  return b;
}
function tickPreviewBoards() {
  previewPaso = (previewPaso + 1) % (MINI_JUGADAS.length + 2);
  const n = Math.min(previewPaso, MINI_JUGADAS.length);
  for (const b of previewBoards) {
    if (!b.isConnected) continue;
    const celdas = b.children;
    for (let i = 0; i < 9; i++) {
      celdas[i].textContent = "";
      celdas[i].classList.remove("x", "o", "pop", "gana-mini");
    }
    for (let k = 0; k < n; k++) {
      const jug = MINI_JUGADAS[k];
      const c = celdas[jug[0]];
      c.textContent = jug[1];
      c.classList.add(jug[1] === "X" ? "x" : "o");
      if (k === n - 1) c.classList.add("pop");
    }
    if (previewPaso === MINI_JUGADAS.length + 1) {
      [0, 4, 8].forEach(i => celdas[i].classList.add("gana-mini"));
    }
  }
}
/* Mini tablero de la portada: juega solo, en bucle. */
const MINI_JUGADAS = [[0, "X"], [1, "O"], [4, "X"], [2, "O"], [8, "X"]];
let miniPaso = 0;
function dibujarMini() {
  const grid = $("mini-grid");
  if (!grid) return;
  grid.innerHTML = "";
  for (let i = 0; i < 9; i++) {
    const c = document.createElement("div");
    c.className = "mini-celda";
    grid.appendChild(c);
  }
}
function tickMini() {
  const pantalla = $("pantalla-inicio");
  if (!pantalla || !pantalla.classList.contains("activo")) return;
  const grid = $("mini-grid");
  if (!grid || !grid.children.length) return;
  if (miniPaso >= MINI_JUGADAS.length) {
    miniPaso = 0;
    dibujarMini();
    return;
  }
  const jug = MINI_JUGADAS[miniPaso];
  const celda = grid.children[jug[0]];
  if (celda) {
    for (const c of grid.children) c.classList.remove("pop");
    celda.textContent = jug[1];
    celda.classList.add(jug[1] === "X" ? "x" : "o", "pop");
  }
  miniPaso++;
  if (miniPaso >= MINI_JUGADAS.length) {
    [0, 4, 8].forEach(i => { const c = grid.children[i]; if (c) c.classList.add("gana-mini"); });
  }
}
setInterval(tickMini, 850);

/* ---------------- Modo demo ---------------- */
/* La demo juega sola una partida corta en Fácil para mostrar cómo se
   juega. Pide los retos con ?demo=1 (el servidor incluye los valores
   correctos solo en ese modo) y los escribe en los campos con
   animación, los valida y coloca la pieza. La demo NO guarda progreso,
   XP ni acreditaciones, y el reloj no corre. En la demo la primera
   colocación también resuelve un reto (en el juego real es libre),
   para que se vean 4 retos resueltos: apertura + 3 casillas. */
let demoActivo = false;
let demoTimer = null;
let demoEscribiendo = false;
let demoIndiceX = 0;
let demoMovsCPU = [];
const DEMO_MOVS_X = [0, 2, 1];   // casillas 1, 3, 2 -> fila superior
const DEMO_MOVS_CPU_FIJOS = [4, 8]; // casillas 5 y 9
function demoEstado(txt) {
  const el = $("demo-estado");
  if (el) { el.textContent = txt; el.style.display = "block"; }
  const nota = $("demo-nota");
  if (nota) nota.style.display = "block";
}
function demoFormatoValor(v) {
  // Hasta 6 decimales, sin ceros de más; dentro de la tolerancia ±0.001.
  let s = Number(v).toFixed(6);
  if (s.indexOf(".") >= 0) s = s.replace(/0+$/, "").replace(/\.$/, "");
  return s === "-0" ? "0" : s;
}
function iniciarDemo() {
  salirDemoSilencioso();
  demoActivo = true;
  demoIndiceX = 0;
  demoEscribiendo = false;
  demoMovsCPU = DEMO_MOVS_CPU_FIJOS.slice();
  nivel = 0;
  const b = $("btn-salir-demo");
  if (b) b.style.display = "block";
  demoEstado("Demostración: el programa juega solo una partida corta en Fácil.");
  iniciarPartida(true);
  if (demoTimer) clearInterval(demoTimer);
  demoTimer = setInterval(demoLoop, 400);
}
function salirDemoSilencioso() {
  const habiaDemo = demoActivo || !!demoTimer;
  if (demoTimer) { clearInterval(demoTimer); demoTimer = null; }
  demoActivo = false;
  demoEscribiendo = false;
  const b = $("btn-salir-demo");
  if (b) b.style.display = "none";
  const e = $("demo-estado");
  if (e) { e.textContent = ""; e.style.display = "none"; }
  const nota = $("demo-nota");
  if (nota) nota.style.display = "none";
  if (habiaDemo) { retoToken++; actual = null; }
}
function salirDemo() {
  salirDemoSilencioso();
  ocultarSmasher();
  activo = false;
  if (timerId) { clearInterval(timerId); timerId = null; }
  $("modal-ficha").classList.remove("activo");
  $("modal-reto").classList.remove("activo");
  $("modal-reto").classList.add("sin-reto");
  actualizarInicio();
  mostrar("pantalla-inicio");
}
async function demoEscribirYValidar() {
  const vals = actual && actual.reto ? actual.reto.demo_valores : null;
  if (!vals) { mostrarToast("La demo no recibió los valores."); salirDemo(); return; }
  const campos = actual.reto.campos || [];
  const yaEscritos = campos.every((c, i) => {
    const el = $("campo-" + i);
    return el && el.value.trim() !== "";
  });
  if (yaEscritos) return;
  demoEscribiendo = true;
  /* Narración: qué método se resuelve y que primero va la comprobación
     a mano (el validador), y luego el resultado. */
  demoEstado("Reto de " + nombreVisible(actual.nombre) +
    " — primero la comprobación a mano, luego el resultado.");
  /* Pausa para que la maestra lea qué método es antes de que empiece
     a escribir. */
  await new Promise(r => setTimeout(r, 5000));
  if (!demoActivo) { demoEscribiendo = false; return; }
  for (let i = 0; i < campos.length; i++) {
    const el = $("campo-" + i);
    if (!el) continue;
    const esComp = campos[i].tipo === "comprobacion" || campos[i].tipo === "comprobacion2";
    demoEstado(esComp
      ? "Comprobación (hazlo a mano): el programa escribe el paso…"
      : "Resultado: el programa escribe el valor…");
    const texto = demoFormatoValor(vals[campos[i].id]);
    el.value = "";
    for (const ch of texto) {
      if (!demoActivo) { demoEscribiendo = false; return; }
      el.value += ch;
      await new Promise(r => setTimeout(r, 500));
    }
    await new Promise(r => setTimeout(r, 2000));
  }
  if (!demoActivo) { demoEscribiendo = false; return; }
  demoEscribiendo = false;
  demoEstado("Comprobación y resultado escritos. Validando…");
  await new Promise(r => setTimeout(r, 3000));
  if (!demoActivo) return;
  $("btn-validar").click();
}
async function demoLoop() {
  if (!demoActivo || demoEscribiendo) return;
  if ($("pantalla-fin") && $("pantalla-fin").classList.contains("activo")) {
    /* Al llegar a Victoria, la demo se queda en la pantalla final, que
       ya muestra el resumen y, por casilla, las comprobaciones y los
       resultados. "Salir de la demo" sigue visible siempre. */
    if (demoTimer) { clearInterval(demoTimer); demoTimer = null; }
    return;
  }
  if (retoFallido) { mostrarToast("La demo no pudo cargar un reto."); salirDemo(); return; }
  if ($("modal-ficha").classList.contains("activo")) {
    demoEstado("El programa elige la ficha X.");
    demoEscribiendo = true;
    const bx = document.querySelector('#modal-ficha [data-ficha="X"]');
    if (bx) bx.click();
    setTimeout(() => {
      if (!demoActivo) return;
      libre = false;
      demoEscribiendo = false;
      demoEstado("El programa resuelve el reto de la casilla 1…");
      abrirReto(DEMO_MOVS_X[0]);
      demoIndiceX = 1;
    }, 4000);
    return;
  }
  if (actual && $("modal-reto").classList.contains("activo")) {
    await demoEscribirYValidar();
    return;
  }
  if (activo && !actual && !procesando && demoIndiceX < DEMO_MOVS_X.length) {
    const celda = DEMO_MOVS_X[demoIndiceX];
    demoEstado("Coloca la X en la casilla " + (celda + 1) + "…");
    demoIndiceX++;
    casilla(celda);
    return;
  }
}

/* ---------------- Inicio / eventos ---------------- */
function init() {
  aplicarSkin();
  actualizarInicio();
  const fondo = $("fondo-flotante");
  if (fondo) {
    const colores = ["#FCEE0A", "#FF003C", "#00F0FF", "#FFFFFF", "#2BFF88"];
    for (let i = 0; i < 12; i++) {
      const s = document.createElement("span");
      s.textContent = i % 2 === 0 ? "X" : "O";
      s.style.left = (3 + Math.random() * 90) + "%";
      s.style.top = (4 + Math.random() * 88) + "%";
      s.style.fontSize = (34 + Math.random() * 52) + "px";
      s.style.color = colores[i % colores.length];
      s.style.animationDuration = (8 + Math.random() * 8) + "s";
      s.style.animationDelay = (-Math.random() * 8) + "s";
      fondo.appendChild(s);
    }
  }
  dibujarMini();
  renderHomeSkins();
  if (!previewTimer) previewTimer = setInterval(tickPreviewBoards, 650);
  document.querySelectorAll(".nivel").forEach(el => {
    el.addEventListener("click", () => {
      nivel = parseInt(el.dataset.nivel, 10);
      actualizarInicio();
    });
  });
  $("btn-jugar").addEventListener("click", () => iniciarPartida(false));
  $("btn-demo").addEventListener("click", iniciarDemo);
  $("btn-salir-demo").addEventListener("click", salirDemo);
  $("btn-recompensas").addEventListener("click", () => { renderRecompensas(); mostrar("pantalla-recompensas"); });
  $("btn-metodos").addEventListener("click", () => { renderMetodos(); mostrar("pantalla-metodos"); });
  $("btn-records").addEventListener("click", () => { renderRecords(); mostrar("pantalla-records"); });
  $("btn-volver-inicio-4").addEventListener("click", () => { actualizarInicio(); mostrar("pantalla-inicio"); });
  $("btn-volver-inicio").addEventListener("click", () => { salirDemoSilencioso(); actualizarInicio(); mostrar("pantalla-inicio"); });
  $("btn-volver-inicio-2").addEventListener("click", () => { salirDemoSilencioso(); actualizarInicio(); mostrar("pantalla-inicio"); });
  $("btn-volver-inicio-3").addEventListener("click", () => { actualizarInicio(); mostrar("pantalla-inicio"); });
  $("btn-otra-vez").addEventListener("click", () => iniciarPartida(false));
  $("btn-copiar-reporte").addEventListener("click", copiarReporte);
  $("btn-tiempos").addEventListener("click", () => {
    $("t0").value = progreso.tiempos[0];
    $("t1").value = progreso.tiempos[1];
    $("t2").value = progreso.tiempos[2];
    $("error-tiempos").textContent = "";
    mostrar("pantalla-tiempos");
  });
  $("btn-cancelar-tiempos").addEventListener("click", () => mostrar("pantalla-inicio"));
  $("btn-guardar-tiempos").addEventListener("click", () => {
    const a = parseInt($("t0").value, 10), b = parseInt($("t1").value, 10), c = parseInt($("t2").value, 10);
    if (![a, b, c].every(v => Number.isInteger(v)) || !(a >= 1 && a < b && b < c && c <= 120)) {
      $("error-tiempos").textContent = "Usa minutos enteros de 1 a 120, en orden ascendente.";
      return;
    }
    progreso.tiempos = [a, b, c];
    guardarProgreso();
    actualizarInicio();
    mostrar("pantalla-inicio");
  });
  let confirmarReinicio = false;
  $("btn-reiniciar").addEventListener("click", () => {
    const btn = $("btn-reiniciar");
    if (!confirmarReinicio) {
      confirmarReinicio = true;
      btn.textContent = "¿Seguro? Toca de nuevo para borrar todo";
      setTimeout(() => { confirmarReinicio = false; btn.textContent = "Reiniciar progreso"; }, 4000);
      return;
    }
    confirmarReinicio = false;
    btn.textContent = "Reiniciar progreso";
    progreso = { acreditados: [], victorias: 0, racha: 0, skin: "Clásica", tiempos: TIEMPOS_DEFECTO.slice(), victoriaAvanzada: false, partidas: 0, derrotas: 0, mejorRacha: 0, mejorTiempo: null, tiempoTotal: 0 };
    guardarProgreso();
    aplicarSkin();
    actualizarInicio();
    renderRecompensas();
  });
  $("btn-abandonar").addEventListener("click", () => terminar("Abandono"));
  $("btn-validar").addEventListener("click", () => validar(false));
  $("btn-ceder").addEventListener("click", () => validar(true));
  document.querySelectorAll("#modal-ficha [data-ficha]").forEach(b => {
    b.addEventListener("click", () => {
      jugador = b.dataset.ficha;
      libre = true;
      $("modal-ficha").classList.remove("activo");
      $("reto-espera-txt").textContent = "Coloca tu primera ficha en una casilla libre.";
      dibujarTablero("¡Correcto! Elige dónde colocar tu primera ficha.");
    });
  });
  document.addEventListener("keydown", e => {
    if (e.key === "Enter" && $("modal-reto").classList.contains("activo")) validar(false);
  });
}
if (typeof document !== "undefined") {
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
}

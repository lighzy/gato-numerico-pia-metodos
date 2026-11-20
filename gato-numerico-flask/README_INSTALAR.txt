GATO NUMÉRICO — VERSIÓN FLASK
==============================

El juego Gato Numérico (Métodos Numéricos) en versión web con Python
y Flask. El servidor genera los retos con los 29 métodos en 5
categorías y los valida con tolerancia ±0.001.

REQUISITOS
----------
- Python 3.9 o superior.
- Flask (se instala con el paso 1).

INSTALACIÓN (Windows, en PowerShell)
------------------------------------
1. Entra a la carpeta del proyecto (donde están app.py y
   requirements.txt) y instala Flask:

   pip install -r requirements.txt

   Si eso falla, instala Flask directamente:

   pip install flask

2. Arranca el servidor:

   python app.py

   Verás algo como "Running on http://0.0.0.0:5000". No cierres
   esa ventana mientras juegues: ahí corre el servidor.

3. Abre el juego en el navegador:

   http://localhost:5000

JUGAR DESDE EL CELULAR (misma Wi-Fi)
-------------------------------------
1. En la computadora, averigua su dirección IP local. En PowerShell:

   ipconfig

   Busca "Dirección IPv4" de tu Wi-Fi (algo como 192.168.1.15).
2. En el celular, conectado a la misma Wi-Fi, abre:

   http://192.168.1.15:5000

   (cambia 192.168.1.15 por la IP de tu computadora).
3. Si el celular no abre la página, permite Python en el Firewall
   de Windows cuando lo pregunte, o revisa que el celular esté en
   la misma red Wi-Fi que la computadora.

CÓMO SE JUEGA
--------------
- Elige nivel: Fácil (PARTE 1 DE 3), Medio (PARTE 2 DE 3) o Difícil
  (PROBLEMA COMPLETO). Los tiempos son 25, 30 y 60 minutos.
- Cada reto pide primero una COMPROBACIÓN: un valor intermedio del
  procedimiento que debes calcular a mano (por ejemplo, la primera
  aproximación nueva, el primer incremento k1 o la suma ponderada
  interior). Esa comprobación nunca viene escrita en el enunciado:
  si la copias de algún lado, es que no la calculaste.
- En Difícil (PROBLEMA COMPLETO) se piden DOS comprobaciones: la
  primera y una segunda, que es otro paso intermedio del mismo
  método. En Fácil y Medio solo hay una comprobación.
- Después se piden los resultados del método.
- Las respuestas se aceptan con punto o con coma decimal (1.234
  o 1,234) y con tolerancia ±0.001.
- Respuesta incorrecta: pierdes tiempo (Fácil −2 min, Medio −3 min,
  Difícil −4 min). Tres en línea gana la casilla.
- Los problemas se ven con notación matemática real: exponentes como
  superíndices, integrales con el símbolo ∫ y sus dos límites,
  fracciones apiladas, subíndices y raíces.

MODO DEMO
---------
- El botón VER DEMO (en la pantalla principal) juega solo una
  partida corta en Fácil para mostrar cómo se juega: resuelve los
  retos por sí mismo, escribe las respuestas en los campos, las
  valida y coloca la pieza. Son 4 retos: apertura + 3 casillas,
  y gana con la fila superior. La computadora sigue una secuencia
  fija y sencilla en la demo. Mientras juega, una línea explica lo
  que va pasando ("Reto de Newton-Raphson — primero la
  comprobación a mano…", "Comprobación correcta…"), y la demo
  escribe también la Comprobación (hazlo a mano), para que se vea
  el validador. Al ganar, la pantalla final muestra el resumen y,
  por casilla, las comprobaciones y los resultados de cada reto.
- El reloj no corre en la demo y la demo NO guarda progreso, XP
  ni acreditaciones. Puedes salir en cualquier momento con el
  botón "Salir de la demo", que sigue visible hasta el final.
  Al terminar puedes volver al inicio o jugar de verdad.
- La demo juega con la skin que tengas seleccionada.

SKINS
-----
- Clásica: disponible desde el inicio.
- Neón: 3 victorias.
- Circuito: completa una categoría (acredita todos sus métodos).
- Dorada: gana una partida en Difícil. Cada casilla ocupada (con X
  o con O) lleva un destello dorado ✦ que palpita en la esquina,
  igual que el de la vista previa: en el tablero, en el mini
  tablero, en el tablero final y en la demo.
- Campeón: completa las 5 categorías. Es la más difícil de conseguir
  y también la más bonita: cada casilla ocupada (con X o con O) lleva
  un contorno amarillo brilloso y una coronita ♛ en la esquina.
- La skin elegida se aplica en todas partes: el tablero al jugar,
  la demo y el mini tablero "Así se juega". Cada skin muestra en
  Recompensas un mini tablero 3×3 que juega solo con su estilo.

MÉTODOS
-------
- El botón MÉTODOS (en la pantalla principal) muestra las 5
  categorías como lista desplegable: al desplegar una categoría se
  ven sus métodos con su nombre original y su número de sección,
  y si ya están acreditados (✓ Acreditado) o pendientes.

REPORTE DE PARTIDA (EN LA PANTALLA DE FIN)
-------------------------------------------
- Al terminar una partida, la pantalla de fin muestra primero un
  resumen: resultado, nivel, tiempo usado, retos correctos,
  métodos acreditados en la partida y tiempo perdido por errores.
  Debajo, una tarjeta por casilla, en orden de juego: método,
  comprobación 1 dada y correcta, comprobación 2 (solo en
  Difícil), resultados dados y correctos, acierto o fallo y
  segundos usados en cada reto. Cada tarjeta se puede desplegar
  con "Ver problema y pasos" para ver el enunciado y los pasos
  resueltos de ese reto.
- El botón "Copiar reporte" (en la misma pantalla de fin) copia
  ese mismo contenido como texto plano, para guardarlo o
  compartirlo.
- Sirve para repasar después de la partida qué salió bien y dónde
  falló cada cálculo, sin tener que volver a jugar.

MIS RÉCORDS
-----------
- El botón "Mis récords" (en la pantalla principal) muestra tus
  números en el campeonato: partidas jugadas, victorias, derrotas,
  % de victorias, mejor tiempo de victoria (con su nivel), racha
  actual, mejor racha y tiempo total jugado; además, métodos
  acreditados (n/29 y por categoría) y skins desbloqueadas (n/5).
- Los récords se actualizan solos al terminar cada partida real
  (la demo no cuenta) y se guardan en el navegador con el resto del
  progreso. Toda partida que no termina en victoria cuenta como
  derrota, así partidas = victorias + derrotas siempre.
- El tiempo total jugado se registra a partir de esta versión; las
  partidas anteriores a ella no se suman (no se inventan datos).

RESPALDO
--------
La versión anterior del juego (un solo archivo HTML, sin servidor)
sigue funcionando como respaldo: ábrela directamente en el navegador
con doble clic, sin instalar nada.

ARCHIVOS
--------
- app.py ............... Servidor Flask (rutas / y /api/reto, /api/validar).
- metodos.py ........... Generadores de los 29 métodos y comprobación.
- problemas_libro.py ... Banco de los 87 problemas (29 métodos x 3).
- requirements.txt ..... Solo Flask.
- sweep.py ............. Verificación automática de los 87 retos.
- templates/index.html . Interfaz del juego (frontend).

# Dodgem

Juego de tablero **Dodgem** con interfaz gráfica y agente Minimax.
Fundamentos de Inteligencia Artificial.

Sin dependencias externas: solo la biblioteca estándar de Python 3.8+
(Tkinter viene incluido).

---

## Cómo ejecutar

```bash
python main.py                       # abre la pantalla de configuración
python main.py --n 8                 # tablero 8 x 8
python main.py --modo humano_vs_agente --nivel dificil
python main.py --n 10 --diagnostico  # imprime el estado inicial y sale
```

Modos: `humano_vs_humano`, `humano_vs_agente`, `agente_vs_humano`,
`agente_vs_agente`. Niveles: `facil`, `medio`, `dificil`, `experto`.

Si Tkinter no está instalado (algunas distribuciones de Linux lo
separan del intérprete):

```bash
sudo apt install python3-tk
```

---

## Estructura del proyecto

| Archivo | Responsabilidad | Contiene lógica de juego |
|---|---|---|
| `config.py` | Todos los parámetros: tamaños, direcciones, reglas, pesos, colores. | No |
| `motor.py` | Máquina de estados **pura**: las 6 funciones exigidas. | Sí, toda |
| `gui.py` | Interfaz Tkinter: dibuja y traduce clics. | No |
| `main.py` | Punto de entrada y argumentos de línea de comandos. | No |
| `heuristica.py` | Función de evaluación (Semana 3). | No, solo la mide |
| `agente.py` | Minimax + Alfa-Beta + transposiciones (Fase 2). | No, solo la busca |
| `pruebas_motor.py` | 41 pruebas unitarias del motor. | No |
| `pruebas_heuristica.py` | 30 pruebas de la heurística. | No |
| `pruebas_agente.py` | 23 pruebas del agente. | No |
| `banco_heuristica.py` | Banco de medición. **No es entrega.** | No |
| `banco_agente.py` | Banco de medición. **No es entrega.** | No |

La regla de oro del diseño: **`gui.py` no sabe jugar al Dodgem.** Si
una jugada aparece resaltada en pantalla es porque
`motor.movimientos_legales()` la devolvió. Esa frontera es lo que
permitió, en la Fase 2, enchufar el agente sin tocar ni una regla:
`gui.py` solo aprendió *a quién pedirle* la jugada, no *cómo* elegirla.

---

## API del motor

```python
validar_n(n)                -> bool
estado_inicial(n)           -> Estado
movimientos_legales(estado) -> tuple[Movimiento, ...]
aplicar(estado, movimiento) -> Estado      # no muta el original
es_terminal(estado)         -> bool
ganador(estado)             -> "A" | "B" | "EMPATE" | None
```

### Representación del estado

```python
Estado(
    n            = 6,
    fichas_a     = frozenset({(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)}),
    fichas_b     = frozenset({(5, 1), (5, 2), (5, 3), (5, 4), (5, 5)}),
    turno        = "A",
    salidas_a    = 0,
    salidas_b    = 0,
    sin_progreso = 0,
)
```

* `NamedTuple` + `frozenset` ⇒ el estado es **inmutable y hashable**,
  así que sirve directamente como clave de una tabla de
  transposiciones en la Fase 2.
* Conjuntos de coordenadas en vez de matriz `n × n`: comprobar
  "casilla ocupada" cuesta O(1) y generar jugadas cuesta O(fichas), no
  O(n²).
* Coordenadas `(fila, columna)` en base 0, con fila 0 arriba. La
  conversión a la numeración del enunciado (desde 1) ocurre solo en la
  capa de presentación.

---

## Reglas implementadas

* Tablero `n × n` con **n par y n > 4**; `n − 1` fichas por jugador.
* Disposición inicial oficial: A ocupa la columna izquierda completa,
  B la fila inferior completa, y la esquina inferior izquierda queda
  vacía. Al descontar esa esquina compartida, cada jugador queda con
  exactamente `n − 1` fichas.
* **A** avanza a la derecha; puede desplazarse una casilla arriba o
  abajo. Nunca a la izquierda.
* **B** avanza hacia arriba; puede desplazarse una casilla a la
  izquierda o a la derecha. Nunca hacia abajo.
* El destino debe estar vacío. No hay capturas ni saltos.
* **Salidas**: una ficha abandona el tablero solo con un movimiento de
  *avance* cuyo destino cae fuera. Esa única condición implementa a la
  vez que A solo sale por la derecha y B solo por arriba: un intento de
  salir lateralmente usa un vector que no es el de avance y se descarta
  sin necesidad de una regla aparte.
* **Victoria por salida**: gana quien saca todas sus fichas.
* **Bloqueo**: si al inicio de su turno un jugador conserva fichas pero
  no tiene movimientos legales, pierde (no se permite pasar).

> Nota: el Dodgem clásico usa la convención inversa para el bloqueo
> (se penaliza a quien bloquea). Ambas están implementadas; la activa
> se elige con `config.REGLA_BLOQUEO`.

---

## Parámetros modificables en vivo

Todo lo siguiente se cambia editando **solo `config.py`**, sin tocar
`motor.py` ni `gui.py`:

| Quiero cambiar… | Constante |
|---|---|
| El rango de tamaños permitidos | `TAMANO_MINIMO_EXCLUSIVO`, `TAMANO_MAXIMO_TABLERO` |
| Que n pueda ser impar | `RESTO_PARIDAD_REQUERIDO` |
| Cuántas fichas tiene cada jugador | `FICHAS_MENOS_QUE_LADO` |
| La dirección de avance de un jugador | `DIRECCION_AVANCE` (la colocación inicial se reacomoda sola) |
| Los movimientos laterales permitidos | `DIRECCIONES_LATERALES` |
| Que la esquina compartida no quede vacía | `ESQUINA_COMPARTIDA_VACIA` |
| Quién gana al quedar bloqueado | `REGLA_BLOQUEO` |
| Activar tablas por falta de progreso | `TABLAS_HABILITADAS`, `LIMITE_JUGADAS_SIN_PROGRESO` |
| Quién mueve primero | `JUGADOR_INICIAL` |
| Los colores de la interfaz | `PALETA` |

---

## Pruebas

```bash
python -m unittest pruebas_motor pruebas_heuristica pruebas_agente -v
```

**94 pruebas en total.** Las 41 del motor cubren: validación de `n`, disposición inicial para
todos los tamaños, prohibición de retroceder, reglas de salida por el
borde correcto, pureza de `aplicar()`, condiciones de victoria y de
bloqueo (con ambas convenciones), tablas, y una simulación de partidas
aleatorias que verifica invariantes jugada a jugada:

* fichas en tablero + fichas fuera = `n − 1`, siempre;
* nunca hay dos fichas en la misma casilla;
* toda ficha en juego está dentro del tablero.

---

## Función heurística (Semana 3)

Archivos: `heuristica.py` (entrega), `pruebas_heuristica.py` (30
pruebas), `banco_heuristica.py` (banco de medición, **no** es entrega).

```python
heuristica_dodgem(estado, jugador_max) -> float   # h(n)
evaluar(estado, jugador_max, profundidad=0)       # f(n) = g(n) + h(n)
explicar(estado, jugador_max) -> str              # desglose para defender
```

### La idea: el Dodgem es una carrera de dos pathfindings

Cada ficha resuelve su propio problema de camino hacia el carril de
salida. La partida es la superposición de los dos, compitiendo por las
mismas casillas. De ahí los dos bloques de la fórmula: **progreso**
(cuánto me falta) y **restricción** (cuánto le estorbo).

### Distancia Manhattan a un objetivo que es una línea

El objetivo de una ficha no es una casilla sino un *conjunto*: cualquier
casilla pasado su borde de salida. La distancia Manhattan a un conjunto
es el mínimo a sus elementos, y para A en `(f, c)`:

```
h(f, c) = mín  |f − f'| + |n − c|  =  n − c        (el mínimo está en f' = f)
          f'
```

La componente perpendicular se anula: la distancia Manhattan **degenera
en la distancia horizontal**. No es una simplificación arbitraria, es el
resultado exacto de la definición aplicada a una meta lineal.

* **Admisible**: en el problema relajado (tablero vacío) una ficha a
  distancia `d` necesita exactamente `d` movimientos; los obstáculos
  solo alargan. Luego `h ≤ h*`. Verificado con BFS en las pruebas.
* **Consistente**: un movimiento cambia una coordenada en 1, luego
  `|h(s) − h(s')| ≤ 1` = coste del movimiento.
* **Cota inferior del jugador**: cada turno mueve una ficha una casilla,
  y un lateral no reduce la distancia. Luego `D(J) = Σ h` es una cota
  inferior del número de turnos que le faltan a `J` para ganar.

### Dónde están g(n) y h(n)

| A* | Aquí |
|---|---|
| `g(n)` coste pagado | profundidad del nodo en el árbol |
| `h(n)` coste estimado | `heuristica_dodgem()` en las hojas del corte |
| `f(n) = g + h` | `evaluar()`: un final ganado vale `VICTORIA − profundidad` |

El descuento por profundidad hace que entre dos victorias el agente
elija la **más corta**, y entre dos derrotas la **más larga**. Y el
orden de `movimientos_legales()` (salidas y avances primero) es
exactamente "explorar antes lo que más reduce h", que es lo que hace
podar temprano a Alfa-Beta.

### La fórmula

```
H = W_DISTANCIA      · (D_min  − D_max)      ← invertida: menos distancia es mejor
  + W_SALIDA         · (F_max  − F_min)
  + W_BLOQUEO_RIVAL  · (BR_min − BR_max)
  + W_BLOQUEO_PROPIO · (BP_min − BP_max)
  + s · W_INMOVILIZADA · (I_min − I_max)
  + W_MOVILIDAD      · (M_max  − M_min)
  + W_TEMPO          · (±1 según quién mueve)
```

Es antisimétrica por construcción: `H(s, A) = −H(s, B)`. El factor `s`
sigue a `config.REGLA_BLOQUEO`: con la regla clásica (el bloqueado gana)
inmovilizar al rival **resta**, porque bloquearlo sería perder.

### Evidencia (banco de medición, tablero 6×6)

| Medición | Resultado |
|---|---|
| Coste por evaluación | 15,7 µs (n=6) · 41 µs (n=16) — unas 64 000/s |
| Contra jugador aleatorio, prof. 1 | 97 % de victorias [IC95: 92–100] |
| Contra jugador aleatorio, prof. 2 y 3 | 100 % |
| Contra "solo distancia", prof. 1 | 75 % [IC95: 67–83] |
| Contra "solo distancia", prof. 2 | 71 % [IC95: 63–79] |

El segundo experimento es el que justifica el bloque de restricción: a
profundidad 1 no hay búsqueda que compense, así que mide la evaluación
y no el árbol. Los intervalos excluyen el 50 %, o sea que la diferencia
no es ruido.

### Los pesos se midieron, no se adivinaron

Cada peso se propuso con un argumento analítico y después se midió
enfrentando variantes (120 partidas por combinación, dos tamaños de
tablero). Tres valores cambiaron al medirlos:

| Peso | Estimado | Medido | Por qué |
|---|---|---|---|
| `W_BLOQUEO_RIVAL` | 3,0 | **6,0** | El rival puede *sostener* el bloqueo; no cuesta solo el rodeo puntual |
| `W_INMOVILIZADA` | 8,0 | **4,0** | Un valor alto hacía perseguir bloqueos totales (raros) en vez de correr |
| `W_MOVILIDAD` | 0,5 | **0,2** | Competía de igual a igual con avanzar; el agente daba vueltas |

Con los pesos estimados el agente empataba con "solo distancia" a
profundidad 2 (47 %); con los medidos gana 71 %.

> Advertencia metodológica que conviene mencionar en la defensa: dos
> agentes deterministas producen siempre la misma partida, así que
> "80 partidas" serían 2 repetidas 40 veces. Por eso el banco desempata
> al azar entre jugadas de igual valor, y por eso no poda con alfa en la
> raíz (podar ahí devolvería cotas en lugar de valores exactos y el
> conjunto de empatados quedaría mal identificado).

### Cómo defenderla en pantalla

```bash
python banco_heuristica.py            # informe completo
python -m unittest pruebas_heuristica -v
```

`heuristica.explicar(estado, "A")` imprime una tabla con el aporte de
cada término, para no tener que exhibir un número mágico:

```
TERMINO                     APORTE   DETALLE
Distancia a la salida         -1.0   me faltan 28 pasos, a el 27
Atascos propios               +1.0   mios 0, suyos 1
Movilidad                     +0.5   10 jugadas contra 9
Tempo                         -0.5   mueve Jugador B
TOTAL                         +0.0   (1 punto = 1 paso de avance)
```

---


## El agente Minimax (Fase 2)

Archivos: `agente.py` (entrega), `pruebas_agente.py` (23 pruebas),
`banco_agente.py` (banco de medición, **no** es entrega).

```python
AgenteMinimax(jugador, nivel).elegir(estado) -> Resultado
elegir_movimiento(estado, nivel=...) -> Movimiento   # API mínima
```

### Cómo se juega contra él

En la pantalla de configuración se elige el modo (Humano vs Humano,
Humano vs Bot, Bot vs Humano, Bot vs Bot) y el nivel. Durante la
partida, el panel lateral muestra en vivo la profundidad alcanzada,
los nodos visitados, las podas y los aciertos de tabla: son la
evidencia de que la poda funciona, sin salir del juego.

### Las tres técnicas

**1. Poda Alfa-Beta** (obligatoria según el enunciado). `alfa` es lo
mejor que MAX tiene asegurado; `beta`, lo mejor de MIN. Cuando
`alfa ≥ beta` la rama ya no puede influir en la decisión y se corta.

**2. Tabla de transposiciones.** Distintas secuencias de jugadas
llegan a la misma posición. Aquí se cobra la decisión de la Entrega 1:
`Estado` es un `NamedTuple` de `frozenset`, o sea **hashable**, y
sirve tal cual como clave de un diccionario.

**3. Profundización iterativa.** Se busca a profundidad 1, 2, 3…
Parece desperdicio repetir trabajo, pero cada iteración deja en la
tabla la mejor jugada de cada posición, y eso hace que la siguiente
pode mucho más. Además siempre hay una respuesta lista, que es lo que
permite tener un tope de tiempo sin devolver una búsqueda a medias.

### El detalle delicado: puntajes de victoria en la tabla

`evaluar()` devuelve `VICTORIA − profundidad`, así que el valor
depende de **dónde** está el nodo en el árbol, no solo de la posición.
Guardarlo tal cual y reutilizarlo desde otra profundidad haría creer
al agente que tiene una victoria más cercana (o más lejana) de lo que
es. Al guardar se convierte a "distancia desde este nodo" sumando el
ply; al leer se deshace. Los puntajes heurísticos normales no se tocan.

Es el error clásico de un Minimax con transposiciones, y es
exactamente lo que caza `test_la_tabla_no_altera_el_valor`.

### La prueba que importa

Una optimización que cambia el resultado es un error. `agente.py`
incluye `minimax_sin_poda()`, una implementación de referencia
deliberadamente lenta y obviamente correcta, y las pruebas comparan
las dos búsquedas sobre decenas de posiciones y varias profundidades:

```python
minimax_sin_poda(estado, d, jugador) == valor_con_alfa_beta(estado, d, jugador)
```

El banco repite esa comprobación con `assert` en cada medición, para
que ningún número de nodos se reporte sin haber verificado antes que
el valor sigue siendo el mismo.

### Evidencia (tablero 6×6)

Nodos visitados desde la posición inicial — **las tres columnas
devuelven el mismo valor**:

| Profundidad | Sin poda | Con poda | Poda + tabla | Ahorro |
|---|---|---|---|---|
| 3 | 326 | 135 | 135 | 2,4× |
| 4 | 2 702 | 584 | 469 | 5,8× |
| 5 | 24 028 | 2 214 | 1 475 | **16,3×** |

Tiempo por jugada (el `*` marca que actuó el tope de seguridad):

| Nivel | n=6 | n=10 | n=16 |
|---|---|---|---|
| fácil (prof. 2) | 0,00 s | 0,00 s | 0,01 s |
| medio (prof. 4) | 0,01 s | 0,03 s | 0,25 s |
| difícil (prof. 6) | 0,09 s | 0,78 s | 8,02 s* |
| experto (prof. 8) | 0,50 s | 5,67 s | 15,04 s* |

Esto es justo lo que justifica el diseño elegido: la profundidad manda
(el bot es determinista y reproducible), y el tope de tiempo solo se
activa en tableros grandes para que la ventana no se congele.

Calidad de juego (20 partidas, apertura aleatoria distinta en cada una):

| Enfrentamiento | Resultado |
|---|---|
| fácil / medio / difícil contra aleatorio | 20-0 los tres |
| medio contra fácil | 11-1 (8 sin resolver) |
| difícil contra medio | 12-5 (3 sin resolver) |

> Las "sin resolver" son partidas que llegaron al tope de 400 jugadas.
> Es la propiedad conocida del Dodgem en tableros pares: con juego
> defensivo por ambos lados la partida puede no terminar. Para
> demostraciones bot contra bot conviene activar
> `config.TABLAS_HABILITADAS`.

> Advertencia metodológica: los agentes son **deterministas**, así que
> enfrentarlos desde la posición inicial produciría siempre la misma
> partida y "20 partidas" serían una repetida veinte veces. Por eso
> cada partida del banco arranca con 4 jugadas al azar.

### La interfaz no se congela

La búsqueda **no** puede correr en el hilo de Tkinter: mientras
calcula, la ventana dejaría de repintarse y el sistema la marcaría
como "no responde". El agente corre en un hilo aparte que deja el
resultado en una `queue.Queue`, y el hilo de la interfaz la consulta
cada 50 ms con `after()`.

Regla de oro respetada en todo el código: **solo el hilo de Tkinter
toca widgets**. El hilo trabajador únicamente pone una tupla en la
cola. Y trabajar sobre el estado desde otro hilo es seguro sin copiar
ni bloquear nada precisamente porque el motor es puro.

Detalles que evitan errores reales:

* **Generación de partida.** Si el usuario reinicia mientras el bot
  piensa, el resultado que llegue tarde trae una generación antigua y
  se descarta. Sin esto, el bot aplicaría una jugada de una partida
  que ya no existe.
* **Cancelación.** Un `threading.Event` que la búsqueda consulta cada
  2048 nodos: aborta pronto en vez de seguir gastando CPU.
* **Tablero en solo lectura** durante el turno del bot.
* **Deshacer** retrocede hasta la última decisión *humana*, no una
  sola jugada: deshacer una devolvería el turno al bot, que repetiría
  su jugada al instante (es determinista) y el botón parecería roto.

Todo eso está verificado sin servidor gráfico, con un doble de prueba
de Tkinter que simula el bucle de eventos: se comprueba el ciclo
completo —lanzar el hilo, sondear la cola, aplicar la jugada, y
descartar un resultado obsoleto tras un reinicio a media búsqueda—.

### Parámetros del agente

| Quiero cambiar… | Constante en `config.py` |
|---|---|
| Profundidad o tope de tiempo de un nivel | `NIVELES` |
| Añadir un nivel nuevo | `NIVELES` + `ORDEN_NIVELES` (la interfaz lo muestra sola) |
| Modo de juego por defecto | `MODO_POR_DEFECTO` |
| Tamaño de la tabla de transposiciones | `MAXIMO_ENTRADAS_TRANSPOSICION` |
| Conservar la tabla entre jugadas | `REUSAR_TABLA_ENTRE_JUGADAS` |
| Pausa mínima antes de que el bot mueva | `PAUSA_MINIMA_AGENTE_MS` |

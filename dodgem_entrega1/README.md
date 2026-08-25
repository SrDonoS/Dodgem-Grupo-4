# Dodgem — Entrega 1

Juego de tablero **Dodgem** para dos jugadores humanos, con interfaz
gráfica. Fundamentos de Inteligencia Artificial.

Sin dependencias externas: solo la biblioteca estándar de Python 3.8+
(Tkinter viene incluido).

---

## Cómo ejecutar

```bash
python main.py              # abre la pantalla de configuración
python main.py --n 8        # arranca directamente en un tablero 8 x 8
python main.py --n 10 --diagnostico   # imprime el estado inicial y sale
```

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
| `pruebas_motor.py` | 41 pruebas unitarias del motor. | No |
| `pruebas_heuristica.py` | 30 pruebas de la heurística. | No |
| `banco_heuristica.py` | Banco de medición. **No es entrega.** | No |

La regla de oro del diseño: **`gui.py` no sabe jugar al Dodgem.** Si
una jugada aparece resaltada en pantalla es porque
`motor.movimientos_legales()` la devolvió. Esa frontera es lo que
permitirá, en la Fase 2, reemplazar a un humano por un agente Minimax
sin tocar la interfaz.

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
python -m unittest pruebas_motor -v
```

40 pruebas que cubren: validación de `n`, disposición inicial para
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

## Preparado para la Fase 2 (Minimax + poda Alfa-Beta)

Lo que ya está resuelto para el agente:

1. **Funciones puras**: `aplicar()` devuelve un estado nuevo, así que
   la recursión no necesita deshacer jugadas.
2. **Estados hashables**: tabla de transposiciones sin trabajo extra.
3. **Orden de jugadas**: `movimientos_legales()` entrega primero las
   salidas y los avances (`config.ORDEN_TIPOS_MOVIMIENTO`), que es el
   orden que provoca más cortes en la poda Alfa-Beta.
4. **Corte de profundidad infinita**: el contador `sin_progreso` y la
   regla opcional de tablas evitan ramas que nunca terminan.
5. **Interruptor de rendimiento**:
   `config.VALIDAR_MOVIMIENTOS_AL_APLICAR = False` elimina la
   revalidación dentro de `aplicar()` cuando el buscador ya garantiza
   que el movimiento es legal.

El agente se conectará con una función nueva del tipo
`elegir_movimiento(estado) -> Movimiento`; la interfaz solo tendrá que
llamarla cuando el turno sea del agente y pasar el resultado a
`aplicar()`.

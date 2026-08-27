# 🔧 Guía personal de Donovan
## El motor, la configuración, la interfaz y el arranque

> Tu papel en la defensa: **tú construiste las bases del juego.**
> El tablero, las reglas, la pantalla y el arranque. Un Dodgem completo
> y jugable para **dos personas**, sin nada de inteligencia artificial.
>
> Carlos y Valentín construyeron encima. Pero **encima de lo tuyo**.

---

## 📑 Índice

1. [Cómo presentar tu parte](#1)
2. [El recorrido de un clic](#2) ← *empieza por aquí*
3. [`config.py` — el panel de control](#3)
4. [`motor.py` — las reglas del juego](#4)
5. [`main.py` — el arranque](#5)
6. [`gui.py` — la ventana](#6)
7. [Dónde termina lo tuyo y empieza lo de ellos](#7)
8. [Cambios en vivo, con guion](#8)
9. [Preguntas trampa](#9)
10. [Glosario](#10)

---

<a name="1"></a>
# 1. 🎤 Cómo presentar tu parte

## Tu frase de apertura (30 segundos)

> *"Yo construí el núcleo del juego: un motor de reglas que funciona
> como una **máquina de estados pura**, un archivo de configuración
> donde vive todo lo modificable, y una interfaz gráfica para que dos
> personas puedan jugar una partida completa. El juego funciona entero
> sin ninguna IA — de hecho, así se entregó la primera fase. Lo que
> hicieron mis compañeros después se enchufa encima sin tocar ni una
> regla."*

Eso encuadra tu trabajo perfectamente: **tú hiciste el juego, ellos le
pusieron un cerebro**.

## 💡 Ajuste práctico antes de la demo

Como tú presentas **humano vs humano**, deja el programa abriéndose
directamente en tu modo. En `config.py`, sección 9:

```python
MODO_POR_DEFECTO = MODO_HUMANO_VS_HUMANO   # era MODO_HUMANO_VS_AGENTE
```

Así la pantalla de configuración arranca con tu modo ya marcado y no
tienes que andar clicando mientras hablas.

## 🎬 Guion de demo en 3 minutos

| Momento | Qué haces | Qué dices |
|---|---|---|
| 0:00 | `python main.py` | *"Arranca pidiendo el tamaño del tablero. Estos botones no están escritos a mano: se generan desde `motor.tamanos_validos()`."* |
| 0:20 | Eliges 6, "Humano vs Humano", Comenzar | *"n debe ser par y mayor que 4. Cinco fichas por bando y la esquina inferior izquierda libre: es la disposición oficial del Dodgem."* |
| 0:40 | Clic en una ficha rosa | *"Al seleccionar, se resaltan sus jugadas legales. La interfaz no las calcula: se las pide al motor."* |
| 1:00 | Mueves, mueves, mueves | *"A avanza a la derecha o esquiva arriba y abajo. B avanza hacia arriba. Nunca se retrocede, no hay capturas y no se salta."* |
| 1:40 | Llevas una ficha al carril y la sacas | *"El carril lila es la salida. Gana quien saca todas sus fichas."* |
| 2:10 | Pulsas **Deshacer** dos o tres veces | *"Deshacer es una pila de estados. No reconstruye nada: como el motor nunca modifica un estado, el anterior sigue intacto en memoria."* |
| 2:30 | `python main.py --n 10 --diagnostico` | *"Y el motor funciona sin interfaz. Esto imprime el tablero y las jugadas legales por consola."* |

🎯 Ese último paso es tu **seguro de vida**: demuestra que las reglas
viven en el motor y no en la pantalla.

---

<a name="2"></a>
# 2. 🔄 El recorrido de un clic

**Si entiendes esta página, entiendes el proyecto entero.** Es el
camino completo desde que el usuario hace clic hasta que ve el tablero
actualizado.

```
👆 El usuario hace clic en la casilla (3,2)
│
├─ 1. Tkinter dispara el evento <Button-1>
│     → PantallaJuego._al_hacer_clic(evento)      [gui.py]
│
├─ 2. Dos guardas de seguridad:
│     ¿La partida terminó?  → si sí, no hago nada
│     ¿Es turno de humano?  → si no, no hago nada
│
├─ 3. Traducir píxeles a casilla
│     _casilla_desde_pixel(evento.x, evento.y) → (3, 2)   [gui.py]
│     "el clic cayó en la fila 3, columna 2"
│
├─ 4. ¿Qué significa ese clic? Tres posibilidades:
│
│     a) Es un destino resaltado  → _jugar(movimiento)
│     b) Es una ficha propia      → _seleccionar(casilla)
│     c) Cualquier otra cosa      → _seleccionar(None)  (deselecciona)
│
├─ 5. Si fue (b), SELECCIONAR:
│     movimientos = motor.movimientos_legales(estado)     [motor.py] ⭐
│     self._destinos = {destino: mov  para los que salen de esa casilla}
│     _dibujar()  → se ven los círculos verdes
│
├─ 6. Si fue (a), JUGAR:
│     nuevo = motor.aplicar(estado, movimiento)           [motor.py] ⭐
│            ↑ NO modifica el estado viejo, devuelve uno NUEVO
│     self._estados.append(nuevo)      ← la pila crece
│     self._jugadas.append(texto)      ← el historial crece
│     _refrescar()
│
├─ 7. _refrescar() sincroniza TODO el panel:
│     · ¿de quién es el turno?
│     · marcadores: fichas en tablero / fichas fuera
│     · historial
│     · mensaje inferior
│     · botón Deshacer activado o no
│     · y al final llama a _dibujar()
│
└─ 8. _dibujar() repinta el tablero desde cero:
      _recalcular_geometria()  → ¿de qué tamaño es cada casilla ahora?
      lienzo.delete(ALL)       → borrón y cuenta nueva
      carriles → celdas → rótulos → destinos → fichas → cartel final
```

## 🔑 Las dos únicas llamadas al motor

Fíjate: en todo ese recorrido, `gui.py` llama al motor **solo dos
veces**:

| Llamada | Para qué |
|---|---|
| `motor.movimientos_legales(estado)` | Preguntar **qué se puede hacer** |
| `motor.aplicar(estado, movimiento)` | Pedir **el estado resultante** |

(Más algunas consultas de solo lectura: `es_terminal`, `ganador`,
`fichas_de`.)

> 💬 **Frase para la defensa:** *"La interfaz solo sabe hacer dos
> preguntas: '¿qué jugadas hay?' y '¿cómo queda el tablero si hago
> esta?'. No sabe en qué dirección avanza cada jugador, no sabe quién
> gana, no sabe qué es una salida. Todo eso vive en el motor."*

---

<a name="3"></a>
# 3. ⚙️ `config.py` — el panel de control

**Qué es:** un archivo con **solo constantes**. No tiene ni una
función, ni una clase, ni un `if`. Es una lista de valores con nombre.

**Por qué existe:** porque el enunciado exige que el juego sea
parametrizable y que no haya "números mágicos".

> 🔍 **¿Qué es un "número mágico"?** Un número suelto en medio del
> código cuyo significado no está claro. Por ejemplo `if n % 2 == 0`.
> ¿Por qué 2? ¿Se puede cambiar? ¿Dónde más aparece ese 2? Al
> convertirlo en `DIVISOR_PARIDAD = 2`, el número tiene nombre, vive en
> un solo sitio y se puede cambiar sin buscarlo por todo el proyecto.

## Sección 1 — Identificación de los jugadores

| Constante | Valor | Qué hace |
|---|---|---|
| `JUGADOR_A` | `"A"` | Identificador interno del jugador que avanza a la derecha |
| `JUGADOR_B` | `"B"` | El que avanza hacia arriba |
| `JUGADORES` | `("A", "B")` | Tupla con ambos. **Iterar sobre esto evita escribir "A" y "B" a mano** por todo el proyecto |
| `JUGADOR_INICIAL` | `JUGADOR_A` | Quién mueve primero |
| `EMPATE` | `"EMPATE"` | Lo que devuelve `ganador()` si hay tablas |
| `NOMBRES_JUGADORES` | dict | `"Jugador A"` — el texto que ve el usuario |
| `OBJETIVOS_JUGADORES` | dict | `"avanza a la derecha y sale por el borde derecho"` |

**Por qué se separan el identificador y el nombre:** el motor trabaja
con `"A"` (corto, rápido de comparar); la pantalla muestra
`"Jugador A"`. Si mañana quieres llamarlos "Rojo" y "Azul", cambias un
diccionario y no se rompe nada.

## Sección 2 — Restricciones del tamaño

```python
DIVISOR_PARIDAD = 2            # se comprueba n % DIVISOR
RESTO_PARIDAD_REQUERIDO = 0    # y el resto debe ser este
TAMANO_MINIMO_EXCLUSIVO = 4    # n debe ser ESTRICTAMENTE mayor
TAMANO_MAXIMO_TABLERO = 16     # cota práctica de la interfaz
TAMANO_POR_DEFECTO = 6         # el que aparece marcado al abrir
FICHAS_MENOS_QUE_LADO = 1      # fichas por jugador = n - esto
```

🎯 **La joya de esta sección:** la regla "n par" no está escrita como
`if n % 2 == 0`. Está descompuesta en **divisor + resto exigido**. Eso
permite tres configuraciones distintas sin tocar código:

| Quiero | `DIVISOR_PARIDAD` | `RESTO_PARIDAD_REQUERIDO` |
|---|---|---|
| Solo pares (por defecto) | 2 | 0 |
| Solo impares | 2 | 1 |
| **Pares e impares** | **1** | 0 |

*(El truco de la última fila: todo número entero módulo 1 da 0.)*

> ⚠️ **`TAMANO_MAXIMO_TABLERO` no es una regla del Dodgem.** Es un
> límite práctico para que la interfaz siga siendo legible. Dilo así si
> te preguntan, porque demuestra que distingues las reglas del juego de
> las decisiones de implementación.

## Sección 3 — Geometría y direcciones ⭐ la más importante

```python
DIRECCION_AVANCE = {
    JUGADOR_A: (0, 1),     # Δfila=0, Δcolumna=+1 → Este (derecha)
    JUGADOR_B: (-1, 0),    # Δfila=-1, Δcolumna=0 → Norte (arriba)
}

DIRECCIONES_LATERALES = {
    JUGADOR_A: ((-1, 0), (1, 0)),   # arriba y abajo
    JUGADOR_B: ((0, -1), (0, 1)),   # izquierda y derecha
}

ESQUINA_COMPARTIDA_VACIA = True
```

### Cómo leer un vector

Un vector es `(Δfila, Δcolumna)`: cuánto cambia la fila y cuánto la
columna.

| Vector | Significa |
|---|---|
| `(0, 1)` | una casilla a la **derecha** |
| `(0, -1)` | una casilla a la **izquierda** |
| `(-1, 0)` | una casilla **arriba** (¡la fila 0 es la de arriba!) |
| `(1, 0)` | una casilla **abajo** |

### 🚨 La pregunta que te van a hacer

**❓ "¿Dónde está el código que impide que A retroceda?"**

> ✅ **"No existe tal código."** El vector `(0, -1)` —la izquierda— no
> aparece **en ninguna de las dos listas de A**. No hay un `if` que lo
> prohíba: simplemente nunca se genera. Es prohibir por **omisión**,
> no por validación.

📌 Esa es una respuesta de arquitecto, no de programador. Apréndetela.

### Sobre `ESQUINA_COMPARTIDA_VACIA`

Las dos líneas de partida (la columna izquierda de A y la fila inferior
de B) se cruzan en **una** casilla: la esquina inferior izquierda. Con
esta constante en `True`, esa casilla queda vacía — y por eso cada
jugador acaba con exactamente `n − 1` fichas.

## Sección 4 — Tipos de movimiento

```python
TIPO_AVANCE = "avance"      # hacia adelante, dentro del tablero
TIPO_LATERAL = "lateral"    # esquiva
TIPO_SALIDA = "salida"      # hacia adelante, cae FUERA → la ficha se va
ORDEN_TIPOS_MOVIMIENTO = (TIPO_SALIDA, TIPO_AVANCE, TIPO_LATERAL)
```

**`ORDEN_TIPOS_MOVIMIENTO`** determina en qué orden aparecen las jugadas
en la lista que devuelve el motor. Sirve para dos cosas:

1. **Determinismo:** la misma posición produce siempre la misma lista,
   así las pruebas son reproducibles.
2. **Es un regalo para Valentín:** su poda Alfa-Beta corta antes si las
   jugadas prometedoras se examinan primero.

> 💬 *"Ese orden lo puse yo pensando en la Fase 2, antes de que
> existiera el agente."* ← esto suma muchísimo.

## Sección 5 — Condiciones de término

```python
BLOQUEADO_PIERDE = "bloqueado_pierde"
BLOQUEADO_GANA = "bloqueado_gana"
REGLA_BLOQUEO = BLOQUEADO_PIERDE    # ← la activa

TABLAS_HABILITADAS = False
LIMITE_JUGADAS_SIN_PROGRESO = 100
```

**Las dos convenciones de bloqueo:**

| Regla | Significa |
|---|---|
| `BLOQUEADO_PIERDE` | Si te quedas sin jugadas legales, **pierdes**. Es lo que pide el enunciado de la asignatura. |
| `BLOQUEADO_GANA` | Si te quedas sin jugadas, **ganas**, porque se penaliza a quien te bloqueó. Es la regla del **Dodgem clásico**. |

> ⚠️ **Prepárate para esto:** el Dodgem original usa la convención
> **contraria** a la del enunciado. Si el profesor lo menciona, tu
> respuesta es: *"Correcto, y es deliberado. Implementamos las dos y se
> elige con una constante. Se lo cambio ahora si quiere."*

**Las tablas** están **desactivadas** por defecto porque el enunciado
no las pide. Existen porque en tableros pares una partida puede no
terminar nunca si ambos solo esquivan.

## Sección 6 — Rendimiento

```python
VALIDAR_MOVIMIENTOS_AL_APLICAR = True
```

Cuando está en `True`, `aplicar()` comprueba que el movimiento sea
legal antes de construir el estado nuevo. Es lo correcto mientras
juegan humanos (un clic mal traducido daría error en vez de corromper
la partida). El buscador de Valentín lo desactiva pasando
`validar=False`.

## Sección 7 — Interfaz

Tamaños de ventana, márgenes, fracciones de dibujo, tipografías y la
**paleta pastel**. Lo importante: `PALETA` es un diccionario con
**nombres semánticos**, no colores.

```python
PALETA = {
    "fondo_ventana": "#FAF6F2",
    "ficha_a": "#F2A7AF",
    "destino_normal": "#B4E1C4",
    ...
}
```

> 💬 *"Las claves describen **el papel** del color, no el color. Por eso
> se puede cambiar el tema completo editando un solo diccionario."*

## Secciones 8 y 9 — De tus compañeros

Los pesos de la heurística (Carlos) y los modos/niveles del agente
(Valentín). Tú no tienes que dominarlas, pero **sí saber que están ahí
y por qué**: para que todo lo parametrizable del proyecto viva en el
mismo sitio.

---

<a name="4"></a>
# 4. 🧠 `motor.py` — las reglas del juego

**Qué es:** el corazón. Contiene **todas** las reglas del Dodgem.

**Qué NO hace** (y esto hay que decirlo en voz alta):

- ❌ No imprime nada
- ❌ No lee el teclado
- ❌ No dibuja
- ❌ No guarda ninguna variable global
- ❌ No modifica nada de lo que recibe

> 💬 *"Es una **máquina de estados pura**: le das un estado y te
> devuelve un valor. Dos llamadas con la misma entrada dan siempre la
> misma salida."*

---

## 4.1 🧊 Las dos estructuras de datos

### `Movimiento` — una jugada

```python
class Movimiento(NamedTuple):
    origen: Casilla       # siempre dentro del tablero
    destino: Casilla      # ¡puede caer FUERA! eso es una salida
    tipo: str             # "avance" | "lateral" | "salida"

    @property
    def es_salida(self):
        return self.tipo == config.TIPO_SALIDA
```

**`es_salida` es una `@property`:** se usa como `movimiento.es_salida`
(sin paréntesis), como si fuera un atributo. Existe para no escribir
`movimiento.tipo == config.TIPO_SALIDA` en veinte sitios.

**❓ "¿Por qué el destino puede estar fuera del tablero?"**

Porque una salida es un movimiento con destino **virtual**. Ficha de A
en `(2,5)` con n=6 → destino `(2,6)`, que no existe. Guardar esa
coordenada tiene dos ventajas concretas:

- La interfaz dibuja el carril de salida en la columna 6, y el destino
  cae **exactamente ahí**. Cero casos especiales para detectar el clic.
- El historial es reconstruible: se sabe por dónde salió cada ficha.

### `Estado` — la fotografía completa de la partida

```python
class Estado(NamedTuple):
    n: int                          # lado del tablero
    fichas_a: FrozenSet[Casilla]    # dónde están las fichas de A
    fichas_b: FrozenSet[Casilla]    # dónde están las de B
    turno: str                      # "A" o "B"
    salidas_a: int                  # cuántas de A ya salieron
    salidas_b: int                  # cuántas de B ya salieron
    sin_progreso: int               # jugadas sin que salga ninguna
```

Ejemplo real (n=6, posición inicial):

```python
Estado(
    n=6,
    fichas_a=frozenset({(0,0), (1,0), (2,0), (3,0), (4,0)}),
    fichas_b=frozenset({(5,1), (5,2), (5,3), (5,4), (5,5)}),
    turno="A",
    salidas_a=0, salidas_b=0, sin_progreso=0,
)
```

### 🚨 Las tres preguntas garantizadas

**❓ 1. "¿Qué es un `NamedTuple` y por qué no una clase normal?"**

Es una tupla con campos que tienen nombre. Escribes `estado.turno` en
vez de `estado[3]`. Y lo más importante: **es inmutable**. Una vez
creado, no se puede modificar.

```python
estado.turno = "B"     # ❌ AttributeError: can't set attribute
```

**❓ 2. "¿Qué es un `frozenset` y por qué no un `set`?"**

Un `set` es un conjunto (sin orden, sin repetidos, con búsqueda O(1)).
Un `frozenset` es lo mismo pero **inmutable**.

¿Por qué importa? Porque en Python **solo se puede meter en un
diccionario, como clave, algo inmutable**. Con `set` el estado no sería
"hashable" y no serviría de clave.

```python
tabla = {}
tabla[estado] = 5     # ✅ funciona porque todo dentro es inmutable
```

Y eso es exactamente lo que Valentín necesitaba para su tabla de
transposiciones. **Se lo diste gratis.**

**❓ 3. "¿Por qué conjuntos de coordenadas y no una matriz n×n?"**

| Operación | Matriz `n×n` | `frozenset` |
|---|---|---|
| ¿Casilla ocupada? | O(1) | **O(1)** |
| Generar movimientos | O(n²) — recorrer todo | **O(fichas)** = O(n) |
| Copiar el estado | O(n²) | O(fichas) |
| ¿Sirve de clave de dict? | ❌ | ✅ |

Con n=16 la matriz tiene **256 casillas** pero solo hay **15 fichas**
por bando. Recorrer 256 celdas para encontrar 15 fichas es tirar
trabajo — y en la Fase 2 eso se hace cientos de miles de veces.

### 🧭 El sistema de coordenadas (trampa clásica)

```
INTERNO (motor):      (fila, columna) en base 0.  Fila 0 = ARRIBA
ENUNCIADO (humano):   fila 1 = arriba, columna n = derecha
```

**❓ "¿Por qué no usan la numeración del enunciado?"**

> *"Porque en base 0 no hay que sumar y restar 1 en cada cálculo, y ahí
> es donde se cometen los errores. La conversión ocurre **solo en el
> borde**, en `a_coordenada_humana()`."*

---

## 4.2 🔩 Las funciones auxiliares (las pequeñas)

Estas son cortas y aburridas, pero **existen por una razón**: para que
el resto del código no repita la misma comprobación una y otra vez.

### `oponente(jugador) -> str`

Devuelve `"B"` si le das `"A"` y viceversa.
**Por qué existe:** para no escribir el ternario en 15 sitios. Si un
día hubiera tres jugadores, se cambia aquí.

### `fichas_de(estado, jugador) -> frozenset`

Devuelve `estado.fichas_a` o `estado.fichas_b` según el jugador.
**Por qué existe:** casi todas las funciones del motor necesitan "las
fichas del que juega ahora" sin saber cuál es. Sin esto, cada una
tendría un `if jugador == "A"` propio.

### `salidas_de(estado, jugador) -> int`

Lo mismo pero con el contador de fichas fuera.

### `casillas_ocupadas(estado) -> frozenset`

La **unión** de las fichas de ambos: `fichas_a | fichas_b`.
**Por qué existe:** se calcula **una sola vez** al principio de
`movimientos_legales()`, en vez de consultar dos conjuntos por cada
casilla candidata.

### `dentro_del_tablero(casilla, n) -> bool`

```python
fila, columna = casilla
return 0 <= fila < n and 0 <= columna < n
```

**Por qué existe:** es la comprobación que distingue un movimiento
normal de una salida. Está en un solo sitio para que no haya dos
versiones que puedan discrepar.

### `fichas_por_jugador(n) -> int`

Devuelve `n - config.FICHAS_MENOS_QUE_LADO`, o sea `n − 1`.
**Por qué existe:** el número de fichas aparece en el motor (para
colocarlas), en la interfaz (para la barra de progreso) y en las
pruebas. Una sola fuente de verdad.

---

## 4.3 🔒 Las funciones privadas (con guion bajo)

> 🔍 **¿Qué significa el guion bajo inicial?** Es una convención de
> Python: *"esto es de uso interno del módulo, no forma parte de la
> API"*. No lo impide el lenguaje, es un acuerdo entre programadores.

### `_linea_de_partida(n, direccion_avance) -> list[Casilla]`

**Qué hace:** calcula el borde entero donde se despliegan las fichas de
un jugador.

**Cómo funciona:**

```python
delta_fila, delta_columna = direccion_avance
if delta_columna != 0:
    # Avanza en horizontal → arranca en una COLUMNA
    columna = 0 if delta_columna > 0 else n - 1
    return [(fila, columna) for fila in range(n)]
# Avanza en vertical → arranca en una FILA
fila = 0 if delta_fila > 0 else n - 1
return [(fila, columna) for columna in range(n)]
```

**La lógica:** en Dodgem cada bando arranca pegado al borde **opuesto**
a su dirección de avance, para tener el tablero por delante.

- A avanza a la derecha (`Δcolumna = +1`) → arranca en la **columna 0**
- B avanza hacia arriba (`Δfila = −1`) → arranca en la **fila n−1**

🎯 **Por qué esto es lo mejor que escribiste:**

> *"No escribí 'A empieza en la columna 0'. Escribí 'A empieza en el
> borde opuesto a su avance', y el código lo calcula. Por eso si usted
> invierte la dirección de A en `config.py`, las fichas se recolocan
> solas."*

### `_recortar_linea(casillas, cantidad, esquina, jugador) -> frozenset`

**Qué hace:** deja exactamente `fichas_por_jugador(n)` fichas sobre la
línea de partida.

**Cuándo hace falta:** normalmente la línea tiene `n` casillas, se quita
la esquina compartida y quedan `n − 1`, que es justo lo que se quiere.
Pero si alguien cambia `FICHAS_MENOS_QUE_LADO`, sobran casillas y hay
que decidir cuáles quitar.

**El criterio:** se descartan las **más cercanas a la esquina
compartida**.

> *"No es caprichoso: la esquina es la zona donde los dos bandos se
> estorban desde la primera jugada, así que quitar fichas de ahí es lo
> que menos altera el carácter de la apertura. Y como se mide por
> distancia y no por índice, sigue teniendo sentido si se invierte una
> dirección."*

Si le piden más fichas de las que caben, **lanza `ValueError` con un
mensaje explícito** en vez de romperse en silencio.

### `_clave_de_orden(movimiento) -> tuple`

**Qué hace:** genera la clave con la que se ordena la lista de jugadas.
Primero por tipo (según `ORDEN_TIPOS_MOVIMIENTO`), luego por
coordenadas.

---

## 4.4 ⭐ Las 6 funciones que exige el enunciado

## 1️⃣ `validar_n(n) -> bool`

**Qué hace:** dice si un tamaño de tablero es aceptable.

```python
def validar_n(n):
    if isinstance(n, bool) or not isinstance(n, int):
        return False
    if n % config.DIVISOR_PARIDAD != config.RESTO_PARIDAD_REQUERIDO:
        return False
    if n <= config.TAMANO_MINIMO_EXCLUSIVO:
        return False
    return n <= config.TAMANO_MAXIMO_TABLERO
```

**Línea por línea:**

| Línea | Qué comprueba | Por qué |
|---|---|---|
| `isinstance(n, bool)` | Que no sea `True`/`False` | 🔍 En Python `True == 1` y `isinstance(True, int)` es `True`. Sin esta guarda, `validar_n(True)` daría cosas raras |
| `not isinstance(n, int)` | Que sea entero | `"6"` o `6.0` no valen |
| `n % DIVISOR != RESTO` | La paridad | Parametrizada, no `n % 2 == 0` |
| `n <= MINIMO_EXCLUSIVO` | Que sea > 4 | "exclusivo" = no incluye el 4 |
| `n <= MAXIMO` | Cota de la interfaz | No es regla del juego |

**Por qué devuelve `bool` y no un mensaje:** para que el contrato sea
limpio. El mensaje lo da su hermana.

### `motivo_invalidez(n) -> str | None`

**Qué hace:** explica **en castellano** por qué se rechazó un tamaño.
Devuelve `None` si el tamaño es válido.

**Por qué existe separada:** para que `validar_n` siga siendo un `bool`
puro (útil para el motor) y la interfaz tenga texto que mostrar, **sin
duplicar la lógica de validación**.

### `tamanos_validos() -> tuple[int, ...]`

**Qué hace:** devuelve todos los tamaños aceptados: `(6, 8, 10, 12, 14, 16)`.

**Por qué existe:** 🎯 **la pantalla de configuración genera sus
botones con esto.** Si cambias `config.py`, los botones cambian solos.

> 💬 *"Los botones de tamaño no están escritos a mano en la interfaz.
> Se generan desde el motor."*

---

## 2️⃣ `estado_inicial(n) -> Estado`

**Qué hace:** construye la posición de apertura.

**Los cuatro pasos:**

```python
# PASO 1: validar
if not validar_n(n):
    raise ValueError(motivo_invalidez(n))

# PASO 2: calcular los dos bordes de partida
linea_a = _linea_de_partida(n, config.DIRECCION_AVANCE[JUGADOR_A])
linea_b = _linea_de_partida(n, config.DIRECCION_AVANCE[JUGADOR_B])

# PASO 3: la intersección es UNA casilla: la esquina compartida
compartidas = set(linea_a) & set(linea_b)     # → {(5, 0)} con n=6
libres_a = [c for c in linea_a if c not in compartidas]
libres_b = [c for c in linea_b if c not in compartidas]

# PASO 4: recortar a la cantidad exacta y comprobar el invariante
fichas_a = _recortar_linea(libres_a, fichas_por_jugador(n), esquina, "A")
fichas_b = _recortar_linea(libres_b, fichas_por_jugador(n), esquina, "B")
if fichas_a & fichas_b:
    raise ValueError("...fichas de ambos jugadores en la misma casilla")
```

**El resultado con n=6:**

```
     1  2  3  4  5  6
 1   A  .  .  .  .  .
 2   A  .  .  .  .  .
 3   A  .  .  .  .  .
 4   A  .  .  .  .  .
 5   A  .  .  .  .  .
 6   .  B  B  B  B  B
     ↑
     esquina compartida: queda vacía
```

**Por qué salen 5 fichas sin contar nada:** la columna de A tiene 6
casillas, se le quita la esquina → 5. La fila de B tiene 6, se le quita
la esquina → 5. `n − 1` sale solo de la geometría.

🛡️ **El invariante final:** comprueba que ninguna casilla esté en los
dos conjuntos. Si una configuración exótica dejara dos fichas
encimadas, falla con un mensaje claro **en vez de arrancar una partida
corrupta**. Menciónalo: demuestra que pensaste en la robustez.

---

## 3️⃣ `movimientos_legales(estado) -> tuple[Movimiento, ...]`

**Qué hace:** devuelve **todas** las jugadas legales del jugador en
turno.

```python
jugador = estado.turno
propias = fichas_de(estado, jugador)
ocupadas = casillas_ocupadas(estado)          # una sola vez

avance = config.DIRECCION_AVANCE[jugador]
laterales = config.DIRECCIONES_LATERALES[jugador]
vectores = (avance,) + tuple(laterales)       # los 3 vectores

movimientos = []
for origen in propias:                        # cada ficha propia
    fila, columna = origen
    for vector in vectores:                   # cada dirección posible
        destino = (fila + vector[0], columna + vector[1])
        es_avance = vector == avance

        if not dentro_del_tablero(destino, estado.n):
            if es_avance:                     # ⭐⭐⭐ LA CLAVE
                movimientos.append(Movimiento(origen, destino, SALIDA))
            continue

        if destino in ocupadas:
            continue                          # sin capturas ni saltos

        tipo = TIPO_AVANCE if es_avance else TIPO_LATERAL
        movimientos.append(Movimiento(origen, destino, tipo))

movimientos.sort(key=_clave_de_orden)
return tuple(movimientos)
```

### 🎯 La línea que tienes que saber explicar

```python
if not dentro_del_tablero(destino, estado.n):
    if es_avance:
        movimientos.append(Movimiento(origen, destino, SALIDA))
    continue
```

> 💬 **La joya de tu defensa:** *"Un destino fuera del tablero es legal
> **solo si el vector usado era el de avance**. Esa única condición
> implementa a la vez las dos reglas de salida del enunciado: que A
> solo pueda salir por el borde derecho y que B solo pueda salir por
> arriba. Un intento de salir lateralmente cae fuera del tablero con un
> vector que no es el de avance, y se descarta sin necesidad de
> escribir una regla aparte."*

**Ejemplo concreto para explicarlo:** ficha de A en `(0, 3)` — fila
superior. Sus tres vectores:

| Vector | Destino | ¿Qué pasa? |
|---|---|---|
| `(0, 1)` avance | `(0, 4)` | Dentro y vacía → **jugada legal** |
| `(-1, 0)` lateral arriba | `(-1, 3)` | Fuera, pero **no es avance** → ❌ descartada |
| `(1, 0)` lateral abajo | `(1, 3)` | Dentro → legal si está vacía |

**Así se implementa "A no puede salir por el borde superior" sin
escribir esa regla.**

### Otras dos cosas de esta función

**`return tuple(...)` y no `list`:** una tupla es inmutable. Ninguna
capa superior puede alterar por accidente la lista de jugadas.

**`movimientos.sort(...)`:** por determinismo y por la poda de
Valentín. Ver `ORDEN_TIPOS_MOVIMIENTO`.

---

## 3️⃣bis Las dos hermanas de rendimiento

Estas dos no las exige el enunciado. **Existen porque medimos y hacían
falta.**

### `hay_movimientos_legales(estado) -> bool`

Es `movimientos_legales` pero **corto-circuitada**: en cuanto encuentra
**una** jugada, devuelve `True` y para.

**Por qué:** para detectar un bloqueo basta saber si hay al menos una
jugada. Construir la lista completa y ordenarla es trabajo tirado. La
usa `ganador()`, que se llama en cada nodo del árbol de búsqueda.

### `contar_movimientos_legales(estado, jugador) -> int`

Cuenta las jugadas **sin crear los objetos `Movimiento` ni ordenarlos**.

**Por qué:** la heurística de Carlos la llama en cada hoja del árbol.
Medido: pasó de **30,6 µs a 15,7 µs** por evaluación — **3,5× más
rápido**. El parámetro `jugador` permite medir la movilidad del bando
que **no** está en turno.

> ⚠️ **Posible objeción:** *"¿No están duplicando la regla?"*
> **Respuesta:** *"Es la misma condición escrita una segunda vez por
> rendimiento, y está justo al lado de la original a propósito. Además
> hay una prueba unitaria que verifica que el contador rápido da
> exactamente lo mismo que `len(movimientos_legales(...))`."*

---

## 4️⃣ `aplicar(estado, movimiento) -> Estado` ⭐⭐ LA MÁS IMPORTANTE

**Qué hace:** devuelve un estado **NUEVO** con la jugada aplicada.
**Qué NO hace:** tocar el estado original. Ni un byte.

```python
def aplicar(estado, movimiento, validar=None):
    if validar is None:
        validar = config.VALIDAR_MOVIMIENTOS_AL_APLICAR
    if validar:
        if movimiento not in movimientos_legales(estado):
            raise ValueError("Movimiento ilegal...")

    jugador = estado.turno
    nuevas_fichas = set(fichas_de(estado, jugador))   # COPIA
    nuevas_fichas.discard(movimiento.origen)          # quita del origen

    salidas = salidas_de(estado, jugador)
    if movimiento.es_salida:
        salidas += 1
        sin_progreso = 0            # sacar una ficha SÍ es progreso
    else:
        nuevas_fichas.add(movimiento.destino)         # pone en destino
        sin_progreso = estado.sin_progreso + 1

    campos = {"turno": oponente(jugador), "sin_progreso": sin_progreso}
    if jugador == config.JUGADOR_A:
        campos["fichas_a"] = frozenset(nuevas_fichas)
        campos["salidas_a"] = salidas
    else:
        campos["fichas_b"] = frozenset(nuevas_fichas)
        campos["salidas_b"] = salidas

    return estado._replace(**campos)     # ⭐ devuelve una tupla NUEVA
```

### 🔍 Las tres piezas que te pueden preguntar

**❓ "¿Qué es `_replace`? El guion bajo sugiere que es privado."**

> *"Es la **API oficial y documentada** de `NamedTuple`. El guion bajo
> está para no chocar con nombres de campo que pueda poner el usuario,
> no porque sea privado. **No muta nada**: construye una tupla nueva con
> los campos indicados reemplazados."*

**❓ "¿Por qué `set(...)` y luego `frozenset(...)`?"**

> *"Porque `frozenset` es inmutable: no puedo hacerle `.add()` ni
> `.discard()`. Así que copio a un `set` normal, lo modifico, y lo
> vuelvo a congelar al construir el estado nuevo. **El original nunca se
> toca**."*

**❓ "¿Y el parámetro `validar`?"**

> *"Por defecto lee `config.VALIDAR_MOVIMIENTOS_AL_APLICAR`. El
> buscador de Valentín pasa `validar=False` porque solo aplica
> movimientos que él mismo sacó de `movimientos_legales()`: revalidar
> regeneraría la lista entera en cada nodo. Se pasa **por argumento** y
> no cambiando la constante global para no crear una **condición de
> carrera** — el agente busca en otro hilo mientras la interfaz sigue
> usando el motor."*

### 🎯 La respuesta que demuestra que entiendes el proyecto entero

**❓ "¿Y esto de la inmutabilidad para qué sirve en la práctica?"**

> *"Minimax explora miles de partidas hipotéticas. Con estado mutable
> tendrías que aplicar la jugada, bajar en la recursión y luego
> **deshacerla** al volver — el patrón do/undo, que es donde se cometen
> los errores más difíciles de encontrar. Como `aplicar()` es pura, el
> padre simplemente pasa el hijo a la llamada recursiva y sigue
> intacto.*
>
> *Y en mi parte tiene un beneficio directo: el botón **Deshacer** es
> una pila de estados. No reconstruye nada, no invierte ninguna jugada.
> Solo descarta el último y el anterior sigue ahí, intacto, porque
> nadie lo modificó nunca."*

---

## 5️⃣ y 6️⃣ `ganador(estado)` y `es_terminal(estado)`

```python
def ganador(estado):
    # 1. Victoria por salida (la comprobación más barata)
    if not estado.fichas_a: return config.JUGADOR_A
    if not estado.fichas_b: return config.JUGADOR_B

    # 2. Tablas por falta de progreso (opcional)
    if config.TABLAS_HABILITADAS:
        if estado.sin_progreso >= config.LIMITE_JUGADAS_SIN_PROGRESO:
            return config.EMPATE

    # 3. Bloqueo (la más costosa: hay que generar movimientos)
    if not hay_movimientos_legales(estado):
        if config.REGLA_BLOQUEO == config.BLOQUEADO_PIERDE:
            return oponente(estado.turno)
        return estado.turno

    return None      # la partida sigue


def es_terminal(estado):
    return ganador(estado) is not None
```

**❓ "¿Por qué ese orden?"**
1. **Victoria por salida:** dos comprobaciones de conjunto vacío. Es
   barata y tiene prioridad.
2. **Tablas:** una comparación de enteros.
3. **Bloqueo:** hay que generar movimientos. La más costosa, al final.

**❓ "¿Por qué `not estado.fichas_a` significa que A ganó?"**
Porque en Python un conjunto vacío es "falso". Si A no tiene ninguna
ficha en el tablero es porque **las sacó todas**. Y sacarlas todas es
la condición de victoria.

**❓ "¿Por qué `es_terminal` está definida en función de `ganador`?"**

> *"Para que no puedan desincronizarse. Existe **una sola definición**
> de fin de partida y vive en `ganador()`. Si estuvieran escritas por
> separado, alguien podría cambiar una y olvidar la otra."*

### `motivo_de_termino(estado) -> str | None`

Explica en castellano **por qué** terminó la partida. Distingue las dos
formas de ganar:

```python
if not fichas_de(estado, resultado):
    return "Jugador A saco todas sus fichas del tablero."
# si el ganador SÍ tiene fichas, ganó porque el otro se bloqueó
return "Jugador B quedo sin movimientos legales y pierde."
```

**El truco:** si el ganador **no tiene fichas**, ganó por salida. Si
**sí las tiene**, ganó porque el rival se bloqueó. No hace falta
guardar ningún dato extra: se deduce del estado.

---

## 4.5 🖨️ Las funciones de presentación y diagnóstico

Estas tres no son reglas. Traducen el estado a texto.

### `a_coordenada_humana(casilla) -> str`

Convierte `(2, 0)` → `"f3c1"`. **Aquí y solo aquí** se pasa de base 0 a
la numeración del enunciado.

### `describir_movimiento(movimiento, jugador) -> str`

Genera la línea del historial:
`"Jugador A  f2c1  ->  f2c2  (avance)"` o `"Jugador A  f2c6  ->  SALE"`.

### `tablero_ascii(estado) -> str`

Dibuja el tablero en texto plano:

```
     1  2  3  4  5  6
 1   A  .  .  .  .  .
 ...
Turno: Jugador A | Fuera -> A: 0, B: 0
```

🎯 **Esta es tu red de seguridad en la defensa.** Si la interfaz falla
por lo que sea, `python main.py --diagnostico` demuestra que el motor
funciona igual. Y si el profesor cambia un parámetro, es la forma más
rápida de ver el efecto.

---

<a name="5"></a>
# 5. 🚪 `main.py` — el arranque

El archivo más corto (100 líneas). Solo hace tres cosas.

### `construir_analizador() -> ArgumentParser`

Define los argumentos de línea de comandos con `argparse` (biblioteca
estándar):

| Argumento | Qué hace |
|---|---|
| `--n TAMANO` | Fija el tablero sin pasar por la pantalla de configuración |
| `--modo` | `humano_vs_humano`, `humano_vs_agente`, ... |
| `--nivel` | `facil`, `medio`, `dificil`, `experto` |
| `--diagnostico` | Imprime el estado inicial por consola y sale |

**Por qué existe `--n`:** el enunciado pide que el tamaño sea *"entrada
en la ejecución"*. Así se cumple literalmente, **sin renunciar** a
elegirlo también en la interfaz.

### `imprimir_diagnostico(n)`

Vuelca por consola: el tamaño, las fichas por jugador, el tablero
ASCII, **todos** los movimientos legales del primer turno, y qué
devuelven `es_terminal` y `ganador`.

### `main(argumentos=None) -> int`

```python
opciones = construir_analizador().parse_args(argumentos)

# 1. Validación temprana con el MISMO criterio del motor
if opciones.n is not None and not motor.validar_n(opciones.n):
    print("Tamano invalido: %s" % motor.motivo_invalidez(opciones.n),
          file=sys.stderr)
    return 2

# 2. Modo diagnóstico: no abre ventana
if opciones.diagnostico:
    imprimir_diagnostico(opciones.n or config.TAMANO_POR_DEFECTO)
    return 0

# 3. La interfaz se importa AQUÍ, no arriba
try:
    import gui
except ImportError:
    print("No se pudo cargar tkinter...", file=sys.stderr)
    return 1

gui.lanzar(opciones.n, opciones.modo, opciones.nivel)
return 0
```

### 🔍 Tres detalles que puedes mencionar

**1. `import gui` está dentro de la función, no arriba.**

> *"A propósito. Así `--diagnostico` sigue funcionando en un equipo
> donde falte el módulo `tkinter`, que en algunas distribuciones de
> Linux se instala aparte. Si el import estuviera arriba, el programa
> ni arrancaría."*

**2. Devuelve códigos de salida distintos:** `0` = todo bien, `1` =
falta tkinter, `2` = tamaño inválido. Es la convención de Unix.

**3. La validación usa `motor.validar_n`,** no una copia. Un solo
criterio para toda la aplicación.

---

<a name="6"></a>
# 6. 🖼️ `gui.py` — la ventana

El archivo más largo, pero **el más fácil de defender**, porque no
contiene ninguna regla del juego.

> 💬 **Tu frase:** *"`gui.py` no sabe jugar al Dodgem. Solo sabe hacer
> dos preguntas al motor: '¿qué jugadas hay?' y '¿cómo queda el tablero
> si hago esta?'."*

## 6.1 🧱 Componentes reutilizables

### `_familia_tipografica(raiz) -> str`

Elige la primera tipografía disponible de una lista de preferencias.

**Por qué:** en Linux, Windows y macOS el conjunto de fuentes instaladas
es distinto. Pedir una que no existe produce una sustitución arbitraria
y fea. Esto prueba varias en orden y usa la primera que encuentra.

### `class BotonPastel(tk.Frame)`

Un botón dibujado a mano: un `Frame` con un `Label` dentro y los
eventos enlazados manualmente.

**❓ "¿Por qué no usan `tk.Button`?"**

> *"Porque en macOS `tk.Button` **ignora el color de fondo** y en
> Windows dibuja un relieve gris que rompe el estilo pastel. Un `Frame`
> con un `Label` dentro se ve idéntico en los tres sistemas
> operativos."*

Sus métodos:

| Método | Qué hace |
|---|---|
| `_colores(resaltado)` | Devuelve (fondo, texto) según variante y estado |
| `_repintar(resaltado)` | Aplica esos colores |
| `_al_presionar` / `_al_entrar` / `_al_salir` | Manejan clic y hover |
| `habilitar(activo)` | Activa o desactiva (cambia color y cursor) |
| `marcar(marcado)` | Marca un "chip" como seleccionado |

**Las tres variantes:** `"normal"`, `"primario"` (el verde de
Comenzar), `"chip"` (los selectores de tamaño y modo).

### `_crear_tarjeta(maestro) -> tk.Frame`

Crea un contenedor con fondo de tarjeta y borde suave. Todas las
tarjetas del proyecto salen de aquí, así que se ven iguales.

### `_rectangulo_redondeado(lienzo, x1, y1, x2, y2, radio, ...)`

**Qué hace:** dibuja un rectángulo con esquinas redondeadas en un
`Canvas`.

**Por qué existe:** ⚠️ **Tkinter no ofrece esta primitiva.** Solo tiene
rectángulos con esquinas rectas.

**El truco:** se crea un **polígono** con los vértices duplicados en las
esquinas y se activa `smooth=True`, que aplica una curva de Bézier
sobre esos puntos.

```python
puntos = [x1+radio, y1,  x2-radio, y1,  x2, y1,
          x2, y1+radio,  x2, y2-radio,  x2, y2, ...]
return lienzo.create_polygon(puntos, smooth=True, **kwargs)
```

🎯 Si te preguntan "¿cómo hicieron las esquinas redondeadas?", esta es
una respuesta que impresiona porque revela que conoces la limitación de
la herramienta.

---

## 6.2 🎛️ `class PantallaConfiguracion`

La primera pantalla: elegir tamaño, modo y nivel.

| Método | Qué hace |
|---|---|
| `__init__` | Guarda los valores por defecto y llama a `_construir` |
| `_construir` | Título, subtítulo y **dos columnas** (ajustes a la izquierda, reglas a la derecha) |
| `_construir_tarjeta_tamano` | Los chips de tamaño + la casilla "otro valor" |
| `_construir_tarjeta_oponente` | Los 4 modos + los 4 niveles |
| `_construir_tarjeta_reglas` | El recordatorio de reglas |
| `_elegir(n)` | Marca un chip de tamaño |
| `_aplicar_entrada()` | Valida el número escrito a mano |
| `_elegir_modo(modo)` | Marca un modo y **activa o desactiva** los niveles |
| `_elegir_nivel(nivel)` | Marca un nivel y muestra su descripción |
| `_comenzar()` | Le pide a la aplicación que arranque la partida |

### 🔍 Tres detalles que demuestran buen diseño

**1. Los chips de tamaño se generan desde el motor:**

```python
for n in motor.tamanos_validos():
    chip = BotonPastel(fila_chips, str(n), lambda valor=n: self._elegir(valor), ...)
```

> *"Si en `config.py` se amplía el máximo, aparecen solos."*

**2. La tarjeta de reglas se arma leyendo `config.py`:**

```python
if config.REGLA_BLOQUEO == config.BLOQUEADO_PIERDE:
    texto_bloqueo = "Sin movimientos legales al inicio del turno: ese jugador PIERDE."
else:
    texto_bloqueo = "...ese jugador GANA (regla clasica)."
```

> 🎯 *"Si el profesor cambia una regla, **la pantalla lo refleja sola**.
> No hay que editar la interfaz."* ← esto es de nota alta.

**3. El campo "otro valor" usa el motor para validar:**

```python
if not motor.validar_n(valor):
    self._mensaje.configure(text=motor.motivo_invalidez(valor), ...)
```

La interfaz **no sabe** que n debe ser par. Solo pregunta y muestra la
respuesta.

---

## 6.3 🎮 `class PantallaJuego` — el tablero

La clase grande. La voy a partir en bloques.

### 📦 Bloque A — Estado interno (`__init__`)

```python
self._estados = [motor.estado_inicial(n)]   # LA PILA de estados
self._jugadas = []                          # historial de textos
self._seleccion = None                      # ficha activa
self._destinos = {}                         # {casilla: Movimiento}
```

**❓ "¿Por qué una lista de estados y no un solo estado?"**

> *"Porque es la pila del botón Deshacer. Como el motor nunca modifica
> un estado, guardar la referencia anterior basta: `_estados[-1]` es la
> posición actual, `_estados[-2]` la anterior, y deshacer es
> simplemente `pop()`."*

Y una **propiedad** que da la posición actual:

```python
@property
def _estado(self):
    return self._estados[-1]
```

**❓ "¿Por qué el historial no está dentro del `Estado`?"**

> *"Porque Minimax no lo necesita y arrastrarlo multiplicaría la
> memoria del árbol de búsqueda. El historial es responsabilidad de la
> interfaz."*

> 💡 **En tu modo humano vs humano**, `self._agentes` queda **vacío**,
> así que la tarjeta del bot no se crea y toda la maquinaria de hilos
> nunca se ejecuta. Puedes decirlo: *"En este modo ese código no
> corre."*

### 📐 Bloque B — Geometría

La rejilla que se dibuja es **más grande que el tablero**: además de
las n×n casillas, reserva una fila o columna extra por cada carril de
salida.

```
   columnas:  -  0  1  2  3  4  5   6      (6 = carril de A)
   filas:
      -1      ░  ░  ░  ░  ░  ░  ░           ← carril de B (arriba)
       0      1  ·  ·  ·  ·  ·  ·   ▓
       1      2  ·  ·  ·  ·  ·  ·   ▓
      ...
       5      6  ·  ·  ·  ·  ·  ·   ▓
              ↑  1  2  3  4  5  6
           margen de rótulos
```

| Método | Qué hace |
|---|---|
| `_carriles_de_salida()` | **Deduce** dónde va el carril de cada jugador a partir de `config.DIRECCION_AVANCE` |
| `_recalcular_geometria()` | Calcula el lado de la celda y el origen, centrando el dibujo |
| `_esquina(fila, columna)` | Casilla lógica → píxel superior izquierdo |
| `_centro(fila, columna)` | Casilla lógica → píxel del centro |
| `_casilla_desde_pixel(px, py)` | Píxel → casilla lógica (**la inversa exacta**) |

### 🎯 El detalle elegante de la geometría

Un movimiento de salida tiene destino `(fila, 6)` con n=6 — una
coordenada que **no existe en el tablero**. Pero el carril de A se
dibuja justo en la columna 6.

> 💬 *"La coordenada virtual de una salida cae **exactamente** sobre el
> carril dibujado. Por eso no hace falta ningún caso especial ni para
> pintarla ni para detectar el clic: el usuario hace clic en el carril
> y `_casilla_desde_pixel` devuelve `(fila, 6)`, que es justo la clave
> que hay en el diccionario de destinos."*

Y las posiciones de los carriles **no están escritas a mano**: salen de
`_carriles_de_salida()`, que lee las direcciones de `config.py`. Si
inviertes la dirección de A, su carril se muda solo al borde correcto.

### 🎨 Bloque C — Dibujo

`_dibujar()` es el director de orquesta:

```python
if self._lienzo.winfo_width() <= 1:
    return                              # la ventana aún no tiene tamaño
self._recalcular_geometria()
self._lienzo.delete(tk.ALL)             # borra TODO
self._dibujar_carriles()                # franjas de salida + flechas
self._dibujar_celdas()                  # el damero
self._dibujar_rotulos()                 # números de fila y columna
self._dibujar_ultima_jugada_del_bot()   # resalte ámbar (inerte sin bot)
self._dibujar_marcadores_de_destino()   # círculos verdes y lilas
self._dibujar_fichas()                  # las fichas
if motor.es_terminal(self._estado):
    self._dibujar_cartel_final()        # tarjeta de "Gana X"
```

**❓ "¿Repintan todo de cero cada vez? ¿No es ineficiente?"**

> *"Es más simple y mucho menos propenso a errores que actualizar
> objetos individuales, y con tableros de a lo más 16×16 el coste es
> irrelevante. Preferimos código correcto a una optimización que no
> hace falta."*

Detalles de cada función de dibujo:

| Función | Qué hace |
|---|---|
| `_dibujar_carriles()` | Franja de color por jugador, con flechas. Posición deducida de la dirección de avance |
| `_dibujar_flecha(cx, cy, direccion)` | Triángulo que apunta según el vector. **Se reorienta solo** si cambias la dirección |
| `_dibujar_celdas()` | Damero de casillas redondeadas, alternando dos tonos |
| `_dibujar_rotulos()` | Números 1..n en el margen, en la numeración del enunciado |
| `_dibujar_marcadores_de_destino()` | Halo amarillo en la ficha seleccionada; círculo verde en destinos normales; **lila en las salidas** |
| `_dibujar_fichas()` | Recorre ambos jugadores |
| `_dibujar_ficha(casilla, colores)` | Sombra + círculo + brillo (efecto de relieve) |
| `_dibujar_cartel_final()` | Tarjeta central con el resultado y el motivo |

### 🖱️ Bloque D — Interacción

| Método | Qué hace |
|---|---|
| `_turno_es_humano()` | ¿La jugada actual le toca a una persona? (siempre `True` en tu modo) |
| `_al_hacer_clic(evento)` | Las 3 posibilidades del clic |
| `_al_mover_raton(evento)` | Cambia el cursor a manita sobre lo accionable |
| `_seleccionar(casilla)` | Fija la ficha activa y **filtra** sus destinos legales |
| `_jugar(movimiento)` | Aplica y apila |

**`_seleccionar` es la función que hay que enseñar** si preguntan por la
separación de capas:

```python
self._seleccion = casilla
self._destinos = {}
if casilla is not None:
    for movimiento in motor.movimientos_legales(self._estado):
        if movimiento.origen == casilla:
            self._destinos[movimiento.destino] = movimiento
self._dibujar()
```

> 💬 *"Los destinos **no se calculan aquí**: se **filtran** de la lista
> que devuelve el motor. La interfaz nunca decide qué es legal."*

### 🔘 Bloque E — Botones

| Método | Qué hace |
|---|---|
| `_deshacer()` | `pop()` de la pila de estados y del historial |
| `_reiniciar()` | `self._estados = self._estados[:1]` — vuelve al inicial |
| `_nuevo_tablero()` | Vuelve a la pantalla de configuración |

> 💬 **Sobre Deshacer:** *"Basta con descartar el último estado. Como
> `aplicar()` nunca modificó el anterior, sigue intacto en la pila. No
> hay que reconstruir nada ni invertir la jugada."*

*(Cuando hay bot, deshacer retrocede hasta el turno humano. En tu modo
retrocede exactamente una jugada.)*

### 🔄 Bloque F — Actualización del panel

`_refrescar()` sincroniza **todos** los widgets con el estado actual:
punto de color del turno, nombre del jugador, marcadores de fichas,
barras de progreso, historial, mensaje inferior y botón Deshacer. Al
final llama a `_dibujar()`.

`_dibujar_barra_progreso(...)` tiene un detalle curioso: si el widget
todavía no tiene ancho (Tk aún no calculó la geometría), **se reprograma
solo** con `after(50, ...)` para reintentarlo.

---

## 6.4 🪟 `class AplicacionDodgem(tk.Tk)`

La ventana principal. Solo alterna entre pantallas.

| Método | Qué hace |
|---|---|
| `__init__` | Título, tamaño, tamaño mínimo, elige tipografía |
| `_cambiar_pantalla(pantalla)` | Destruye la anterior y monta la nueva |
| `mostrar_configuracion()` | Monta `PantallaConfiguracion` |
| `iniciar_partida(n, modo, nivel)` | Monta `PantallaJuego` |
| `_al_cerrar()` | Cancela lo que haya en curso y destruye la ventana |

Y la función suelta al final:

```python
def lanzar(n_inicial=None, modo=None, nivel=None):
    aplicacion = AplicacionDodgem(n_inicial, modo, nivel)
    aplicacion.mainloop()
```

**`mainloop()`** es el bucle de eventos de Tkinter: se queda esperando
clics, teclas y repintados hasta que se cierra la ventana.

---

<a name="7"></a>
# 7. 🔌 Dónde termina lo tuyo y empieza lo de ellos

No necesitas dominar sus archivos, pero **sí saber dónde se enchufan**.
Si el profesor pregunta "¿y cómo se conecta esto con la IA?", esta es
tu respuesta:

```
Carlos (heuristica.py) usa de lo tuyo:
   · motor.fichas_de()                → dónde están las fichas
   · motor.dentro_del_tablero()       → si una casilla existe
   · motor.contar_movimientos_legales()  → movilidad
   · config.DIRECCION_AVANCE          → hacia dónde medir la distancia
   · motor.ganador()                  → si la partida acabó

Valentín (agente.py) usa de lo tuyo:
   · motor.movimientos_legales()      → qué ramas explorar
   · motor.aplicar(..., validar=False)→ bajar por una rama
   · motor.ganador()                  → cuándo parar
   · Estado como CLAVE de diccionario → su tabla de transposiciones

gui.py llama al agente solo cuando el turno no es humano.
```

🎯 **La frase que resume tu aporte a la Fase 2:**

> *"Cuando enchufamos el agente, `gui.py` no aprendió ni una regla
> nueva. Solo aprendió **a quién pedirle** la jugada, no **cómo**
> elegirla. Eso fue posible porque la frontera entre capas ya estaba
> puesta desde la primera entrega."*

Y el regalo concreto:

> *"El estado es inmutable y hashable porque lo diseñé así pensando en
> la Fase 2. Eso le dio a Valentín la tabla de transposiciones sin
> escribir ninguna función de hash."*

---

<a name="8"></a>
# 8. 🔥 Cambios en vivo, con guion

> ✅ Todos probados. **Practícalos esta noche con el código delante.**

## Antes de nada: cómo se hace un cambio en vivo

1. Abre `config.py`
2. Busca la constante (usa Ctrl+F)
3. Cámbiala
4. **Guarda** (Ctrl+S)
5. **Cierra la ventana del juego y vuelve a ejecutar** `python main.py`

⚠️ Python **no recarga** los módulos en caliente. Si cambias
`config.py` con el juego abierto, no pasa nada. Hay que reiniciar.

---

## 🎲 Cambio 1: "Que acepte tableros impares"

📍 `config.py`, sección 2

```python
# Opción A: solo impares
RESTO_PARIDAD_REQUERIDO = 1      # era 0

# Opción B (más elegante): pares E impares
DIVISOR_PARIDAD = 1              # era 2
```

**Qué decir:**

> *"La paridad no está escrita como `if n % 2 == 0`. Está expresada
> como un divisor y el resto exigido. Con el resto en 1 acepta impares.
> Y si pongo el divisor en 1, acepta cualquier tamaño mayor que 4,
> porque todo entero módulo 1 da cero."*

**Qué verás:** los botones de la pantalla de configuración cambian a
5, 7, 9, 11... **solos**, porque salen de `motor.tamanos_validos()`.

**Comprobación rápida por consola:**

```bash
python main.py --n 7 --diagnostico
```

Resultado real: 6 fichas por jugador, esquina inferior izquierda libre.

> 🎤 **Remate:** *"Y no toqué `motor.py` ni `gui.py`."*

---

## ↔️ Cambio 2: "Que A avance hacia la izquierda"

📍 `config.py`, sección 3

```python
DIRECCION_AVANCE = {
    JUGADOR_A: (0, -1),    # era (0, 1)
    JUGADOR_B: (-1, 0),
}
```

**Qué pasa solo, sin tocar nada más:**

| Componente | Cómo se adapta |
|---|---|
| Colocación inicial | `_linea_de_partida()` pone a A en la **columna derecha** |
| Esquina libre | Pasa a ser la inferior **derecha** |
| Movimientos legales | Cambia el vector de avance; los laterales siguen siendo verticales |
| Regla de salida | Sale por el borde **izquierdo** |
| Carril en la GUI | Se dibuja a la **izquierda**, con flechas al Oeste |
| Heurística de Carlos | Mide la distancia hacia el borde correcto |

> 💬 *"Ninguna función tiene escrito 'A va a la derecha'. Todas leen el
> vector de `config.py`."*

⚠️ **Aviso honesto:** si además cambias el avance de A a **vertical**
(ej. `(1, 0)`), tienes que cambiar también sus `DIRECCIONES_LATERALES`
a horizontales, porque los laterales deben ser **perpendiculares** al
avance. Si no, A tendría disponible el vector de retroceso. Dilo tú
antes de que lo descubran.

---

## 🏆 Cambio 3: "Cambie la condición de victoria"

📍 `config.py`, sección 5

```python
REGLA_BLOQUEO = BLOQUEADO_GANA     # era BLOQUEADO_PIERDE
```

**Qué decir:**

> *"Esta es la regla del Dodgem clásico: se penaliza a quien bloquea.
> Y fíjese que la pantalla de configuración **actualiza sola** el texto
> de las reglas, porque lo genera leyendo esta misma constante."*

🎯 **El extra que suma:**

> *"Y la heurística de mi compañero también se entera: lee esta
> constante e invierte el signo del término de inmovilización. Con la
> regla clásica, bloquear al rival sería perder, así que una heurística
> que siguiera premiando el bloqueo empujaría al agente hacia la
> derrota."*

**Variante — activar tablas:**

```python
TABLAS_HABILITADAS = True
LIMITE_JUGADAS_SIN_PROGRESO = 100
```

---

## 🔢 Cambio 4: "Que cada jugador tenga n−3 fichas"

📍 `config.py`, sección 2

```python
FICHAS_MENOS_QUE_LADO = 3      # era 1
```

**Resultado real con n=6:** 3 fichas por bando, en las casillas **más
lejanas a la esquina compartida**.

```
     1  2  3  4  5  6
 1   A  .  .  .  .  .
 2   A  .  .  .  .  .
 3   A  .  .  .  .  .
 4   .  .  .  .  .  .
 5   .  .  .  .  .  .
 6   .  .  .  B  B  B
```

> *"Se descartan las fichas más cercanas a la esquina compartida, que
> es donde los dos bandos se estorban desde la primera jugada. Y si se
> piden más fichas de las que caben en el borde, falla con un mensaje
> explícito en vez de romperse en silencio."*

---

## 📏 Cambio 5: "Quiero un tablero de 20×20"

```python
TAMANO_MAXIMO_TABLERO = 20
```

> *"El motor lo soporta sin problema; ese máximo es solo una cota de
> legibilidad de la interfaz, no una regla del juego."*

---

## 🔄 Cambio 6: "Que empiece el jugador B"

```python
JUGADOR_INICIAL = JUGADOR_B
```

---

## 🎨 Cambio 7: "Cámbieme los colores"

```python
PALETA["ficha_a"] = "#A8D5C2"      # A pasa a verde menta
PALETA["ficha_a_borde"] = "#7FB79A"
```

> *"Las claves de la paleta son nombres semánticos —`ficha_a`,
> `destino_normal`— y no colores. Por eso se puede cambiar el tema
> completo editando un solo diccionario."*

---

<a name="9"></a>
# 9. 🎯 Preguntas trampa

## Sobre el motor

| ❓ Pregunta | ✅ Respuesta |
|---|---|
| *"Muéstreme dónde impide que A vaya a la izquierda."* | *"No existe ese código. El vector `(0,-1)` no está en ninguna lista de A, así que nunca se genera. Es prohibir por omisión, no por validación."* |
| *"¿Dónde valida que no se salte sobre otra ficha?"* | *"`if destino in ocupadas: continue`. Y no hay lógica de salto porque solo se prueban vectores de **una** casilla."* |
| *"¿Qué pasa si llamo a `aplicar` con un movimiento ilegal?"* | *"Lanza `ValueError`, porque `VALIDAR_MOVIMIENTOS_AL_APLICAR` está en `True`. El buscador lo desactiva pasando `validar=False`."* |
| *"¿Cómo distingue si ganó por salida o por bloqueo?"* | *"`motivo_de_termino()`: si el ganador **no tiene fichas**, ganó por salida; si las tiene, ganó porque el rival se bloqueó. No guardo ningún dato extra, se deduce del estado."* |
| *"Su motor no tiene ninguna variable global. ¿Por qué?"* | *"Porque una variable global compartida haría imposible explorar partidas hipotéticas sin corromper la real. Toda la información viaja dentro del `Estado`."* |
| *"¿Esto funciona con dos partidas abiertas a la vez?"* | *"Sí. Cada `PantallaJuego` tiene su propia pila de estados y no hay estado global mutable."* |
| *"¿Por qué `movimientos_legales` devuelve tupla y no lista?"* | *"Porque es inmutable: ninguna capa superior puede alterar por accidente la lista de jugadas de una posición."* |

## Sobre la interfaz

| ❓ Pregunta | ✅ Respuesta |
|---|---|
| *"¿Cómo sabe la interfaz qué casillas resaltar?"* | *"No lo sabe: filtra la lista de `motor.movimientos_legales()` por la ficha seleccionada."* |
| *"¿Y si el motor tuviera un bug?"* | *"La interfaz mostraría jugadas equivocadas, porque confía en él. Por eso hay 98 pruebas unitarias sobre el motor."* |
| *"¿Cómo detecta el clic sobre el carril de salida?"* | *"El carril se dibuja en la columna n, que es exactamente la coordenada virtual del destino de una salida. No hay caso especial."* |
| *"¿Por qué repintan todo el tablero en cada jugada?"* | *"Más simple y menos propenso a errores. Con 16×16 como máximo, el coste es irrelevante."* |
| *"¿Por qué no usaron `tk.Button`?"* | *"Porque en macOS ignora el color de fondo y en Windows dibuja un relieve gris. Un `Frame` con un `Label` se ve igual en los tres sistemas."* |

## Sobre el diseño en general

| ❓ Pregunta | ✅ Respuesta |
|---|---|
| *"¿Por qué tanto archivo? Cabría en uno solo."* | *"Cabría, pero cada archivo tiene una responsabilidad y una sola razón para cambiar. Y se nota en la práctica: cuando añadimos la IA en la Fase 2, no tocamos ninguna regla."* |
| *"¿Qué es lo que más le costó?"* | Responde con verdad. Una buena: *"Decidir que el estado fuera inmutable. Al principio parece incómodo porque hay que crear objetos nuevos todo el rato, pero luego resolvió gratis el Deshacer y la tabla de transposiciones."* |
| *"Si tuviera que empezar de nuevo, ¿qué cambiaría?"* | *"Separaría antes la geometría del dibujo en la interfaz. Y mediría el rendimiento desde el principio, porque descubrimos tarde que `movimientos_legales` se llamaba de más."* |

---

<a name="10"></a>
# 10. 📖 Glosario

| Término | Qué significa |
|---|---|
| **Máquina de estados** | Sistema que en todo momento está en un estado concreto y pasa a otro según una entrada. Aquí: estado = posición del tablero; entrada = movimiento. |
| **Función pura** | Función que (a) con la misma entrada da siempre la misma salida y (b) no modifica nada fuera de ella. |
| **Inmutable** | Que no se puede modificar después de crearlo. Tuplas, `frozenset` y cadenas lo son; listas, `set` y diccionarios no. |
| **Hashable** | Que puede usarse como clave de diccionario. Requiere ser inmutable. |
| **`NamedTuple`** | Tupla cuyos campos tienen nombre. Inmutable y hashable. |
| **`frozenset`** | Conjunto inmutable. Búsqueda O(1). |
| **O(1) / O(n) / O(n²)** | Cómo crece el coste con el tamaño. O(1) = constante; O(n) = proporcional; O(n²) = al cuadrado. |
| **Número mágico** | Número suelto sin nombre en medio del código. Es lo que el enunciado prohíbe. |
| **Vector de dirección** | Par `(Δfila, Δcolumna)` que indica un desplazamiento. |
| **Invariante** | Condición que debe cumplirse siempre. Ej.: dos fichas nunca en la misma casilla. |
| **Canvas** | Widget de Tkinter para dibujar formas libres. |
| **`mainloop()`** | Bucle de eventos de Tkinter: espera clics y repintados. |
| **Widget** | Cualquier elemento de interfaz: botón, etiqueta, marco... |
| **Prueba unitaria** | Código que comprueba automáticamente que una función hace lo que debe. |

---

# ✅ Checklist para esta noche

- [ ] Poner `MODO_POR_DEFECTO = MODO_HUMANO_VS_HUMANO`
- [ ] Jugar **una partida completa** de principio a fin, hasta que gane alguien
- [ ] Provocar una victoria **por bloqueo** (arrincona una ficha) para ver el cartel
- [ ] Usar **Deshacer** cinco veces seguidas
- [ ] Ejecutar `python main.py --n 10 --diagnostico` y leer la salida
- [ ] Hacer los 7 cambios en vivo, **uno por uno**, y deshacerlos
- [ ] Ejecutar `python -m unittest pruebas_motor -v` y ver los 44 OK
- [ ] Ensayar el guion de demo de 3 minutos **en voz alta**, con cronómetro
- [ ] Repasar las 5 frases de abajo

# 💬 Tus 5 frases

1. 🏛️ *"La interfaz no sabe jugar al Dodgem. Si una jugada se resalta
   es porque el motor la devolvió."*
2. 🎯 *"Un destino fuera del tablero es legal solo si el vector era el
   de avance. Esa única condición implementa las dos reglas de salida."*
3. 🧊 *"El estado es inmutable, y por eso Deshacer es solo descartar el
   último de una pila: el anterior sigue intacto porque nadie lo tocó."*
4. 🧭 *"No escribí 'A empieza en la columna 0'. Escribí 'A empieza en el
   borde opuesto a su avance', y el código lo calcula."*
5. 🔌 *"Cuando enchufamos la IA, la interfaz no aprendió ni una regla
   nueva. Solo aprendió a quién pedirle la jugada."*

---

**¡Suerte mañana, Donovan! 🍀**

*Tu parte es la base sobre la que se apoya todo lo demás. Preséntala
con esa seguridad: sin motor no hay heurística, y sin heurística no hay
agente.*

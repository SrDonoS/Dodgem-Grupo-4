# 🎓 Guía de Defensa — Proyecto Dodgem

**Fundamentos de Inteligencia Artificial** · Documento de estudio y repaso
Para: **Donovan**, **Carlos** y **Valentín**

---

## ⚠️ Antes de empezar: léanlo los tres

Este documento explica **qué hace y por qué existe** cada función del
proyecto. Pero hay algo que ningún documento puede hacer por ustedes:

> 🔴 **No lo lean. Háganlo.** Esta noche, cada uno abra su archivo,
> ejecute los cambios en vivo de su sección con el código delante, y
> vea el resultado en pantalla. Si mañana es la primera vez que tocan
> `config.py`, se va a notar en tres segundos.

El profesor no evalúa si saben recitar. Evalúa si **entienden el
sistema que están defendiendo**. Y la señal más clara de que alguien
no lo entiende es que sabe *qué* hace el código pero no *por qué está
escrito así*.

### 🧭 Regla de oro para sobrevivir a cualquier pregunta

Si no saben algo, **no inventen**. Digan esto:

> *"No manejo ese detalle de memoria, pero está en `X.py`. La decisión
> de diseño detrás es Y, y puedo mostrárselo en el código."*

Eso demuestra que entienden la arquitectura aunque no recuerden una
línea. Inventar y equivocarse es infinitamente peor.

---

## 🏛️ La arquitectura en 60 segundos (los tres deben poder decir esto)

El proyecto tiene **tres capas que no se mezclan nunca**:

```
┌──────────────────────────────────────────────────────┐
│  gui.py  ·  main.py          ← PRESENTACIÓN          │
│  Dibuja y traduce clics. NO sabe jugar al Dodgem.    │
├──────────────────────────────────────────────────────┤
│  agente.py                   ← DECISIÓN (dinámica)   │
│  Minimax + Alfa-Beta. Busca en el árbol.             │
├──────────────────────────────────────────────────────┤
│  heuristica.py               ← DECISIÓN (estática)   │
│  Puntúa una posición. No busca, solo evalúa.         │
├──────────────────────────────────────────────────────┤
│  motor.py                    ← REGLAS                │
│  Máquina de estados PURA. Única fuente de verdad.    │
├──────────────────────────────────────────────────────┤
│  config.py                   ← PARÁMETROS            │
│  Todo lo modificable. Cero números mágicos.          │
└──────────────────────────────────────────────────────┘
```

**La frase que resume el diseño** (apréndansela los tres):

> *"Si una jugada aparece resaltada en la pantalla, es porque
> `motor.movimientos_legales()` la devolvió. La interfaz no sabe jugar
> al Dodgem."*

**El beneficio concreto:** cuando enchufamos el agente Minimax en la
Fase 2, `gui.py` no aprendió ni una regla nueva. Solo aprendió **a
quién pedirle** la jugada, no **cómo** elegirla.

### 📁 Mapa de archivos

| Archivo | Dueño | Qué es |
|---|---|---|
| `config.py` | Donovan | Todos los parámetros del sistema |
| `motor.py` | Donovan | Las 6 funciones de la máquina de estados |
| `gui.py` | Donovan | Interfaz Tkinter |
| `main.py` | Donovan | Punto de entrada + argumentos CLI |
| `heuristica.py` | Carlos | Función de evaluación h(n) |
| `agente.py` | Valentín | Minimax + Alfa-Beta + transposiciones |
| `pruebas_*.py` | cada uno | 98 pruebas unitarias |
| `banco_*.py` | Carlos / Valentín | Bancos de medición (no son entrega) |

> ⚠️ **Ojo Valentín:** el archivo se llama **`agente.py`** (singular),
> no `agentes.py`. Si lo nombras mal en la defensa, el profesor va a
> pensar que no lo has abierto.

### ▶️ Cómo se ejecuta

```bash
python main.py                                   # pantalla de configuración
python main.py --n 8 --modo humano_vs_agente --nivel dificil
python main.py --n 6 --diagnostico               # estado inicial en consola
python -m unittest pruebas_motor pruebas_heuristica pruebas_agente -v
```

💡 **`--diagnostico` es su salvavidas.** Imprime el tablero en texto
sin abrir la ventana. Si un cambio en vivo rompe la interfaz, pueden
demostrar que el **motor** funciona igual.

---

# 👤 SECCIÓN 1 — DONOVAN

## Motor, Configuración e Interfaz

**Tus archivos:** `motor.py`, `config.py`, `gui.py`, `main.py`
**Tu tema estrella:** la máquina de estados pura y la inmutabilidad.

---

## 1.1 🧊 Las estructuras de datos (esto es lo primero que te van a preguntar)

### `Estado` — la fotografía de la partida

```python
class Estado(NamedTuple):
    n: int                              # lado del tablero
    fichas_a: FrozenSet[Casilla]        # posiciones de A
    fichas_b: FrozenSet[Casilla]        # posiciones de B
    turno: str                          # "A" o "B"
    salidas_a: int                      # fichas de A ya fuera
    salidas_b: int                      # fichas de B ya fuera
    sin_progreso: int                   # jugadas sin que salga ninguna
```

**❓ "¿Por qué `NamedTuple` y no una clase normal?"**

Tres razones, en orden de importancia:

1. **Es inmutable.** Una vez creado, nadie puede modificarlo. Eso hace
   *imposible* el bug clásico de los buscadores: que una rama
   hipotética del árbol corrompa la partida real.
2. **Es hashable.** Como todos sus campos son inmutables (y los
   conjuntos son `frozenset`, no `set`), el estado completo puede
   usarse **como clave de un diccionario**. De ahí sale gratis la
   tabla de transposiciones de Valentín.
3. **Es legible.** `estado.turno` en vez de `estado[3]`.

**❓ "¿Por qué `frozenset` y no una matriz `n × n`?"**

Respuesta corta: **rendimiento en el árbol de búsqueda.**

| Operación | Con matriz | Con `frozenset` |
|---|---|---|
| ¿Casilla ocupada? | O(1) pero hay que construir la matriz | **O(1)** directo |
| Generar movimientos | O(n²) recorrer todo | **O(fichas)** = O(n) |
| Copiar el estado | O(n²) | O(fichas) |
| ¿Hashable? | ❌ No | ✅ Sí |

Con `n = 16` la matriz tiene 256 casillas pero solo hay 15 fichas por
bando. Recorrer 256 celdas para encontrar 15 fichas es tirar trabajo a
la basura — y Minimax hace eso *cientos de miles de veces*.

### `Movimiento` — una jugada

```python
class Movimiento(NamedTuple):
    origen: Casilla       # siempre dentro del tablero
    destino: Casilla      # ¡puede caer FUERA! (eso es una salida)
    tipo: str             # "avance" | "lateral" | "salida"
```

**❓ "¿Por qué el destino puede estar fuera del tablero?"**

Porque una salida es un movimiento con destino "virtual". Ficha de A
en `(2, 5)` con `n=6` → destino `(2, 6)`, que no existe. Conservar esa
coordenada tiene dos beneficios:

- La interfaz dibuja el carril de salida en `columna = n` y el destino
  cae **exactamente ahí**. Cero casos especiales para el clic.
- El historial es reconstruible: se sabe por dónde salió cada ficha.

### 🎯 Sistema de coordenadas (¡pregunta trampa clásica!)

```
INTERNO (motor):     (fila, columna) en base 0, fila 0 = ARRIBA
ENUNCIADO (humano):  fila 1 = arriba, columna n = derecha
```

**❓ "¿Por qué no usan la numeración del enunciado directamente?"**

Porque en base 0 no hay que sumar y restar 1 en cada cálculo del
árbol de búsqueda, y ahí es donde se cometen los errores. La
conversión ocurre **solo en el borde**, en
`motor.a_coordenada_humana()`, que traduce `(2, 0)` → `"f3c1"`.

---

## 1.2 🔧 Las 6 funciones exigidas — qué hace cada una y por qué

### 1️⃣ `validar_n(n) -> bool`

**Qué hace:** dice si un tamaño de tablero es aceptable.
**Por qué existe:** para que la regla "n par y mayor que 4" viva en
**un solo lugar** y no repartida por toda la interfaz.

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

🔍 **Detalle fino que impresiona:** el `isinstance(n, bool)` está ahí
porque en Python `True == 1` y `isinstance(True, int)` es `True`. Sin
esa guarda, `validar_n(True)` haría cosas raras.

**Funciones hermanas:**

| Función | Para qué |
|---|---|
| `motivo_invalidez(n)` | Devuelve el *mensaje en castellano* de por qué falló. Existe para que `validar_n` siga siendo un `bool` limpio y la lógica no se duplique. |
| `tamanos_validos()` | Lista todos los tamaños aceptados. **La interfaz genera sus botones con esto**, así que si cambias `config.py` los botones cambian solos. |

### 2️⃣ `estado_inicial(n) -> Estado`

**Qué hace:** construye la posición de apertura.
**Por qué es la función más elegante del proyecto:** porque **no
coloca las fichas a mano**.

```python
linea_a = _linea_de_partida(n, config.DIRECCION_AVANCE[JUGADOR_A])
linea_b = _linea_de_partida(n, config.DIRECCION_AVANCE[JUGADOR_B])
compartidas = set(linea_a) & set(linea_b)   # la esquina común
```

**La idea:** en Dodgem cada bando arranca pegado al borde **opuesto**
a su dirección de avance, para tener el tablero por delante. Entonces
`_linea_de_partida()` **deduce** ese borde del vector de avance
declarado en `config.py`.

La intersección de las dos líneas es exactamente **una** casilla: la
esquina inferior izquierda. Al descontarla, cada jugador queda con
`n − 1` fichas **sin contar nada a mano**.

> 💬 **Frase para la defensa:** *"No escribimos 'A empieza en la
> columna 0'. Escribimos 'A empieza en el borde opuesto a su avance', y
> el código lo calcula. Por eso si usted invierte la dirección de A en
> `config.py`, las fichas se recolocan solas."*

**Funciones auxiliares:**

- `_linea_de_partida(n, avance)` → devuelve la fila o columna completa
  del borde de partida. Si el avance es horizontal (`Δcolumna ≠ 0`),
  la línea es una **columna**; si es vertical, una **fila**.
- `_recortar_linea(casillas, cantidad, esquina, jugador)` → deja
  exactamente `fichas_por_jugador(n)` fichas. Si sobran casillas,
  descarta **las más cercanas a la esquina compartida**, que es donde
  los dos bandos se estorban desde la primera jugada.

🛡️ **Invariante de seguridad:** al final comprueba que
`fichas_a & fichas_b` esté vacío. Si una configuración exótica dejara
dos fichas encimadas, falla con un mensaje claro en vez de arrancar
una partida corrupta.

### 3️⃣ `movimientos_legales(estado) -> tuple[Movimiento, ...]`

**Qué hace:** todas las jugadas legales del jugador en turno.
**Por qué está escrita así:** porque **una sola condición implementa
las dos reglas de salida**.

```python
for origen in propias:
    for vector in (avance,) + laterales:
        destino = origen + vector
        if not dentro_del_tablero(destino, n):
            if vector == avance:              # ← ¡AQUÍ ESTÁ LA MAGIA!
                movimientos.append(Movimiento(origen, destino, SALIDA))
            continue
        if destino in ocupadas:
            continue                          # sin capturas ni saltos
        movimientos.append(Movimiento(origen, destino, tipo))
```

> 💬 **La joya de tu defensa:** *"Un destino fuera del tablero es legal
> **solo si el vector usado era el de avance**. Esa única condición
> implementa a la vez que A solo sale por la derecha y que B solo sale
> por arriba. Un intento de salir lateralmente usa un vector que no es
> el de avance, y se descarta sin necesidad de escribir una regla
> aparte."*

**❓ "¿Por qué devuelve una tupla y no una lista?"**
Porque es inmutable: ninguna capa superior puede alterar por accidente
la lista de jugadas de un nodo del árbol.

**❓ "¿Por qué las ordenan?"** Dos motivos:
1. **Determinismo:** la misma posición produce siempre la misma lista.
2. **Alfa-Beta:** el orden es `(salida, avance, lateral)` —
   `config.ORDEN_TIPOS_MOVIMIENTO`. Examinar primero las jugadas más
   prometedoras hace que la poda corte antes. *(Ese es el puente con
   la sección de Valentín.)*

**Hermanas de esta función** (existen por rendimiento):

| Función | Por qué existe |
|---|---|
| `hay_movimientos_legales(estado)` | Para detectar bloqueo basta encontrar **una** jugada. Construir y ordenar la lista entera es trabajo tirado. |
| `contar_movimientos_legales(estado, jugador)` | Cuenta sin crear objetos `Movimiento` ni ordenar. La usa la heurística de Carlos en cada hoja del árbol: **triplicó** las evaluaciones por segundo. |

### 4️⃣ `aplicar(estado, movimiento) -> Estado` ⭐ LA MÁS IMPORTANTE

**Qué hace:** devuelve un estado **NUEVO** con la jugada aplicada.
**Lo que NO hace:** tocar el estado original. Ni un byte.

```python
nuevas_fichas = set(fichas_de(estado, jugador))   # copia
nuevas_fichas.discard(movimiento.origen)
if movimiento.es_salida:
    salidas += 1
    sin_progreso = 0        # sacar una ficha SÍ es progreso
else:
    nuevas_fichas.add(movimiento.destino)
    sin_progreso += 1

return estado._replace(**campos)   # ← NO muta: devuelve tupla nueva
```

**❓ "¿Qué es `_replace`? El guion bajo sugiere que es privado."**

Es la **API oficial y documentada** de `NamedTuple`. El guion bajo está
para no chocar con nombres de campo del usuario, no porque sea
privado. **No muta**: construye una tupla nueva con los campos
indicados reemplazados.

**❓ "¿Y esto para qué sirve en la práctica?"** 🎯 *La respuesta que
demuestra que entiendes el proyecto completo:*

> *"Minimax explora miles de partidas hipotéticas. Con estado mutable
> tendrías que aplicar la jugada, bajar en la recursión y luego
> **deshacerla** al volver — el patrón do/undo, que es donde se cometen
> los errores más difíciles de encontrar. Como `aplicar()` es pura, el
> padre simplemente pasa el hijo a la llamada recursiva y sigue
> intacto. Cero bugs por mutación accidental. Y el botón Deshacer de la
> interfaz es una pila de estados: no reconstruye nada, solo descarta
> el último."*

🔍 **Parámetro `validar`:** `aplicar(estado, mov, validar=False)`. El
buscador lo pasa en `False` porque solo aplica movimientos que él mismo
sacó de `movimientos_legales()`. Revalidar regeneraría la lista entera
en **cada nodo del árbol**. Se pasa por argumento y no cambiando la
constante global para no crear una **condición de carrera**: el agente
busca en otro hilo mientras la interfaz usa el motor.

### 5️⃣ y 6️⃣ `es_terminal(estado)` y `ganador(estado)`

```python
def ganador(estado):
    if not estado.fichas_a: return JUGADOR_A     # 1. victoria por salida
    if not estado.fichas_b: return JUGADOR_B
    if config.TABLAS_HABILITADAS:                # 2. tablas (opcional)
        if estado.sin_progreso >= LIMITE: return EMPATE
    if not hay_movimientos_legales(estado):      # 3. bloqueo
        if config.REGLA_BLOQUEO == BLOQUEADO_PIERDE:
            return oponente(estado.turno)
        return estado.turno
    return None

def es_terminal(estado):
    return ganador(estado) is not None
```

**❓ "¿Por qué ese orden de comprobaciones?"**
1. Victoria por salida: es la **más barata** (dos conjuntos vacíos) y
   la de mayor prioridad.
2. Tablas: un simple contador.
3. Bloqueo: la **más costosa**, porque hay que generar movimientos.

**❓ "¿Por qué `es_terminal` está definida en función de `ganador`?"**
Para que no puedan **desincronizarse**. Existe una sola definición de
"fin de partida" y vive en `ganador()`.

> ⚠️ **Trampa que el profesor puede tender:** *"El Dodgem clásico dice
> que el jugador bloqueado GANA, porque se penaliza a quien bloquea.
> Ustedes lo tienen al revés."*
>
> **Respuesta:** *"Correcto, y es deliberado: el enunciado de la
> asignatura pide que el bloqueado pierda. Implementamos las dos
> convenciones y se elige con `config.REGLA_BLOQUEO`. Se lo cambio
> ahora mismo si quiere."* 💪 (Esto te da puntos, no te los quita.)

---

## 1.3 🖥️ La interfaz (`gui.py`) — lo que debes saber

No necesitas dominar cada píxel, pero sí estas cuatro ideas:

**1. Separación estricta.** `gui.py` no reimplementa ninguna regla.
Los destinos resaltados se **filtran** de lo que devuelve
`motor.movimientos_legales()`.

**2. La rejilla es más grande que el tablero.** Se dibujan filas y
columnas extra para los carriles de salida. La coordenada virtual de
una salida — `(fila, n)` para A — cae **exactamente** sobre su carril,
así que el clic funciona sin ningún caso especial.

Y las posiciones de los carriles **se deducen** de
`config.DIRECCION_AVANCE` mediante `_carriles_de_salida()`. Si
inviertes la dirección de A, su carril se muda solo al borde correcto.

**3. El bot piensa en otro hilo.** Si Minimax corriera en el hilo de
Tkinter, la ventana dejaría de repintarse y el sistema la marcaría
como "no responde". El agente corre en un `threading.Thread`, deja el
resultado en una `queue.Queue`, y el hilo de la interfaz la consulta
cada 50 ms con `after()`.

> 💬 **Regla de oro que puedes citar:** *"Solo el hilo de Tkinter toca
> widgets. El hilo trabajador únicamente pone una tupla en la cola. Y
> trabajar sobre el estado desde otro hilo es seguro sin copiar ni
> bloquear nada **precisamente porque el motor es puro**."*

**4. Detalles que evitan bugs reales:**

| Mecanismo | Qué problema evita |
|---|---|
| Contador de **generación** | Si reinicias mientras el bot piensa, su resultado llega tarde y se **descarta**. Sin esto aplicaría una jugada de una partida que ya no existe. |
| `threading.Event` de cancelación | Se consulta cada 2048 nodos: la búsqueda aborta pronto en vez de seguir gastando CPU. |
| Tablero en solo lectura | Durante el turno del bot los clics no hacen nada. |
| **Deshacer retrocede hasta tu turno** | Deshacer una sola jugada devolvería el turno al bot, que la repetiría al instante (es determinista) y el botón parecería roto. |

---

## 1.4 🔥 CAMBIOS EN VIVO — Tu guion paso a paso

> ✅ **Los cuatro siguientes están probados y funcionan.** Yo los
> ejecuté. Practícalos igual esta noche.

### 🎲 Cambio 1: "Que acepte tableros impares"

**Archivo:** `config.py`, sección 2.

```python
# ANTES
RESTO_PARIDAD_REQUERIDO = 0     # n % 2 == 0  → solo pares

# DESPUÉS (opción A: solo impares)
RESTO_PARIDAD_REQUERIDO = 1     # n % 2 == 1  → solo impares
```

```python
# DESPUÉS (opción B: pares E impares, más elegante)
DIVISOR_PARIDAD = 1             # n % 1 == 0 siempre → cualquier n > 4
```

**Qué decir mientras lo haces:**

> *"La paridad no está escrita como `if n % 2 == 0`. Está expresada
> como dos constantes: un divisor y el resto exigido. Con
> `RESTO_PARIDAD_REQUERIDO = 1` acepta impares; con
> `DIVISOR_PARIDAD = 1` acepta cualquier tamaño, porque todo entero
> módulo 1 da cero."*

**Resultado real con `n = 7`:** 6 fichas por jugador, esquina inferior
izquierda libre, todo funciona. Los botones de la pantalla de
configuración **se regeneran solos** porque salen de
`motor.tamanos_validos()`.

> 🎤 **Remate:** *"Y no toqué `motor.py` ni `gui.py`."*

### ↔️ Cambio 2: "Que A avance hacia la izquierda"

**Archivo:** `config.py`, sección 3.

```python
DIRECCION_AVANCE = {
    JUGADOR_A: (0, -1),    # ← era (0, 1). Ahora avanza al Oeste
    JUGADOR_B: (-1, 0),
}
```

**Lo que pasa automáticamente** (esto es lo que hay que explicar):

| Componente | Cómo se adapta |
|---|---|
| Colocación inicial | `_linea_de_partida()` pone a A en la **columna derecha** |
| Esquina libre | Se recalcula: ahora es la inferior **derecha** |
| Movimientos legales | El vector de avance cambia, los laterales siguen siendo verticales |
| Regla de salida | Sale por el borde **izquierdo**, sin tocar código |
| Heurística de Carlos | `_eje_de_salida()` mide la distancia hacia el borde correcto |
| **Carril en la GUI** | Se dibuja a la **izquierda**, con las flechas apuntando al Oeste |

> 💬 *"Ninguna función tiene escrito 'A va a la derecha'. Todas leen el
> vector de `config.py`. Cambiar ese vector reconfigura el juego
> entero, incluida la interfaz."*

⚠️ **Detalle honesto:** si además cambias el avance de A a **vertical**
(por ejemplo `(1, 0)`), tienes que cambiar también sus
`DIRECCIONES_LATERALES` a horizontales — porque los laterales deben ser
**perpendiculares** al avance. Si no, A tendría el vector de retroceso
disponible. Si el profesor lo pide, cambia **los dos** diccionarios.

### 🏆 Cambio 3: "Cambia la condición de victoria"

**Archivo:** `config.py`, sección 5.

```python
# ANTES (enunciado): quedarse sin jugadas = perder
REGLA_BLOQUEO = BLOQUEADO_PIERDE

# DESPUÉS (Dodgem clásico): quedarse sin jugadas = ganar
REGLA_BLOQUEO = BLOQUEADO_GANA
```

**Qué decir:**

> *"Y lo importante: la heurística **también** se entera. En
> `heuristica.py`, `_signo_del_termino_de_inmovilidad()` lee esta misma
> constante y **invierte el signo** del término de inmovilización. Con
> la regla clásica, bloquear al rival sería perder, así que una
> heurística que siguiera premiando el bloqueo empujaría al agente
> justo hacia la derrota."*

🎤 Eso demuestra que pensaron el sistema como un todo. Es la respuesta
que separa un 5 de un 7.

**Activar tablas** (otra variante de condición de término):

```python
TABLAS_HABILITADAS = True
LIMITE_JUGADAS_SIN_PROGRESO = 100
```

### 🔢 Cambio 4: "Que cada jugador tenga n−3 fichas"

**Archivo:** `config.py`, sección 2.

```python
FICHAS_MENOS_QUE_LADO = 3      # era 1
```

**Resultado real con `n = 6`:** 3 fichas por bando, colocadas en las
casillas **más lejanas a la esquina compartida** (filas 1, 2 y 3 para
A). Si pides más fichas de las que caben en el borde, el código falla
con un mensaje explícito en vez de romperse en silencio.

### 📏 Cambio 5: "Quiero un tablero de 20×20"

```python
TAMANO_MAXIMO_TABLERO = 20
```

⚠️ Avisa: *"El motor lo soporta sin problema. La interfaz también, pero
el bot en nivel difícil puede tardar; para eso está el tope de tiempo
de seguridad."*

### 🔄 Cambio 6: "Que empiece el jugador B"

```python
JUGADOR_INICIAL = JUGADOR_B
```

---

## 1.5 🎯 Preguntas trampa para Donovan

| ❓ Pregunta | ✅ Respuesta |
|---|---|
| *"¿Dónde está el código que dice que A no puede ir a la izquierda?"* | **No existe tal código.** `DIRECCIONES_LATERALES[A]` solo contiene los vectores verticales, y el de avance es el horizontal positivo. El vector de retroceso simplemente **no está en ninguna lista**, así que nunca se genera. |
| *"Muéstreme dónde valida que la ficha no salte sobre otra."* | En `movimientos_legales`: `if destino in ocupadas: continue`. No hay lógica de salto porque solo se prueban vectores de **una casilla**. |
| *"¿Qué pasa si llamo a `aplicar` con un movimiento ilegal?"* | Lanza `ValueError`, porque `VALIDAR_MOVIMIENTOS_AL_APLICAR` está en `True`. El buscador lo desactiva pasando `validar=False`. |
| *"¿Cómo sabe el juego que terminó por bloqueo y no por salida?"* | `motivo_de_termino()` lo distingue: si el ganador **no tiene fichas**, ganó por salida; si las tiene, ganó por bloqueo del rival. |
| *"¿Por qué el historial no está dentro del `Estado`?"* | Porque Minimax no lo necesita y arrastrarlo **multiplicaría la memoria del árbol**. El historial es responsabilidad de la interfaz. |
| *"¿Esto funciona si dos personas juegan a la vez en dos ventanas?"* | Sí. No hay estado global mutable: cada `PantallaJuego` tiene su propia pila de estados. |

---

# 👤 SECCIÓN 2 — CARLOS

## Heurística y Pathfinding

**Tus archivos:** `heuristica.py`, `banco_heuristica.py`
**Tu tema estrella:** la distancia Manhattan degenerada y por qué es
admisible.

---

## 2.1 🧠 Empecemos por cero: ¿qué es una heurística?

Imagina que Minimax es un explorador que mira jugadas futuras. En
algún momento **tiene que parar** (no puede mirar hasta el final de la
partida, sería astronómico). Cuando para, se encuentra con una
posición a medias y necesita responder: **"¿esto pinta bien o mal?"**

Esa respuesta es la heurística. Es una función que mira un tablero y
devuelve **un número**:

- **Positivo** → la posición favorece a mi jugador
- **Negativo** → favorece al rival
- **Cero** → equilibrada

🎯 **Tu frase de apertura en la defensa:**

> *"La heurística es el cerebro **estático**: no explora nada, solo
> mira una foto del tablero y la puntúa. La búsqueda es el cerebro
> **dinámico**. Sin heurística, Minimax no sabría qué prefiere."*

---

## 2.2 🏁 La idea central: Dodgem es una CARRERA de dos pathfindings

**Pathfinding** = búsqueda de camino. Es el problema de "estoy aquí,
quiero llegar allá, ¿cuánto me falta?".

En Dodgem, **cada ficha resuelve su propio problema de camino**: parte
de su casilla y quiere alcanzar su carril de salida. La partida
completa es la **superposición de dos de esos problemas** que compiten
por las mismas casillas.

De ahí salen los **dos bloques** de la fórmula:

```
🏃 PROGRESO      → ¿cuánto me falta para terminar mi ruta?
🚧 RESTRICCIÓN   → ¿cuánto le estoy estorbando yo a él?
```

---

## 2.3 📐 La distancia Manhattan degenerada ⭐ TU TEMA ESTRELLA

### Primero: ¿qué es la distancia Manhattan?

Es la distancia caminando por calles en cuadrícula (como Manhattan, la
isla): **no puedes ir en diagonal**.

```
d((f₁,c₁), (f₂,c₂)) = |f₁ − f₂| + |c₁ − c₂|
```

### Ahora el detalle que hay que entender bien

**La meta de una ficha NO es una casilla. Es un CONJUNTO de casillas.**

Para el jugador A (avanza al Este) la meta es *cualquier* casilla
virtual pasado el borde derecho: `{(f, n) : 0 ≤ f < n}`.

Y la distancia Manhattan **a un conjunto** es el mínimo de las
distancias a sus elementos:

```
h(f, c) = mín  |f − f'| + |n − c|
          f'
```

El mínimo se alcanza en `f' = f` (¡la misma fila!), donde el primer
término vale cero. Por lo tanto:

```
                    h(f, c) = n − c
```

### 🚨 La pregunta que te van a hacer

**❓ "Pero eso solo usa una coordenada. ¿Eso es Manhattan?"**

> ✅ **Tu respuesta:** *"Sí, y es el resultado **exacto** de aplicar la
> definición. La distancia Manhattan a un conjunto es el mínimo a sus
> elementos, y como la meta es una **línea completa** y no un punto, la
> componente perpendicular se anula sola: el mínimo está en la misma
> fila. No es una simplificación que hicimos nosotros — es lo que
> **da** la fórmula. Para B pasa lo simétrico: h = f + 1."*

📌 Esa respuesta vale oro. Muchos grupos usan "solo la columna" sin
saber justificarlo.

### 🧮 Las tres propiedades (¡demostrables en dos líneas cada una!)

**1. Es ADMISIBLE** (nunca sobreestima: `h ≤ h*`)

> Considera el **problema relajado**: quita todas las demás fichas del
> tablero. Una ficha a distancia `d` necesita entonces **exactamente**
> `d` movimientos, porque cada avance descuenta 1. Como los obstáculos
> solo pueden obligar a rodear —nunca a acortar— en el problema real
> hace falta al menos `d`. Luego `h ≤ h*`. ∎

🔬 **Y no lo afirmamos: lo verificamos.** En `pruebas_heuristica.py`,
`test_es_exacta_en_el_problema_relajado` calcula el óptimo con una
**búsqueda en anchura (BFS)** independiente y comprueba que coincide
con la fórmula para **todas** las casillas del tablero.

**2. Es CONSISTENTE** (cumple la desigualdad triangular de A*)

> Un movimiento legal cambia **una** coordenada en **una** unidad,
> luego `|h(s) − h(s')| ≤ 1`, que es exactamente el coste de un
> movimiento. Por lo tanto `h(s) ≤ c(s,s') + h(s')`. ∎

**3. `D(J) = Σh` es COTA INFERIOR de los turnos que faltan** ⭐

> Cada turno de J mueve **una** ficha **una** casilla. Un avance (o
> salida) baja `D` en exactamente 1; un lateral la deja **igual**,
> porque el eje lateral es **perpendicular** al eje de salida. Por
> tanto cada turno reduce `D` en **como máximo 1**, y para llegar a
> cero hacen falta **al menos** `D(J)` turnos. ∎

🎯 Esta es la propiedad que **da sentido a restar las distancias de los
dos jugadores**: estás comparando dos cotas inferiores de "turnos que
me faltan" contra "turnos que le faltan". Es una **carrera**.

🔬 También verificado: `test_cada_turno_reduce_la_distancia_total_a_lo_sumo_en_uno`
comprueba jugada a jugada, en partidas reales, que un avance descuenta
exactamente 1 y un lateral exactamente 0.

---

## 2.4 🔍 Función por función: qué hace y por qué existe

### `_eje_de_salida(jugador) -> (eje, sentido)`

**Qué hace:** dice si el jugador avanza por filas (eje 0) o columnas
(eje 1), y en qué sentido (+1 o −1).
**Por qué existe:** para **deducir** la orientación de
`config.DIRECCION_AVANCE` en vez de escribirla a mano. Si Donovan
invierte la dirección de A, tu heurística mide hacia el carril
correcto sin que toques nada.

### `distancia_a_la_salida(casilla, n, jugador) -> int`

```python
eje, sentido = _eje_de_salida(jugador)
coordenada = casilla[eje]
if sentido > 0:
    return n - coordenada          # meta pasado el índice n-1
return coordenada + 1              # meta pasado el índice 0
```

📊 **Ejemplo con n=6, jugador A:**

| Posición | Distancia | Por qué |
|---|---|---|
| columna 0 | **6** | 5 avances hasta la columna 5, + 1 para cruzar el borde |
| columna 3 | **3** | |
| columna 5 | **1** | solo le falta el movimiento de salida |

> ⚠️ Una ficha en el tablero **nunca** vale 0: siempre le falta al
> menos el movimiento de salida.

### `distancia_total(estado, jugador) -> int`

Suma las distancias de todas las fichas **vivas**. Las que ya salieron
no están en el conjunto, así que aportan 0 de forma natural. **Es la
cota inferior de turnos** que demostraste arriba.

### `_clasificar_bloqueo(...) -> (por_rival, por_propia, inmovilizada)`

**Qué hace:** analiza el estorbo que sufre **una** ficha.

**Criterio:** una ficha está bloqueada si la casilla **justo delante**
—en su dirección de avance— está ocupada.

**❓ "¿Por qué solo mira al frente y no los lados?"**

> *"Porque es el único estorbo que **retrasa el descuento de su
> distancia Manhattan**. Los movimientos laterales no acercan la ficha
> a la meta, así que tener un lateral tapado no cuesta progreso."*

🔑 **Caso especial importante:** si el avance cae **fuera** del
tablero, la ficha está en su carril de salida y **puede irse siempre**.
Nunca cuenta como bloqueada, porque ninguna ficha rival puede ocupar
una casilla que no existe.

🔑 **Las penalizaciones son ACUMULATIVAS:** una ficha inmovilizada
también cuenta como bloqueada de frente, así que suma
`W_BLOQUEO_RIVAL + W_INMOVILIZADA = 6 + 4 = 10`. Por eso siempre pesa
más que un bloqueo simple, aunque el número de `W_INMOVILIZADA` sea
menor.

### `extraer_rasgos(estado, jugador) -> Rasgos`

**Qué hace:** calcula de **una sola pasada** todas las medidas.

```python
class Rasgos(NamedTuple):
    distancia_total: int
    fichas_fuera: int
    bloqueadas_por_rival: int
    bloqueadas_por_propias: int
    inmovilizadas: int
    movilidad: int
```

**❓ "¿Por qué separan los rasgos del cálculo del puntaje?"** 🎯

> *"Porque los rasgos son **hechos** del tablero —cuántos pasos faltan,
> cuántas fichas están tapadas— y los pesos son **opiniones** sobre su
> importancia. Poder mostrar los hechos por separado es lo que permite
> defender la fórmula y ajustarla sin reescribir nada."*

### `heuristica_dodgem(estado, jugador_max) -> float` ⭐ LA PRINCIPAL

```
H = W_DISTANCIA      · (D_min  − D_max)     ← ¡INVERTIDA!
  + W_SALIDA         · (F_max  − F_min)
  + W_BLOQUEO_RIVAL  · (BR_min − BR_max)
  + W_BLOQUEO_PROPIO · (BP_min − BP_max)
  + s · W_INMOVILIZADA · (I_min − I_max)
  + W_MOVILIDAD      · (M_max  − M_min)
  + W_TEMPO          · (+1 si muevo yo, −1 si mueve él)
```

> ⚠️ **El error más fácil de cometer, y te lo pueden preguntar:** la
> distancia entra **invertida** (`D_min − D_max`). En pathfinding
> **menos** distancia es mejor; en una función de evaluación **más**
> puntaje es mejor. Hay que restar al revés.

**❓ "¿Por qué todo son diferencias?"**
Porque así la función es **antisimétrica** por construcción:
`H(s, A) = −H(s, B)`. Es condición necesaria para usarla en un Minimax
de suma cero. *(Verificado en `test_es_antisimetrica`.)*

### `_signo_del_termino_de_inmovilidad() -> float`

Devuelve `+1` con `BLOQUEADO_PIERDE` y `−1` con `BLOQUEADO_GANA`.

> 💬 *"Con la regla del enunciado, dejar al rival sin jugadas es
> **ganar**, así que inmovilizarlo suma. Con la regla clásica es
> **perder**, así que resta. Una heurística que no siguiera a la regla
> activa empujaría al agente justo hacia la derrota."*

### `evaluar(estado, jugador_max, profundidad, resultado)`

**Qué hace:** el valor de un nodo del árbol = **f(n) = g(n) + h(n)**.

```python
if resultado is None:              # partida en curso
    return heuristica_dodgem(estado, jugador_max)      # ← h(n)
if resultado == EMPATE:  return VALOR_EMPATE
if resultado == jugador_max:  return VICTORIA - profundidad   # ← g(n)
return -VICTORIA + profundidad
```

🎯 **El descuento por profundidad:** ganar en la jugada 3 vale
`VICTORIA − 3`; ganar en la jugada 7 vale `VICTORIA − 7`, que es
**menos**. Así el agente prefiere la victoria **más rápida** y la
derrota **más lenta**. Sin eso, todas las victorias valdrían igual y
el agente daría rodeos absurdos teniendo el remate disponible.

### `cota_maxima_heuristica(n) -> float`

**Por qué existe:** garantiza que `config.VICTORIA` (1 000 000) sea
**estrictamente mayor** que cualquier puntaje heurístico posible
(444,5 para n=16). Sin esa garantía, Minimax podría preferir una
posición "bonita" antes que un final ganado.

### `desglosar()` y `explicar()` — tus herramientas de defensa 🎤

`explicar()` imprime una tabla con el aporte de cada término:

```
TERMINO                     APORTE   DETALLE
Distancia a la salida         -1.0   me faltan 28 pasos, a el 27
Atascos propios               +1.0   mios 0, suyos 1
Movilidad                     +0.5   10 jugadas contra 9
Tempo                         -0.5   mueve Jugador B
--------------------------------------------------------------
TOTAL                         +0.0   (1 punto = 1 paso de avance)
```

> 💬 *"No mostramos un número mágico. Mostramos de dónde sale cada
> punto."* Y una prueba verifica que **el desglose suma el total**.

---

## 2.5 ⚖️ Los pesos: los MEDIMOS, no los adivinamos ⭐ TU MEJOR CARTA

| Peso | Valor | Justificación |
|---|---|---|
| `W_DISTANCIA` | **1.0** | Ancla de la escala: **1 punto = 1 paso** |
| `W_SALIDA` | **2.0** | Progreso irreversible (no puede volver a bloquearse) |
| `W_BLOQUEO_RIVAL` | **6.0** | Estimado 3.0 → **medido 6.0** |
| `W_BLOQUEO_PROPIO` | **1.0** | Atasco autoinfligido, se deshace solo |
| `W_INMOVILIZADA` | **4.0** | Estimado 8.0 → **medido 4.0** |
| `W_MOVILIDAD` | **0.2** | Estimado 0.5 → **medido 0.2** |
| `W_TEMPO` | **0.5** | En una carrera, tener el turno vale ≤ 1 paso |

**El método:** primero propusimos cada peso con un **argumento
analítico**, después medimos enfrentando variantes (120 partidas por
combinación, dos tamaños de tablero). **Donde el dato contradijo la
estimación, conservamos el dato.**

Ejemplo concreto que puedes contar:

> *"Para `W_BLOQUEO_RIVAL` razonamos que una ficha bloqueada de frente
> necesita un lateral para esquivar y otro para retomar la línea: ≥ 2
> pasos perdidos, así que propusimos 3. Al medirlo, 6 jugaba claramente
> mejor. La interpretación es que el bloqueo no cuesta solo el rodeo
> puntual: el rival puede **sostenerlo**. Conservamos el 6 medido."*

📊 **Con los pesos estimados** el agente empataba con una versión de
solo distancia (47%). **Con los medidos** gana **71%**.

### 🔬 Evidencia (tablero 6×6)

| Medición | Resultado |
|---|---|
| Coste por evaluación | **15,7 µs** (n=6) · 41 µs (n=16) ≈ **64 000/s** |
| Contra jugador aleatorio, prof. 1 | **97%** [IC95: 92–100] |
| Contra aleatorio, prof. 2 y 3 | **100%** |
| Contra "solo distancia", prof. 1 | **75%** [IC95: 67–83] |
| Contra "solo distancia", prof. 2 | **71%** [IC95: 63–79] |

🎯 **El segundo experimento es el que justifica el bloque de
restricción:** a profundidad 1 **no hay búsqueda que compense**, así
que mide la evaluación y no el árbol. Los intervalos excluyen el 50%,
o sea que la diferencia **no es ruido**.

> ⚠️ **Advertencia metodológica que debes mencionar tú mismo** (suma
> muchísimo): *"Dos agentes deterministas producen siempre la misma
> partida, así que '80 partidas' serían 2 repetidas 40 veces. Por eso
> el banco desempata **al azar** entre jugadas de igual valor, y por
> eso no poda con alfa en la raíz: podar ahí devolvería cotas en lugar
> de valores exactos y el conjunto de empatados quedaría mal
> identificado."*

---

## 2.6 🔥 CAMBIOS EN VIVO — Tu guion paso a paso

### 🚧 Cambio 1: "Que priorice los bloqueos por encima de la distancia"

**Archivo:** `config.py`, sección 8.

```python
# ANTES
W_DISTANCIA = 1.0
W_BLOQUEO_RIVAL = 6.0
W_INMOVILIZADA = 4.0

# DESPUÉS — el bloqueo domina claramente
W_DISTANCIA = 1.0        # se deja como ancla de la escala
W_BLOQUEO_RIVAL = 20.0   # un bloqueo vale 20 pasos de avance
W_INMOVILIZADA = 30.0
```

**Cómo explicar el impacto** (esto es lo que te van a pedir):

> *"Como todos los pesos están en la misma unidad —pasos de avance—,
> subir `W_BLOQUEO_RIVAL` a 20 significa literalmente: **bloquear una
> ficha del rival vale lo mismo que avanzar 20 casillas**. El agente
> dejará de correr hacia su salida y se dedicará a estorbar."*

**Cómo DEMOSTRARLO** con `explicar()`:

```python
python3 -c "
import config, motor, heuristica
config.W_BLOQUEO_RIVAL = 20.0
e = motor.estado_inicial(6)
print(heuristica.explicar(e, 'A'))"
```

La línea *"Tapadas por el rival"* multiplicará su aporte por ~3,3, y el
TOTAL se moverá en consecuencia. **Muestra el antes y el después.**

> ⚠️ **Aviso que te da credibilidad:** *"Lo medimos y jugar así es
> **peor**: un `W_INMOVILIZADA` alto hace que el agente persiga
> bloqueos totales, que son raros, descuidando su propia carrera. Por
> eso lo bajamos de 8 a 4. Puedo cambiarlo si quiere, pero el dato dice
> que empeora."* 💪

### 🎚️ Cambio 2: "Que ignore la distancia por completo"

```python
W_DISTANCIA = 0.0
```

> *"El agente pierde la noción de carrera. En nuestro banco, la versión
> de solo distancia pierde 71-29 contra la completa, pero la versión
> **sin** distancia es mucho peor: sin el término de pathfinding no
> tiene ninguna razón para avanzar."*

### 🔄 Cambio 3: "Invierta el criterio: que prefiera ir despacio"

```python
W_DISTANCIA = -1.0
```

> *"Ahora el agente **huye** de su salida. Es una buena forma de
> comprobar que el signo del término es el que decimos: se puede ver en
> pantalla cómo las fichas retroceden lateralmente."*

### ⏱️ Cambio 4: "Quite el tempo"

```python
W_TEMPO = 0.0
```

> *"Con el tempo en cero, `heuristica_dodgem` sobre la posición inicial
> devuelve **exactamente 0.0**, porque la apertura del Dodgem es
> perfectamente simétrica. Con el tempo en 0.5 devuelve **+0.5**: la
> única ventaja de A es tener el turno. Tenemos una prueba unitaria
> para cada uno de esos dos casos."*

🎤 Ese dato —que la apertura vale exactamente el peso del tempo— es
elegantísimo. Úsalo.

---

## 2.7 🎯 Preguntas trampa para Carlos

| ❓ Pregunta | ✅ Respuesta |
|---|---|
| *"¿Su heurística es admisible? ¿Eso importa en Minimax?"* | *"La **componente de distancia** es admisible y consistente, y lo demostramos. Pero cuidado: la admisibilidad es un requisito de **A\***, no de una función de evaluación de juegos. En Minimax lo que importa es que **ordene bien** las posiciones. La admisibilidad la mencionamos porque justifica que la distancia es una medida **correcta** de lo que falta, no porque Minimax la exija."* ⭐ |
| *"¿Por qué suman las distancias de todas las fichas?"* | Porque cada turno reduce esa suma en **como máximo 1**, luego es una cota inferior del número de turnos que faltan. |
| *"¿Qué pasa si una ficha ya salió?"* | No está en el `frozenset`, así que aporta 0 automáticamente. Sin casos especiales. |
| *"Su función llama a `movimientos_legales`. ¿No es carísimo?"* | *"Lo era. Medimos 30,6 µs por evaluación. Cambiamos a `motor.contar_movimientos_legales()`, que no construye objetos ni ordena, y bajó a 15,7 µs: **3,5× más rápido**. Y hay una prueba que verifica que el contador rápido da lo mismo que la lista completa."* |
| *"¿Cómo sé que sus pesos no son arbitrarios?"* | *"Ejecute `python banco_heuristica.py`. Está el barrido completo con intervalos de confianza."* |
| *"¿Por qué `W_INMOVILIZADA` (4) es menor que `W_BLOQUEO_RIVAL` (6)? ¿No es peor estar inmovilizado?"* | ⭐ *"Sí, y lo es: las penalizaciones son **acumulativas**. Una ficha inmovilizada por el rival también cuenta como bloqueada de frente, así que suma 6 + 4 = 10."* |

---

# 👤 SECCIÓN 3 — VALENTÍN

## El Agente: Minimax con Poda Alfa-Beta

**Tu archivo:** `agente.py` ⚠️ *(singular, no `agentes.py`)*
**Tu tema estrella:** por qué la poda no cambia el resultado, y por qué
el orden de los movimientos lo es todo.

---

## 3.1 🧠 Empecemos por cero: ¿qué es Minimax?

Imagina que juegas al ajedrez y piensas: *"si muevo aquí, él movería
allá, y entonces yo…"*. Eso es Minimax. Formalizado:

- Hay **dos jugadores con intereses opuestos**.
- Tú (**MAX**) quieres el puntaje **más alto** posible.
- Él (**MIN**) quiere el **más bajo**.
- Supones que el rival **juega lo mejor que puede** (pesimismo
  racional: si funciona contra el mejor rival, funciona contra
  cualquiera).

```
                  MAX (mi turno)  → elige el MÁXIMO
                 /       |       \
            MIN        MIN        MIN   → cada uno elige el MÍNIMO
           /  \        /  \       /  \
          3    5      2    9     0    7   ← hojas: la heurística de Carlos
```

- Cada nodo MIN toma el mínimo: 3, 2, 0
- El nodo MAX toma el máximo de esos: **3**

🎯 **Tu frase:** *"Minimax no busca la jugada que más me conviene si el
rival se equivoca. Busca la que **mejor resiste** si el rival juega
perfecto."*

---

## 3.2 ✂️ La poda Alfa-Beta ⭐ TU TEMA ESTRELLA

### El problema

El árbol crece **exponencialmente**. Con ~10 jugadas legales por turno,
mirar 6 jugadas adelante son 10⁶ = **un millón** de posiciones.

### La idea de la poda (explícala con este ejemplo)

```
            MAX
           /    \
      MIN A      MIN B
      /  \       /   \
     3    5     2     ???   ← ¡esta rama NO hace falta mirarla!
```

1. Exploro **A** completo → vale 3 (MIN eligió el mínimo entre 3 y 5).
2. Empiezo **B** y el primer hijo vale **2**.
3. B es un nodo MIN, así que su valor final será **≤ 2**.
4. Pero yo (MAX) ya tengo **3** garantizado con A.
5. **Nunca elegiría B.** ✂️ No hace falta mirar el resto.

### Las dos variables

| Variable | Significado |
|---|---|
| **α (alfa)** | Lo mejor que **MAX** tiene asegurado hasta ahora |
| **β (beta)** | Lo mejor que **MIN** tiene asegurado hasta ahora |

**Condición de corte: `α ≥ β`** → la rama actual ya no puede influir en
la decisión, porque el jugador de arriba ya tiene una opción al menos
igual de buena.

### 🚨 La afirmación clave

> 💬 **"La poda NO cambia el resultado. Solo cambia el trabajo. Devuelve
> exactamente el mismo valor que un Minimax sin poda."**

**Y no lo decimos de palabra: lo demostramos.** `agente.py` incluye
`minimax_sin_poda()`, una implementación de referencia deliberadamente
lenta y **obviamente correcta**:

```python
def minimax_sin_poda(estado, profundidad, jugador_max, ply=0):
    resultado = motor.ganador(estado)
    if resultado is not None or profundidad == 0:
        return heuristica.evaluar(estado, jugador_max, ply, resultado)
    valores = [minimax_sin_poda(motor.aplicar(estado, m, validar=False),
                                profundidad - 1, jugador_max, ply + 1)
               for m in motor.movimientos_legales(estado)]
    return max(valores) if estado.turno == jugador_max else min(valores)
```

Y las pruebas comparan las dos búsquedas sobre **decenas de posiciones
y varias profundidades**. Si alguna vez difirieran, la optimización
estaría mal.

> 🎤 **Si el profesor pregunta "¿cómo sé que su poda es correcta?"**,
> esta es tu respuesta, y es de las mejores del proyecto.

### 📊 Evidencia real (tablero 6×6, posición inicial)

| Profundidad | Sin poda | Con poda | Poda + tabla | Ahorro |
|---|---|---|---|---|
| 3 | 326 | 135 | 135 | 2,4× |
| 4 | 2 702 | 584 | 469 | 5,8× |
| 5 | **24 028** | 2 214 | **1 475** | **16,3×** |

Ramificación efectiva tras podar: **4,67** (frente a las jugadas
legales reales).

---

## 3.3 🎯 El orden de los movimientos lo es TODO

**❓ "¿Por qué importa el orden si el resultado es el mismo?"**

Porque **Alfa-Beta poda más cuanto antes aparezca la mejor jugada**.

- 🥇 **Orden perfecto:** el ahorro es máximo (raíz cuadrada del número
  de nodos: pasas de `bᵈ` a `b^(d/2)`, que es como **duplicar la
  profundidad gratis**).
- 🥉 **Orden pésimo** (peor jugada primero): la poda no sirve
  prácticamente de nada.

### Nuestras dos fuentes de orden

**1. El orden natural del motor.** `movimientos_legales()` devuelve
primero las **salidas**, luego los **avances**, luego los
**laterales** — `config.ORDEN_TIPOS_MOVIMIENTO`.

> 💬 *"Las salidas y los avances son justamente las jugadas que más
> reducen h(n), la distancia a la meta. Explorar primero lo que más
> promete es la misma idea que en una búsqueda informada."*

**2. La mejor jugada de la iteración anterior**, guardada en la tabla
de transposiciones. Es la optimización **más rentable de todas**: si la
primera jugada examinada resulta ser la mejor, todas las demás se podan
casi de inmediato.

```python
@staticmethod
def _ordenar(movimientos, sugerido):
    if sugerido is None or sugerido not in movimientos:
        return movimientos
    return [sugerido] + [m for m in movimientos if m != sugerido]
```

---

## 3.4 🗃️ La tabla de transposiciones

### ¿Qué es una "transposición"?

**Distintas secuencias de jugadas que llevan a la misma posición.**
Mover primero la ficha 1 y luego la 2 da el mismo tablero que mover
primero la 2 y luego la 1. Sin tabla, el árbol vuelve a evaluar ese
subárbol entero **cada vez**.

### 🎁 Aquí cobramos una decisión de la Entrega 1

> 💬 *"`Estado` es un `NamedTuple` de `frozenset`, o sea **hashable**, y
> sirve tal cual como clave de un diccionario. No tuvimos que inventar
> ninguna función de hash: el diseño inmutable del motor nos lo dio
> gratis."*

### Qué se guarda

```python
class Entrada(NamedTuple):
    profundidad: int       # profundidad RESTANTE con la que se analizó
    valor: float           # puntaje, ya normalizado
    bandera: str           # EXACTO | COTA_INFERIOR | COTA_SUPERIOR
    mejor: Movimiento      # para ordenar en el futuro
```

**Las tres banderas** (te lo pueden preguntar):

| Bandera | Significado | Cuándo se guarda |
|---|---|---|
| `EXACTO` | El valor guardado es el verdadero | El nodo se exploró completo dentro de la ventana |
| `COTA_INFERIOR` | El verdadero es **≥** al guardado | Hubo corte por beta (fail-high) |
| `COTA_SUPERIOR` | El verdadero es **≤** al guardado | Nunca superó alfa (fail-low) |

**Reemplazo:** si la entrada existente se analizó **más a fondo**, se
conserva. Vale más una respuesta mirando 6 jugadas que una mirando 2.

---

## 3.5 ⚠️ EL DETALLE DELICADO: puntajes de victoria en la tabla

🔴 **Esto es lo más sofisticado del proyecto. Domínalo.**

### El problema

`evaluar()` devuelve `VICTORIA − profundidad` para un final ganado. Ese
valor depende de **DÓNDE está el nodo en el árbol**, no solo de la
posición.

Si lo guardaras tal cual y lo reutilizaras desde **otra** profundidad,
el agente creería tener una victoria más cercana (o más lejana) de lo
que realmente es.

### La solución

```python
def _hacia_la_tabla(valor, ply):      # al GUARDAR
    if valor >= UMBRAL_VICTORIA:  return valor + ply
    if valor <= -UMBRAL_VICTORIA: return valor - ply
    return valor                       # los puntajes normales no se tocan

def _desde_la_tabla(valor, ply):      # al LEER (operación inversa)
    if valor >= UMBRAL_VICTORIA:  return valor - ply
    if valor <= -UMBRAL_VICTORIA: return valor + ply
    return valor
```

Se convierte el puntaje a **"distancia desde este nodo"**. Así el valor
guardado dice *"desde aquí se gana en d jugadas"*, que **sí** es una
propiedad de la posición y no del sitio donde la encontramos.

> 🎤 **Frase para la defensa:** *"Es el error clásico de un Minimax con
> transposiciones, y es exactamente lo que caza nuestra prueba
> `test_la_tabla_no_altera_el_valor`: compara la búsqueda con tabla
> contra el Minimax puro. Si la normalización estuviera mal, los
> valores se desviarían justo en las posiciones ganadas, que son las
> que importan."*

---

## 3.6 🔁 Profundización iterativa y búsqueda "anytime"

### Qué es

En vez de buscar directamente a profundidad 6, se busca a **1, luego 2,
luego 3…** hasta la profundidad objetivo o hasta agotar el tiempo.

### ❓ "¿No es un desperdicio repetir el trabajo?"

**No, y hay dos razones:**

**1. Cada iteración deja en la tabla la mejor jugada de cada posición.**
La iteración siguiente empieza examinando esa jugada primero y **poda
muchísimo más**. El trabajo "repetido" es una inversión en ordenamiento.

📐 *Dato numérico:* el árbol crece exponencialmente, así que las
iteraciones 1..d−1 juntas cuestan mucho menos que la iteración d. El
sobrecoste teórico es de apenas ~b/(b−1), y el mejor ordenamiento
**compensa de sobra**.

**2. Siempre hay una respuesta lista.** Eso es la propiedad
**ANYTIME**: si te interrumpen en cualquier momento, tienes una jugada
válida disponible.

### 🎯 La sutileza que debes mencionar tú mismo

> 💬 *"Si el tope de tiempo salta a media iteración, devolvemos el
> resultado de la **última profundidad COMPLETA**, nunca el de una
> iteración a medias. Como la raíz se explora en orden, una iteración
> incompleta solo ha visto las primeras jugadas y su 'mejor' estaría
> **sesgada por ese orden**."*

⭐ Esa observación demuestra que entendiste el algoritmo de verdad.

### El corte temprano

```python
if abs(valor) >= config.UMBRAL_VICTORIA:
    break   # ya demostró victoria o derrota forzada
```

Si ya sabes que ganas, mirar más hondo no aporta nada.

---

## 3.7 ⚖️ g(n) vs h(n) — la pregunta que SEGURO te hacen

### En A\* (búsqueda informada clásica)

```
f(n) = g(n) + h(n)
       ↑      ↑
       │      └── coste ESTIMADO de aquí al final
       └───────── coste REAL ya pagado desde el inicio
```

### En nuestro árbol de juego

| Concepto | Dónde está en nuestro código |
|---|---|
| **g(n)** | La **PROFUNDIDAD** del nodo (`ply`): cuántas jugadas se gastaron para llegar. Es coste ya pagado y **conocido**. |
| **h(n)** | Lo que devuelve `heuristica_dodgem()` en las hojas del corte de profundidad. Es la estimación de lo que **falta**. |
| **f(n)** | La función `evaluar()`, que combina ambas: un final ganado vale `VICTORIA − profundidad`. |

### 🚨 Sé honesto con el matiz (esto te da credibilidad)

> 💬 *"Conviene enunciarlo con precisión, porque **no son el mismo
> algoritmo**. En A\* ordenas la frontera por f = g + h. En Minimax no
> hay frontera ordenada: hay un árbol con dos jugadores. La analogía es
> **real pero no literal**: g(n) aparece como el descuento por
> profundidad, que hace que entre dos victorias el agente elija la más
> corta y entre dos derrotas la más larga. Y h(n) es literalmente la
> heurística en las hojas."*

⚠️ Si dices "esto es A\*" sin más, un profesor atento te corrige. Si tú
mismo señalas el matiz, ganas puntos.

---

## 3.8 🔍 Función por función

| Función | Qué hace | Por qué existe |
|---|---|---|
| `_Buscador.__init__` | Guarda jugador, tabla, reloj, contadores | Se separa del agente porque el **agente** vive toda la partida (conserva la tabla) y el **buscador** vive una sola jugada (contadores y reloj) |
| `_comprobar_limites()` | Revisa reloj y cancelación | Solo cada **2048 nodos**: consultar el reloj en cada nodo costaría más que evaluar la posición |
| `_ordenar()` | Pone delante la mejor jugada conocida | La optimización más rentable |
| `_alfa_beta()` | El núcleo recursivo | Es el algoritmo |
| `_guardar()` | Escribe en la tabla con reemplazo por profundidad | Al llenarse, la tabla se vacía entera (política simple, se reinicia por partida) |
| `buscar_raiz()` | Explora la raíz y devuelve **(valor, jugada)** | La raíz se trata aparte porque aquí sí importa **cuál** es la mejor jugada, no solo su valor |
| `AgenteMinimax.elegir()` | Profundización iterativa + estadísticas | Es la API pública |
| `AgenteMinimax.reiniciar()` | Vacía la tabla | Al empezar partida nueva |
| `elegir_movimiento()` | API mínima: estado → jugada | Es la firma que prometimos al cerrar la Entrega 1 |
| `minimax_sin_poda()` | Referencia lenta y correcta | **Para demostrar que la poda no altera el resultado** |
| `valor_con_alfa_beta()` | Valor + nodos visitados | Permite medir cuánto ahorra cada optimización activándolas y desactivándolas |

### `Resultado` — lo que ve el usuario

```python
class Resultado(NamedTuple):
    movimiento, valor, profundidad, nodos, podas,
    aciertos_tabla, segundos, completa
```

El panel lateral muestra esto en vivo durante la partida.

> 💬 *"Esos números no son decoración: son **la evidencia de que la
> poda funciona**. En la interrogación permiten comparar nodos
> visitados y podas entre un nivel y otro sin salir del juego."*

---

## 3.9 🔥 CAMBIOS EN VIVO — Tu guion paso a paso

### 🎚️ Cambio 1: "Cambie la profundidad / añada un nivel"

**Archivo:** `config.py`, sección 9.

```python
NIVELES = {
    "facil":   {"profundidad": 2, "segundos": 2.0,  "descripcion": "..."},
    "medio":   {"profundidad": 4, "segundos": 4.0,  "descripcion": "..."},
    "dificil": {"profundidad": 6, "segundos": 8.0,  "descripcion": "..."},
    "experto": {"profundidad": 8, "segundos": 15.0, "descripcion": "..."},
    # ← AÑADE AQUÍ
    "brutal":  {"profundidad": 10, "segundos": 30.0,
                "descripcion": "Cinco jugadas por bando."},
}
ORDEN_NIVELES = ("facil", "medio", "dificil", "experto", "brutal")
```

> 🎤 *"La interfaz genera los botones a partir de `ORDEN_NIVELES`, así
> que el nivel nuevo **aparece solo** sin tocar `gui.py`."*

### 🎲 Cambio 2: "Hágalo estocástico (que elija al azar entre empates)"

⭐ **Esta es tu pregunta trampa. Prepárala bien.**

**Estado actual: DETERMINISTA.** En `buscar_raiz`, entre jugadas de
igual valor se queda con la **primera** (`if valor > mejor_valor`, con
`>` estricto).

**Cómo hacerlo estocástico** — en `agente.py`, `buscar_raiz`:

```python
import random   # ← añadir arriba del archivo

# ANTES
for movimiento in movimientos:
    hijo = motor.aplicar(estado, movimiento, validar=False)
    valor = self._alfa_beta(hijo, profundidad - 1, alfa, beta, 1)
    if maximizando:
        if valor > mejor_valor:
            mejor_valor, mejor_movimiento = valor, movimiento
            alfa = max(alfa, valor)

# DESPUÉS: se recogen TODAS las empatadas y se elige una al azar
empatadas = []
for movimiento in movimientos:
    hijo = motor.aplicar(estado, movimiento, validar=False)
    valor = self._alfa_beta(hijo, profundidad - 1, -INFINITO, INFINITO, 1)
    if valor > mejor_valor:
        mejor_valor, empatadas = valor, [movimiento]
    elif valor == mejor_valor:
        empatadas.append(movimiento)
mejor_movimiento = random.choice(empatadas)
```

🚨 **El detalle CRÍTICO que debes mencionar** (y que casi nadie ve):

> 💬 *"Fíjese que al hacerlo estocástico **hay que dejar de podar con
> alfa en la raíz**: le paso `-INFINITO, INFINITO` a cada hijo. Si
> podara, las jugadas inferiores devolverían **cotas** en lugar de
> valores exactos, y el conjunto de 'empatadas' quedaría mal
> identificado. Se pierde algo de velocidad en la raíz —solo ahí, las
> ramas internas siguen podando— a cambio de que el desempate sea
> correcto."*

**Ventajas de cada opción:**

| Determinista ✅ | Estocástico ✅ |
|---|---|
| Reproducible: misma partida siempre | Menos predecible para el humano |
| Se puede depurar | Más natural de jugar |
| **Se puede reproducir en la evaluación** | Necesario para **medir** (si no, 20 partidas son 1 repetida 20 veces) |

> 🎤 *"De hecho, en nuestro **banco de medición** el agente **sí** es
> estocástico, justamente porque enfrentando dos agentes deterministas
> las 20 partidas serían la misma repetida. En el juego lo dejamos
> determinista para que usted pueda reproducir una partida."*

⭐⭐ Esa respuesta es de sobresaliente: muestra que entiendes que la
misma decisión de diseño tiene respuestas distintas según el contexto.

### ⏱️ Cambio 3: "Quite el límite de tiempo" / "Póngalo en 1 segundo"

```python
NIVELES["dificil"]["segundos"] = 1.0     # o 0 para desactivarlo
```

**Cómo explicar el diseño:**

> *"La **profundidad manda** y el tiempo es solo una red de seguridad.
> Lo elegimos así porque el bot debe ser **reproducible**: si la
> dificultad dependiera del reloj, jugaría distinto en cada computador
> y usted no podría reproducir una partida. El tope solo se activa en
> tableros grandes."*

📊 **Datos que respaldan la decisión:**

| Nivel | n=6 | n=10 | n=16 |
|---|---|---|---|
| fácil (prof. 2) | 0,00 s | 0,00 s | 0,01 s |
| medio (prof. 4) | 0,01 s | 0,03 s | 0,25 s |
| difícil (prof. 6) | 0,09 s | 0,78 s | **8,02 s\*** |
| experto (prof. 8) | 0,50 s | 5,67 s | **15,04 s\*** |

`*` = actuó el tope de seguridad.

### 🔬 Cambio 4: "Demuéstreme que la poda sirve"

```bash
python banco_agente.py
```

O en vivo:

```python
python3 -c "
import agente, config, motor
e = motor.estado_inicial(6)
for usar in (False, True):
    v, n = agente.valor_con_alfa_beta(e, 5, 'A', usar_tabla=False, usar_poda=usar)
    print('poda=%-5s  valor=%.1f  nodos=%d' % (usar, v, n))"
```

> 🎤 *"Fíjese que el **valor es idéntico** en las dos líneas. Solo
> cambian los nodos: de 24 028 a 2 214."*

---

## 3.10 🎯 Preguntas trampa para Valentín

| ❓ Pregunta | ✅ Respuesta |
|---|---|
| *"¿Alfa-Beta encuentra siempre la misma jugada que Minimax puro?"* | *"Siempre el mismo **valor**. La **jugada** puede diferir si hay empates, porque depende del orden de exploración. Ambas son óptimas."* ⭐ |
| *"¿Qué pasa si la heurística de Carlos es mala?"* | *"El agente juega mal, pero **la búsqueda sigue siendo correcta**. Son responsabilidades separadas: yo garantizo que encuentro el óptimo **según la función de evaluación**; Carlos garantiza que esa función mide lo correcto."* |
| *"¿Por qué su agente juega en otro hilo?"* | *"Porque si Minimax corriera en el hilo de Tkinter, la ventana dejaría de repintarse y el sistema la marcaría como 'no responde'."* |
| *"¿Y si el usuario reinicia mientras piensa?"* | *"Hay un contador de **generación**: el resultado que llega tarde trae una generación antigua y se descarta. Además un `threading.Event` cancela la búsqueda."* |
| *"¿Su agente es óptimo?"* | *"Es óptimo **hasta la profundidad de búsqueda**. Más allá confía en la heurística. Solo con profundidad infinita sería juego perfecto."* |
| *"¿Cuántos nodos por segundo?"* | *"Depende de la posición. La heurística cuesta ~15,7 µs, así que el techo son ~64 000 evaluaciones/s. A profundidad 5 visitamos 1 475 nodos con tabla."* |
| *"¿Por qué guarda la tabla entre jugadas?"* | *"Porque las posiciones ya analizadas siguen siendo válidas. `config.REUSAR_TABLA_ENTRE_JUGADAS` lo controla; se limpia al empezar partida nueva."* |
| *"¿Qué pasa si dos posiciones distintas tienen el mismo hash?"* | *"No usamos hash truncado: la clave es el `Estado` completo, así que Python compara por igualdad real. No hay colisiones falsas. En motores serios se usa Zobrist de 64 bits y sí puede haber colisiones."* ⭐ |

---

# 🚨 ANEXO: Cosas que TODOS deben saber

## ⚠️ Limitaciones honestas (mejor decirlas ustedes que descubrirlas)

**1. Muchas partidas bot-contra-bot no terminan.** 8 de cada 20 llegan
al tope de 400 jugadas.

> *"Es una propiedad conocida del Dodgem en tableros pares: con juego
> defensivo por ambos lados la partida puede no acabar. Está
> documentado para 4×4 y 5×5. Por eso implementamos tablas opcionales
> con `TABLAS_HABILITADAS`."*

💡 **Si van a demostrar bot vs bot mañana, actívenlo antes.**

**2. Los pesos están ajustados sobre 6×6 y 8×8 a profundidad 1–2.**

> *"El siguiente paso sería re-tunearlos contra el agente final, no
> contra el baseline de solo distancia."*

**3. Si se invierte el avance de un jugador a un eje distinto**, hay
que cambiar también sus `DIRECCIONES_LATERALES` para que sean
perpendiculares.

## 🧪 El as bajo la manga: las pruebas

```bash
python -m unittest pruebas_motor pruebas_heuristica pruebas_agente -v
```

**98 pruebas.** Si el profesor duda de una afirmación, hay una prueba
que la respalda:

| Afirmación | Prueba que la demuestra |
|---|---|
| "`aplicar` no muta" | `test_no_muta_el_estado_original` |
| "La distancia es admisible" | `test_es_exacta_en_el_problema_relajado` (BFS independiente) |
| "Cada turno reduce D en ≤1" | `test_cada_turno_reduce_la_distancia_total_a_lo_sumo_en_uno` |
| "La poda no cambia el valor" | `test_la_poda_no_altera_el_valor` |
| "La tabla no cambia el valor" | `test_la_tabla_no_altera_el_valor` |
| "n impar funciona" | `test_acepta_tableros_impares_si_se_cambia_la_paridad` |
| "Nunca hay fichas encimadas" | `test_nunca_hay_fichas_encimadas_en_la_apertura` |

> 🎤 **Frase de cierre potentísima:** *"Cada afirmación de diseño que
> acabamos de hacer tiene una prueba unitaria que la respalda. Puede
> ejecutarlas ahora mismo."*

## 💬 Las 5 frases que deben salir en la defensa

1. 🏛️ *"La interfaz no sabe jugar al Dodgem. Si una jugada se resalta
   es porque el motor la devolvió."*
2. 🧊 *"El estado es inmutable y hashable, y eso nos dio la tabla de
   transposiciones gratis."*
3. 🎯 *"Un destino fuera del tablero es legal solo si el vector era el
   de avance. Esa única condición implementa las dos reglas de salida."*
4. 📐 *"La distancia Manhattan degenera en una coordenada porque la meta
   es una línea, no un punto. Es el resultado exacto de la definición."*
5. ✂️ *"La poda no cambia el resultado, solo el trabajo. Y lo
   demostramos comparando contra un Minimax sin poda."*

## ✅ Checklist para esta noche

- [ ] Cada uno **abre su archivo** y lee las funciones de su sección
- [ ] Donovan ejecuta los 6 cambios en vivo y los deshace
- [ ] Carlos ejecuta `explicar()` antes y después de cambiar un peso
- [ ] Valentín ejecuta el comparador de nodos con y sin poda
- [ ] Los tres corren `python -m unittest ... -v` y ven los 98 OK
- [ ] Los tres juegan **una partida completa** contra el bot
- [ ] Los tres se saben las 5 frases
- [ ] Decidir **quién responde qué** si la pregunta es ambigua
- [ ] Dejar el proyecto abierto en el editor, con `config.py` a mano

---

**¡Mucha suerte mañana! 🍀**

*Recuerden: el profesor no busca que reciten. Busca que entiendan.
Cuando expliquen **por qué** tomaron una decisión, no solo **qué**
hace el código, ahí es donde se gana la defensa.* 💪

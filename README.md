# Tetris con Inteligencia Artificial (DQN)

Este repositorio contiene una implementación completa del juego clásico **Tetris** en Python utilizando la librería **Pygame** para la interfaz gráfica. Además de la modalidad de juego manual, incluye un agente de aprendizaje por refuerzo profundo (**Deep Q-Network - DQN**) que aprende a jugar al Tetris analizando configuraciones futuras del tablero (*afterstates*).

---

## 📂 Estructura del Proyecto

La carpeta contiene los siguientes archivos principales:

1. **[`tetris_engine.py`](file:///C:/Users/jorje/tetris/tetris_engine.py)**: El motor del juego. Contiene toda la lógica matemática del Tetris (tablero, rotaciones, caídas, colisiones, sistema de puntuación, cálculo de niveles y generación de piezas). Es un módulo de lógica pura y **no depende de Pygame**, lo que permite entrenar la IA a máxima velocidad.
2. **[`tetris_ui.py`](file:///C:/Users/jorje/tetris/tetris_ui.py)**: Contiene las funciones auxiliares de renderizado y visualización gráfica compartidas tanto por el modo de juego manual como por el visualizador de la IA. Define el diseño, colores, fuentes, paneles de información (Hold, Next, Stats) y overlays de pausa/fin de juego.
3. **[`tetris.py`](file:///C:/Users/jorje/tetris/tetris.py)**: El punto de entrada para jugar manualmente como humano. Configura la ventana gráfica de Pygame y maneja las entradas del teclado de forma responsiva.
4. **[`train_ai.py`](file:///C:/Users/jorje/tetris/train_ai.py)**: El script de entrenamiento para la IA. Utiliza **TensorFlow/Keras** para construir y entrenar la red neuronal DQN basándose en el análisis de *afterstates*.
5. **[`play_ai.py`](file:///C:/Users/jorje/tetris/play_ai.py)**: Permite cargar un modelo entrenado (un archivo `.keras`) y ver visualmente en Pygame cómo juega la IA en tiempo real, permitiendo acelerar o ralentizar la velocidad de reproducción.
6. **[`compare_ai.py`](file:///C:/Users/jorje/tetris/compare_ai.py)**: Permite cargar dos modelos de IA diferentes y compararlos de forma visual y simultánea (lado a lado / split screen) en tiempo real con estadísticas independientes.

---

## ⚙️ Especificaciones del Motor de Juego (`tetris_engine.py`)

El motor implementa las reglas competitivas modernas del Tetris:
* **Sistema de Piezas (Random Generator)**: Las piezas se generan utilizando el sistema de "bolsa de 7" (*7-bag random generator*), garantizando una distribución uniforme de las piezas `I`, `O`, `T`, `S`, `Z`, `J` y `L`.
* **Sistema de Rotación y Kicks**: Implementa tablas de desvío (*kicks*) específicas para las rotaciones tradicionales (adaptado del estándar SRS), con tablas diferenciadas para la pieza `I` y el resto de piezas (`J`, `L`, `S`, `T`, `Z`).
* **Retardo de Bloqueo (Lock Delay)**: Cuando una pieza toca el suelo, el jugador tiene **0.5 segundos** (Lock Delay) para moverla o rotarla antes de que se fije de forma definitiva. Se permite un máximo de **15 reinicios** por movimiento/rotación para evitar el bloqueo infinito.
* **Progresión de Niveles y Gravedad**: El juego comienza en el nivel 1. Cada 10 líneas completadas se sube de nivel. La velocidad de caída (gravedad) se calcula mediante la fórmula `(0.8 - (level - 1) * 0.007) ** (level - 1)` segundos por celda. A partir del nivel 20, la gravedad se fija en `0.01` segundos por celda.
* **Sistema de Puntuación**:
  * **1 línea**: $40 \times \text{nivel}$
  * **2 líneas**: $100 \times \text{nivel}$
  * **3 líneas**: $300 \times \text{nivel}$
  * **4 líneas (Tetris)**: $1200 \times \text{nivel}$
  * **Soft Drop**: 1 punto por celda descendida.
  * **Hard Drop**: 2 puntos por celda descendida.

---

## 🤖 El Agente de Inteligencia Artificial (DQN)

El agente utiliza **Aprendizaje por Refuerzo** bajo el paradigma de **Deep Q-Learning** aplicado a *afterstates* (estados resultantes de una acción antes de la transición ambiental).

### 1. Representación del Estado (Features)
Para cada pieza que aparece en pantalla, la IA evalúa todas las posiciones y rotaciones posibles donde la pieza puede aterrizar. Para cada uno de estos escenarios futuros (*afterstates*), calcula un vector con **4 características (features)** del tablero resultante:
1. **Líneas Eliminadas**: Número de líneas que se completarán y limpiarán con esta colocación.
2. **Huecos (Holes)**: Número de celdas vacías que tienen al menos un bloque por encima en la misma columna. Los huecos bloquean el juego y son difíciles de limpiar.
3. **Variabilidad de Altura (Bumpiness)**: La suma de las diferencias absolutas de altura entre columnas adyacentes. Un tablero plano es más fácil de gestionar que uno muy irregular.
4. **Altura Agregada (Total Height)**: La suma de las alturas de todas las columnas. Mantener la pila baja reduce el riesgo de perder.

### 2. Arquitectura de la Red Neuronal
La red neuronal toma como entrada el vector de características de tamaño 4 y predice un único valor continuo $V(s)$, que representa la "calidad" o recompensa esperada a largo plazo del tablero resultante:
* **Entrada**: 4 características del tablero.
* **Capas Ocultas**: Dos capas densas (*Dense*) de 64 neuronas con activación **ReLU**.
* **Salida**: 1 neurona lineal (*Linear*) que estima el valor $V(s)$.

El agente elige la colocación que maximiza este valor estimado.

### 3. Entrenamiento (`train_ai.py`)
* **Función de Recompensa**: Por cada colocación realizada, recibe:
  * $+1.0$ por sobrevivir un turno.
  * $+(\text{líneas eliminadas})^2 \times 10$ como bonificación por limpiar líneas (incentiva hacer múltiples líneas a la vez).
  * $-2.0$ si la acción resulta en fin de partida (*Game Over*).
* **Exploración vs. Explotación**: Se utiliza una estrategia $\epsilon$-greedy que empieza en $\epsilon = 1.0$ (acciones aleatorias) y decae progresivamente hasta un mínimo de $\epsilon = 0.001$ a lo largo del 60% de los episodios de entrenamiento.
* **Target Network**: Se usa una red de destino (*Target Network*) para dar estabilidad al aprendizaje, la cual actualiza sus pesos copiando la red principal cada 5 episodios.
* **Replay Memory**: Guarda las últimas 20,000 transiciones y entrena extrayendo lotes aleatorios (*batches*) de tamaño 512.

Los modelos se guardan en la carpeta `models/`:
* `tetris_model.keras`: El modelo más reciente guardado cada 100 episodios.
* `tetris_best.keras`: El modelo con el mejor promedio histórico de recompensa de los últimos 100 episodios.

---

## 🛠️ Instalación y Requisitos

Asegúrate de tener instalado Python 3.8 o superior. Instala las dependencias necesarias ejecutando:

```bash
pip install pygame numpy tensorflow
```

---

## 🚀 Cómo Ejecutar

### 1. Jugar Manualmente
Para jugar de forma tradicional con teclado, ejecuta:
```bash
python tetris.py
```

**Controles del juego:**
* **`A` / `D`**: Mover pieza a la izquierda / derecha.
* **`S`**: Caída suave (*Soft Drop*).
* **`W`**: Caída instantánea (*Hard Drop*).
* **`J` / `K`**: Rotar en sentido horario / antihorario.
* **`I`**: Guardar pieza en reserva (*Hold*).
* **`P` / `Espacio`**: Pausar / reanudar el juego.
* **`R`**: Reiniciar la partida (solo cuando aparece la pantalla de *Game Over*).
* **`Esc`**: Salir del juego.

---

### 2. Entrenar a la IA desde Cero
Para iniciar el proceso de entrenamiento del agente DQN, ejecuta:
```bash
python train_ai.py [número_de_episodios]
```
*Por ejemplo, para entrenar durante 1000 episodios:*
```bash
python train_ai.py 1000
```
*(Por defecto entrenará durante 2500 episodios si no se especifica un número).*

* **Reanudar Entrenamiento**: Si ya tienes un entrenamiento previo y quieres continuarlo desde donde quedó cargando `models/tetris_model.keras`, añade la bandera `--resume`:
  ```bash
  python train_ai.py 1500 --resume
  ```

---

### 3. Ver jugar a la IA entrenada
Una vez que tengas un modelo guardado en la carpeta `models`, puedes ver al agente jugar en tiempo real:
```bash
python play_ai.py
```
*(Cargará automáticamente `models/tetris_best.keras` o, si no existe, `models/tetris_model.keras`).*

También puedes pasarle la ruta de cualquier modelo específico como argumento:
```bash
python play_ai.py models/tetris_model.keras
```

**Controles del visualizador de IA:**
* **`Espacio`**: Pausar / reanudar la simulación.
* **`+` / `-`**: Acelerar o ralentizar la velocidad a la que la IA coloca las piezas.
* **`R`**: Reiniciar la partida de la IA.
* **`Esc`**: Salir de la ventana gráfica.

---

### 4. Comparar Dos Agentes de IA Lado a Lado
Si has entrenado varios modelos con diferente número de episodios (por ejemplo, uno con 1000 y otro con 2000), puedes verlos competir simultáneamente en pantalla dividida:
```bash
python compare_ai.py
```
*(El script cargará `models/tetris_1000.keras` para el tablero izquierdo y `models/tetris_2000.keras` para el tablero derecho).*

**Controles de la Comparativa:**
* **`Espacio`**: Pausar / reanudar ambos tableros.
* **`+` / `-`**: Acelerar o ralentizar la velocidad de ambos agentes.
* **`R`**: Reiniciar ambas partidas.
* **`Esc`**: Salir de la comparativa.

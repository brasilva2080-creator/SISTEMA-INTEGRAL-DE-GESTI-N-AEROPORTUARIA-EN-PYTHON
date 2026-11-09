# AeroAndes — Sistema Integral de Gestión Aeroportuaria

Aplicación de escritorio académica para administrar vuelos, pasajeros, reservas,
asientos, check-in, equipaje, abordaje y rutas de un aeropuerto. La interfaz está
construida con **Tkinter/ttk**, los datos se persisten en **SQLite** y los
indicadores del panel principal se visualizan con **Matplotlib**.

> Todos los nombres, documentos, correos, teléfonos y movimientos incluidos son
> ficticios. El sistema no procesa pagos reales ni almacena información personal
> verdadera.

---

## 1. Funcionalidades

- Panel principal con métricas operativas, próximas salidas, distribución de
  vuelos y ocupación de vuelos.
- Registro, búsqueda, edición, cambio de estado y cancelación de vuelos.
- Directorio de pasajeros con validación de documento único e historial de
  reservas.
- Venta simulada de boletos, reservas pendientes/confirmadas/canceladas, mapa
  visual de asientos y comprobantes en texto.
- Check-in con control de reserva confirmada, equipaje, tarjeta de embarque y
  validación de peso.
- Abordaje mediante una cola FIFO persistente, procesamiento del siguiente
  pasajero y cierre del vuelo.
- Rutas y destinos mediante un grafo no dirigido de aeropuertos, con cálculo de
  camino por BFS.
- Bitácora persistente de operaciones y pila LIFO para deshacer acciones de la
  sesión actual.
- Datos de demostración con aeropuertos de Lima, Cusco, Arequipa, Piura y
  Tarapoto; vuelos con fechas relativas al día de ejecución.

---

## 2. Requisitos

- **Python 3.10 o superior**.
- **Tkinter** (incluido normalmente con Python en Windows).
- **SQLite** (incluido en la biblioteca estándar de Python).
- **Matplotlib 3.8 o superior**, única dependencia externa.
- No se requiere servidor web ni conexión a Internet para ejecutar la aplicación.

Verificación rápida de Tkinter:

```powershell
python -c "import tkinter; print('Tkinter', tkinter.TkVersion)"
```

---

## 3. Instalación y ejecución

Desde la carpeta del proyecto:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python main.py
```

Si PowerShell bloquea la activación del entorno virtual, puede usar:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

También se puede ejecutar sin entorno virtual, instalando la dependencia en el
Python actual:

```powershell
python -m pip install -r requirements.txt
python main.py
```

En Linux/macOS, la activación del entorno virtual es:

```bash
source .venv/bin/activate
python main.py
```

---

## 4. Pruebas automatizadas

La suite utiliza `unittest`, crea una base SQLite temporal aislada para cada
prueba y no modifica la base real del sistema.

```powershell
python -m unittest discover -s tests -v
```

Para ejecutar un archivo específico:

```powershell
python -m unittest tests.test_estructuras -v
python -m unittest tests.test_sistema -v
```

Cobertura principal:

- Operaciones de lista doblemente enlazada, cola FIFO, pila LIFO y grafo.
- Merge sort, quick sort, búsqueda lineal y búsqueda binaria.
- Registro y validación de vuelos y pasajeros.
- Reservas, asientos únicos, capacidad máxima y cancelación.
- Check-in, equipaje, tarjeta de embarque y bloqueo de reservas no confirmadas.
- Cola de abordaje FIFO, orden de procesamiento y cierre del vuelo.
- Construcción del grafo, cálculo de rutas BFS y CRUD de aeropuertos/rutas.
- Métricas del panel, distribuciones y datos de demostración idempotentes.
- Deshacer LIFO y protección frente a dependencias posteriores.

---

## 5. Base de datos y datos de demostración

Al iniciar por primera vez, la aplicación crea automáticamente:

- `aeropuerto.db`: base SQLite con el esquema y los datos de demostración.
- `comprobantes/`: carpeta donde se guardan comprobantes y tarjetas de embarque.

La siembra solo ocurre cuando la tabla `aeropuertos` está vacía. Las fechas de
los vuelos se generan a partir de la fecha de ejecución, por lo que los ejemplos
siempre incluyen salidas próximas.

### Reiniciar los datos

1. Cierre la aplicación.
2. Elimine la base y los archivos auxiliares de SQLite:

```powershell
Remove-Item aeropuerto.db* -Force -ErrorAction SilentlyContinue
```

3. Opcionalmente, elimine los documentos generados:

```powershell
Remove-Item comprobantes\* -Force -ErrorAction SilentlyContinue
```

4. Ejecute nuevamente `python main.py`. La base se creará y sembrará otra vez.

También puede usar una base alternativa al instanciar la aplicación:

```python
from app import AplicacionAeropuerto

app = AplicacionAeropuerto("ruta/a/otra_base.db")
app.ejecutar()
```

---

## 6. Estructura del proyecto

```text
AEROPUERTO/
├── main.py                  # Punto de entrada
├── app.py                   # Ventana principal, navegación y servicios compartidos
├── config.py                # Paleta, tipografías, fechas, moneda y rutas
├── database.py              # Esquema SQLite, claves foráneas e índices
├── seed.py                  # Datos ficticios iniciales
├── requirements.txt         # Dependencia externa (Matplotlib)
├── models/
│   ├── entidades.py         # Dataclasses del dominio
│   ├── aeropuerto.py        # Reexportación de compatibilidad
│   ├── pasajero.py          # Reexportación de compatibilidad
│   ├── reserva.py           # Reexportación de compatibilidad
│   └── vuelo.py             # Reexportación de compatibilidad
├── structures/
│   ├── lista.py             # Lista doblemente enlazada
│   ├── cola.py              # Cola FIFO
│   ├── pila.py              # Pila LIFO
│   ├── grafo.py             # Grafo ponderado no dirigido, BFS y DFS
│   └── ordenamiento.py      # Merge sort, quick sort y búsquedas
├── modules/
│   ├── dashboard.py         # Métricas y series para gráficos
│   ├── gestion_vuelos.py    # Reglas de vuelos, estados y caché
│   ├── gestion_pasajeros.py # Reglas de pasajeros e índices de búsqueda
│   ├── reservas.py          # Ventas, asientos y comprobantes
│   ├── checkin.py           # Check-in, equipaje y tarjetas
│   ├── abordaje.py          # Cola FIFO y cierre de abordaje
│   ├── rutas.py             # Aeropuertos, rutas y cálculo BFS
│   └── actividad.py         # Bitácora y pila de deshacer
├── views/
│   ├── dashboard.py         # Panel con tarjetas y gráficos
│   ├── vuelos_view.py       # Gestión de vuelos
│   ├── pasajeros_view.py    # Gestión de pasajeros
│   ├── reservas_view.py     # Reservas y mapa de asientos
│   ├── checkin_view.py      # Check-in y equipaje
│   ├── abordaje_view.py     # Cola y control de abordaje
│   ├── rutas_view.py        # Aeropuertos, rutas y grafo
│   ├── actividad_view.py    # Bitácora y pila LIFO
│   ├── widgets.py           # Tablas, tarjetas, modales, mapa y grafo
│   ├── base.py              # Vista base
│   └── theme.py             # Tema oscuro ttk
├── tests/
│   ├── test_estructuras.py  # Pruebas de estructuras y algoritmos
│   └── test_sistema.py      # Pruebas integrales de servicios
├── comprobantes/            # Documentos de texto generados
└── aeropuerto.db            # Base creada en la primera ejecución
```

---

## 7. Uso real de estructuras de datos

| Estructura / algoritmo | Dónde se utiliza |
| --- | --- |
| Lista doblemente enlazada | Carga y ordenamiento de vuelos, pasajeros y reservas antes de mostrarlos en las tablas. |
| Cola FIFO | Cola de abordaje. La cola se reconstruye desde `cola_abordaje` y respeta el orden de llegada. |
| Pila LIFO | Historial de la sesión (`Historial`). `Deshacer última` desapila la operación más reciente. |
| Diccionarios | Caché de vuelos por código/id, caché de pasajeros por código/documento y adyacencia del grafo. |
| Grafo ponderado no dirigido | Aeropuertos como vértices y rutas como aristas con distancia y duración. |
| BFS | Cálculo de la ruta con menos conexiones entre dos aeropuertos. |
| DFS | Recorrido alternativo implementado en el grafo y cubierto por pruebas. |
| Merge sort | Ordenamiento estable de vuelos y colecciones; también reordena la lista doble. |
| Quick sort | Algoritmo alternativo implementado y validado por pruebas. |
| Búsqueda lineal | Búsqueda de vuelos y pasajeros por coincidencias de texto. |
| Búsqueda binaria | Búsqueda sobre colecciones ordenadas, validada por pruebas. |

La pila de deshacer es **de sesión**: la bitácora completa queda en la tabla
`operaciones`, pero las operaciones anteriores a un reinicio no se pueden
revertir. Cada reversión comprueba dependencias posteriores (reservas, check-in,
cola o abordaje) antes de ejecutarse.

---

## 8. Reglas de negocio destacadas

- Un pasajero no puede tener dos reservas activas en el mismo vuelo.
- Un asiento no puede venderse dos veces en el mismo vuelo.
- Una reserva cancelada libera su asiento y no permite check-in ni abordaje.
- Solo las reservas confirmadas pueden hacer check-in.
- El check-in debe existir antes de agregar a un pasajero a la cola de abordaje.
- Un vuelo no puede superar la capacidad configurada.
- No se puede cancelar un vuelo con pasajeros ya abordados o en cola.
- No se puede finalizar el abordaje con pasajeros pendientes o en cola, salvo
  cierre forzado explícito.
- No se pueden crear rutas duplicadas, invertidas o de un aeropuerto a sí mismo.
- Los documentos y correos se validan antes de persistirse.

---

## 9. Flujo de demostración sugerido

1. Abra **Panel principal** para revisar métricas y próximas salidas.
2. En **Vuelos**, cree un vuelo o edite uno programado; pruebe **Cambiar estado**.
3. En **Pasajeros**, registre un pasajero ficticio y abra su historial de reservas.
4. En **Reservas**, seleccione un vuelo disponible, haga clic en un asiento del
   mapa y registre la reserva. Pruebe **Ver comprobante**.
5. En **Check-in**, busque `RES-100001` (confirmada), registre equipaje y genere
   la tarjeta. Intente `RES-100003` para comprobar que una reserva pendiente se
   rechaza.
6. En **Abordaje**, seleccione el vuelo `AER104`. La cola existente debe mostrar
   `RES-100011` antes de `RES-100012`. Use **Procesar siguiente** y luego
   **Finalizar abordaje**.
7. En **Rutas y destinos**, calcule una ruta entre Cusco y Piura; el resultado
   usa BFS y muestra distancia, duración y escalas.
8. En **Actividad**, revise la bitácora y pruebe **Deshacer última** después de
   una acción que no tenga dependencias posteriores.

---

## 10. Documentos generados

Los comprobantes y tarjetas se guardan como archivos `.txt` en `comprobantes/`:

- `RES-XXXXXX.txt`: comprobante de reserva.
- `TARJETA_TB-XXXXXXX.txt`: tarjeta de embarque.

Son documentos de simulación académica y no representan compras ni pagos reales.

---

## 11. Alcance y limitaciones

- Aplicación local de un solo usuario; no incluye autenticación ni red.
- No integra pasarelas de pago, correo, impresión térmica ni servicios externos.
- Los datos iniciales son ficticios y las fechas son dinámicas.
- SQLite usa WAL; por eso pueden aparecer archivos `aeropuerto.db-wal` y
  `aeropuerto.db-shm` mientras la aplicación está abierta.
- La interfaz está diseñada para una resolución mínima de 1160 × 760 píxeles.

# Proyecto Final — Pipeline de Transacciones de TiendaNova

[![CI](https://github.com/TU-USUARIO/TU-REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/TU-USUARIO/TU-REPO/actions/workflows/ci.yml)

> ⚠️ Reemplaza `TU-USUARIO/TU-REPO` en el badge de arriba por tu usuario y
> nombre de repositorio reales una vez publicado en GitHub.

Proyecto final del curso **CI/CD para Workflows de Datos con Python** (BSG
Institute). Pipeline que toma el registro de transacciones de junio de 2026
de TiendaNova, detecta filas corruptas mediante reglas genéricas (no
dirigidas a filas concretas), las pone en cuarentena y publica un reporte de
ingresos por categoría junto con un resumen de ejecución.

## Estructura

```
kit_inicio/
├── data/transacciones.csv       <- dataset de entrada (100 filas, no se edita a mano)
├── src/
│   ├── transform.py             <- limpieza + ingresos_por_categoria(df)
│   └── validate.py              <- validar_entrada(df) + separar_validas(df)
├── run_pipeline.py               <- CLI: --input, --output, --max-rechazo
├── tests/
│   ├── test_transform.py
│   ├── test_validate.py
│   └── data_checks/              <- checks de calidad con marker 'datos'
├── output/                        <- ingresos_categoria.csv, rechazadas.csv, resumen.json
├── .github/workflows/ci.yml       <- lint -> test -> datos
├── pyproject.toml
└── requirements*.txt
```

## Instalación y ejecución local

```bash
python -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Ejecutar el pipeline
python run_pipeline.py --input data/transacciones.csv --output output/ingresos_categoria.csv

# Suite de pruebas con cobertura
pytest -m "not datos" --cov=src --cov-fail-under=85

# Checks de calidad de datos
pytest -m datos

# Lint
flake8 src tests run_pipeline.py --max-line-length=100
```

## Validación de datos

- **`validar_entrada(df)`** (contrato mínimo): verifica que estén presentes
  las 9 columnas obligatorias del esquema. Si falta alguna, el pipeline
  termina con **exit 1**.
- **`separar_validas(df)`** (cuarentena): detecta los seis tipos de problema
  sembrados mediante reglas genéricas (nunca por índice de fila) y asigna
  **un único motivo por fila**, según esta prioridad:

  1. `transaccion_id_duplicado` — Unicidad (se conserva la primera
     ocurrencia como válida; las repeticiones se rechazan)
  2. `cantidad_invalida` — Validez (`cantidad <= 0` o nula)
  3. `precio_unitario_nulo` — Completitud
  4. `total_inconsistente` — Consistencia (`total ≠ cantidad × precio_unitario`, tolerancia 0.01)
  5. `metodo_pago_invalido` — Validez (fuera de `Tarjeta`/`Efectivo`/`Billetera`)
  6. `fecha_fuera_de_rango` — Validez (fuera de junio de 2026)

  Las filas rechazadas se archivan en `output/rechazadas.csv` con su
  columna `motivo`.
- **Criterio de aceptación**: si la tasa de rechazo supera `--max-rechazo`
  (por defecto `0.15`), el pipeline termina con **exit 2**. Con el dataset
  entregado la tasa es 0.10, así que el pipeline pasa.
- **Checks de datos** (`tests/data_checks/`, marker `datos`): columnas
  obligatorias presentes, volumen mínimo de filas y tasa de nulos bajo
  umbral (parametrizado) para `producto`, `categoria` y `precio_unitario`.

## Evidencias

### Suite de pruebas con cobertura (`pytest --cov=src`)

```
============================= test session starts =============================
platform win32 -- Python 3.12.8, pytest-8.3.4, pluggy-1.6.0
collected 36 items

tests/data_checks/test_calidad_datos.py ..... [ 13%]
tests/test_transform.py .......... [ 41%]
tests/test_validate.py ..................... [100%]

---------- coverage: platform win32, python 3.12.8-final-0 -----------
Name               Stmts   Miss  Cover   Missing
------------------------------------------------
src\__init__.py        0      0   100%
src\transform.py      23      0   100%
src\validate.py       30      0   100%
------------------------------------------------
TOTAL                 53      0   100%

Required test coverage of 85% reached. Total coverage: 100.00%

============================= 36 passed in 2.68s ==============================
```

### Ejecución del pipeline (`output/resumen.json`)

```json
{
  "filas_entrada": 100,
  "filas_rechazadas": 10,
  "tasa_rechazo": 0.1,
  "categorias_publicadas": [
    "Accesorios",
    "Audio",
    "Computo"
  ],
  "ingresos_totales": 138079.49,
  "ingresos_por_categoria": {
    "Accesorios": 8651.54,
    "Audio": 22291.17,
    "Computo": 107136.78
  }
}
```

### Job Summary del CI

> 📋 Pendiente: pegar aquí una captura del "Job Summary" de la pestaña
> Actions tras el primer workflow ejecutado en GitHub (job `datos`).

### CI en ROJO y en VERDE

> 📋 Pendiente: agregar dos capturas de la pestaña Actions — una ejecución
> en rojo (de cualquier fallo real durante el desarrollo, o de la prueba de
> fuego) y una en verde, demostrando que el semáforo del CI funciona en
> ambos sentidos.

## Preguntas de reflexión

**1. ¿Qué tipo de problema decidiste tratar como el más grave y por qué? ¿Cambiaría tu respuesta si el reporte alimentara pagos a proveedores?**

En este proyecto tratamos `transaccion_id_duplicado` como el más grave en
términos de riesgo silencioso: una fila duplicada es, por lo demás,
perfectamente "válida" (formato correcto, total consistente, categoría
conocida), por lo que no dispara ninguna otra señal de alerta y puede
inflar el ingreso reportado sin que nada "se vea mal". Si el reporte
alimentara pagos a proveedores, la respuesta cambiaría: el problema más
grave pasaría a ser `total_inconsistente` (y, en su origen,
`precio_unitario_nulo`), porque ahí el error se traduce directamente en un
monto de dinero incorrecto transferido a un tercero — un impacto financiero
inmediato y difícil de revertir, más grave que una fila duplicada que
"solo" infla un reporte agregado.

**2. Tu cuarentena asigna UN motivo por fila. ¿Qué fila del dataset podría calificar para dos motivos y cuál elegiste priorizar?**

Las filas con `precio_unitario` nulo (p. ej. `T-0053` y `T-0089`) podrían
calificar también como `total_inconsistente`, ya que no hay forma de
confirmar que `total = cantidad × precio_unitario` cuando falta uno de los
dos factores. Priorizamos `precio_unitario_nulo` (Completitud) sobre
`total_inconsistente` (Consistencia): la completitud es una precondición
para poder evaluar la consistencia, así que no tiene sentido acusar de
"inconsistente" un cálculo que ni siquiera se puede realizar.

**3. Si TiendaNova empezara a enviar el archivo cada madrugada, ¿qué UNA sola línea cambiarías o añadirías en tu workflow?**

Añadiría un disparador `schedule` al bloque `on:` de `ci.yml`, por ejemplo:

```yaml
  schedule:
    - cron: '0 9 * * *'
```

Con eso el workflow se ejecuta automáticamente cada madrugada (además de en
cada push), sin depender de que alguien haga un commit para disparar el
pipeline.

## Reglas de oro

- El CSV **no se edita a mano**: los checks y la cuarentena manejan los
  problemas que trae.
- Los checks son **genéricos** (reglas), nunca dirigidos a filas concretas.

import pandas as pd
import pytest

from src.transform import limpiar_datos, ingresos_por_categoria, normalizar_columnas


def _df_base():
    return pd.DataFrame(
        {
            "Transaccion_ID ": ["T-0001", "T-0002"],
            " Fecha": ["2026-06-01", "2026-06-02"],
            "cliente_id": ["C-001", "C-002"],
            "producto": ["Mouse", "Teclado"],
            "categoria": ["Accesorios", "Accesorios"],
            "cantidad": [2, 1],
            "precio_unitario": [10.0, 20.0],
            "total": [20.0, 20.0],
            "metodo_pago": ["Tarjeta", "Efectivo"],
        }
    )


def test_normalizar_columnas_minusculas_y_sin_espacios():
    df = _df_base()
    normalizado = normalizar_columnas(df)
    assert list(normalizado.columns)[:2] == ["transaccion_id", "fecha"]


def test_limpiar_datos_coerciona_tipos_numericos_y_fecha():
    df = _df_base()
    limpio = limpiar_datos(df)
    assert pd.api.types.is_numeric_dtype(limpio["cantidad"])
    assert pd.api.types.is_datetime64_any_dtype(limpio["fecha"])


def test_limpiar_datos_descarta_filas_sin_transaccion_id():
    df = _df_base()
    df.loc[0, "Transaccion_ID "] = None
    limpio = limpiar_datos(df)
    assert len(limpio) == 1
    assert limpio.iloc[0]["cliente_id"] == "C-002"


def test_limpiar_datos_descarta_filas_sin_categoria():
    df = _df_base()
    df.loc[1, "categoria"] = ""
    limpio = limpiar_datos(df)
    assert len(limpio) == 1


def test_limpiar_datos_con_dataframe_vacio():
    df = _df_base().iloc[0:0]
    limpio = limpiar_datos(df)
    assert limpio.empty


def test_ingresos_por_categoria_suma_correctamente():
    df = pd.DataFrame(
        {
            "categoria": ["Audio", "Audio", "Computo"],
            "total": [100.0, 50.0, 200.0],
        }
    )
    resultado = ingresos_por_categoria(df)
    esperado = {"Audio": 150.0, "Computo": 200.0}
    assert dict(zip(resultado["categoria"], resultado["total"])) == esperado


@pytest.mark.parametrize(
    "totales,categorias,esperado",
    [
        ([10.0, 10.0], ["Audio", "Audio"], {"Audio": 20.0}),
        ([5.0, 15.0], ["Audio", "Computo"], {"Audio": 5.0, "Computo": 15.0}),
        ([1.5, 2.5, 1.0], ["Accesorios", "Accesorios", "Audio"], {"Accesorios": 4.0, "Audio": 1.0}),
    ],
)
def test_ingresos_por_categoria_parametrizado(totales, categorias, esperado):
    df = pd.DataFrame({"categoria": categorias, "total": totales})
    resultado = ingresos_por_categoria(df)
    assert dict(zip(resultado["categoria"], resultado["total"])) == esperado


def test_ingresos_por_categoria_con_dataframe_vacio():
    df = pd.DataFrame(columns=["categoria", "total"])
    resultado = ingresos_por_categoria(df)
    assert resultado.empty
    assert list(resultado.columns) == ["categoria", "total"]

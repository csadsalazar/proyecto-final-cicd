import pandas as pd
import pytest

from src.validate import validar_entrada, separar_validas, COLUMNAS_REQUERIDAS


def _fila_valida(transaccion_id="T-0001", **overrides):
    fila = {
        "transaccion_id": transaccion_id,
        "fecha": pd.Timestamp("2026-06-15"),
        "cliente_id": "C-001",
        "producto": "Mouse",
        "categoria": "Accesorios",
        "cantidad": 2.0,
        "precio_unitario": 10.0,
        "total": 20.0,
        "metodo_pago": "Tarjeta",
    }
    fila.update(overrides)
    return fila


def _df(*filas):
    return pd.DataFrame(list(filas))


def test_validar_entrada_no_lanza_si_columnas_completas():
    df = _df(_fila_valida())
    validar_entrada(df)  # no debe lanzar


def test_validar_entrada_lanza_valueerror_si_falta_columna():
    df = _df(_fila_valida()).drop(columns=["metodo_pago"])
    with pytest.raises(ValueError):
        validar_entrada(df)


@pytest.mark.parametrize("columna", COLUMNAS_REQUERIDAS)
def test_validar_entrada_lanza_para_cualquier_columna_faltante(columna):
    df = _df(_fila_valida()).drop(columns=[columna])
    with pytest.raises(ValueError):
        validar_entrada(df)


def test_separar_validas_detecta_transaccion_duplicada():
    # Se conserva la primera ocurrencia como válida; solo la repetición se rechaza.
    df = _df(_fila_valida("T-0001"), _fila_valida("T-0001"))
    validas, rechazadas = separar_validas(df)
    assert len(validas) == 1
    assert len(rechazadas) == 1
    assert rechazadas.iloc[0]["motivo"] == "transaccion_id_duplicado"


def test_separar_validas_detecta_cantidad_invalida():
    df = _df(_fila_valida(cantidad=0.0, total=0.0))
    _, rechazadas = separar_validas(df)
    assert rechazadas.iloc[0]["motivo"] == "cantidad_invalida"


def test_separar_validas_detecta_precio_unitario_nulo():
    df = _df(_fila_valida(precio_unitario=None))
    _, rechazadas = separar_validas(df)
    assert rechazadas.iloc[0]["motivo"] == "precio_unitario_nulo"


def test_separar_validas_detecta_total_inconsistente():
    df = _df(_fila_valida(total=999.0))
    _, rechazadas = separar_validas(df)
    assert rechazadas.iloc[0]["motivo"] == "total_inconsistente"


def test_separar_validas_detecta_metodo_pago_invalido():
    df = _df(_fila_valida(metodo_pago="bitcoin"))
    _, rechazadas = separar_validas(df)
    assert rechazadas.iloc[0]["motivo"] == "metodo_pago_invalido"


def test_separar_validas_detecta_fecha_fuera_de_rango():
    df = _df(_fila_valida(fecha=pd.Timestamp("2027-01-01")))
    _, rechazadas = separar_validas(df)
    assert rechazadas.iloc[0]["motivo"] == "fecha_fuera_de_rango"


def test_separar_validas_asigna_un_solo_motivo_por_prioridad():
    # Cantidad invalida Y metodo de pago invalido: gana cantidad_invalida (mayor prioridad)
    df = _df(_fila_valida(cantidad=0.0, total=0.0, metodo_pago="bitcoin"))
    _, rechazadas = separar_validas(df)
    assert len(rechazadas) == 1
    assert rechazadas.iloc[0]["motivo"] == "cantidad_invalida"


def test_separar_validas_deja_pasar_filas_correctas():
    df = _df(_fila_valida("T-0001"), _fila_valida("T-0002"))
    validas, rechazadas = separar_validas(df)
    assert len(validas) == 2
    assert rechazadas.empty


def test_separar_validas_con_dataframe_vacio():
    df = _df(_fila_valida()).iloc[0:0]
    validas, rechazadas = separar_validas(df)
    assert validas.empty
    assert rechazadas.empty


def test_separar_validas_con_todo_el_dataframe_invalido():
    df = _df(
        _fila_valida("T-0001", cantidad=-1.0, total=-10.0),
        _fila_valida("T-0002", precio_unitario=None),
        _fila_valida("T-0003", metodo_pago="cheque"),
    )
    validas, rechazadas = separar_validas(df)
    assert validas.empty
    assert len(rechazadas) == 3

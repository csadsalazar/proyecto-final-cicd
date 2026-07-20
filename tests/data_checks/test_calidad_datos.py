"""Checks de calidad sobre el dataset real (marker 'datos')."""
import pandas as pd
import pytest

from src.validate import COLUMNAS_REQUERIDAS

RUTA_DATASET = "data/transacciones.csv"
VOLUMEN_MINIMO = 50


@pytest.fixture(scope="module")
def df_crudo():
    return pd.read_csv(RUTA_DATASET)


@pytest.mark.datos
def test_columnas_obligatorias_presentes(df_crudo):
    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df_crudo.columns]
    assert not faltantes, f"Faltan columnas obligatorias: {faltantes}"


@pytest.mark.datos
def test_volumen_minimo_de_filas(df_crudo):
    assert len(df_crudo) >= VOLUMEN_MINIMO


@pytest.mark.datos
@pytest.mark.parametrize(
    "columna,umbral_maximo",
    [
        ("producto", 0.05),
        ("categoria", 0.05),
        ("precio_unitario", 0.10),
    ],
)
def test_tasa_de_nulos_bajo_umbral(df_crudo, columna, umbral_maximo):
    tasa_nulos = df_crudo[columna].isna().mean()
    assert tasa_nulos <= umbral_maximo, (
        f"Columna {columna} tiene {tasa_nulos:.2%} de nulos, "
        f"supera el umbral de {umbral_maximo:.2%}"
    )

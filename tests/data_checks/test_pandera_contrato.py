"""Check de datos (marker 'datos'): el contrato de pandera detecta
violaciones en el dataset crudo, validando en modo lazy=True."""
import pandas as pd
import pandera.pandas as pa
import pytest

from src.pandera_schema import TRANSACCIONES_SCHEMA

RUTA_DATASET = "data/transacciones.csv"


@pytest.mark.datos
def test_esquema_pandera_detecta_violaciones_en_dataset_crudo():
    df_crudo = pd.read_csv(RUTA_DATASET)

    with pytest.raises(pa.errors.SchemaErrors) as excinfo:
        TRANSACCIONES_SCHEMA.validate(df_crudo, lazy=True)

    fallos = excinfo.value.failure_cases
    assert not fallos.empty, "El esquema debería detectar violaciones en el dataset crudo"

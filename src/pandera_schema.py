"""Contrato de transacciones.csv declarado como pandera.DataFrameSchema.

Es una expresión declarativa del mismo contrato de la sección 2.1: los
mismos tipos, rangos y catálogos que ya implementa `src.validate`, pero
verificados con una librería de validación de esquemas en vez de reglas
escritas a mano.
"""
import pandas as pd
import pandera.pandas as pa
from pandera.pandas import Check, Column, DataFrameSchema

TOLERANCIA_TOTAL = 0.01

TRANSACCIONES_SCHEMA = DataFrameSchema(
    {
        "transaccion_id": Column(
            str, checks=Check.str_matches(r"^T-\d{4}$"), unique=True
        ),
        "fecha": Column(
            pa.DateTime,
            checks=Check.in_range(pd.Timestamp("2026-06-01"), pd.Timestamp("2026-06-30")),
            coerce=True,
        ),
        "cliente_id": Column(str, checks=Check.str_matches(r"^C-\d{3}$")),
        "producto": Column(str, nullable=False),
        "categoria": Column(str, checks=Check.isin(["Computo", "Accesorios", "Audio"])),
        "cantidad": Column(float, checks=Check.ge(1)),
        "precio_unitario": Column(float, checks=Check.gt(0), nullable=False),
        "total": Column(float),
        "metodo_pago": Column(str, checks=Check.isin(["Tarjeta", "Efectivo", "Billetera"])),
    },
    checks=Check(
        lambda df: (
            (df["cantidad"] * df["precio_unitario"] - df["total"]).abs() <= TOLERANCIA_TOTAL
        )
        | df["precio_unitario"].isna(),
        error="total_inconsistente: total != cantidad * precio_unitario",
    ),
)

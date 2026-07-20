"""Validación de datos: contrato de entrada y cuarentena por reglas."""
import pandas as pd

COLUMNAS_REQUERIDAS = [
    "transaccion_id",
    "fecha",
    "cliente_id",
    "producto",
    "categoria",
    "cantidad",
    "precio_unitario",
    "total",
    "metodo_pago",
]

METODOS_VALIDOS = ["Tarjeta", "Efectivo", "Billetera"]
FECHA_INICIO = pd.Timestamp("2026-06-01")
FECHA_FIN = pd.Timestamp("2026-06-30")
TOLERANCIA_TOTAL = 0.01


def validar_entrada(df: pd.DataFrame) -> None:
    """Verifica el contrato mínimo: presencia de columnas obligatorias.

    Lanza ValueError si falta alguna columna requerida por el esquema.
    """
    faltantes = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    if faltantes:
        raise ValueError(
            f"Contrato de entrada violado, faltan columnas: {faltantes}"
        )


def separar_validas(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Separa filas válidas de rechazadas según las reglas de negocio.

    Cada fila rechazada recibe UN motivo, asignado por prioridad (la
    primera regla que la fila incumple, en este orden). Ante un
    transaccion_id repetido se conserva la primera ocurrencia como
    válida y se rechazan las repeticiones siguientes:
    1. transaccion_id_duplicado   (unicidad)
    2. cantidad_invalida          (validez)
    3. precio_unitario_nulo       (completitud)
    4. total_inconsistente        (consistencia)
    5. metodo_pago_invalido       (validez)
    6. fecha_fuera_de_rango       (validez)
    """
    df = df.reset_index(drop=True).copy()
    motivo = pd.Series([None] * len(df), index=df.index, dtype=object)

    dup_mask = df["transaccion_id"].duplicated(keep="first")
    motivo = motivo.mask(dup_mask & motivo.isna(), "transaccion_id_duplicado")

    cantidad_mask = df["cantidad"].isna() | (df["cantidad"] <= 0)
    motivo = motivo.mask(cantidad_mask & motivo.isna(), "cantidad_invalida")

    precio_nulo_mask = df["precio_unitario"].isna()
    motivo = motivo.mask(precio_nulo_mask & motivo.isna(), "precio_unitario_nulo")

    calculado = df["cantidad"] * df["precio_unitario"]
    inconsistente_mask = ((calculado - df["total"]).abs() > TOLERANCIA_TOTAL).fillna(False)
    motivo = motivo.mask(inconsistente_mask & motivo.isna(), "total_inconsistente")

    metodo_mask = ~df["metodo_pago"].isin(METODOS_VALIDOS)
    motivo = motivo.mask(metodo_mask & motivo.isna(), "metodo_pago_invalido")

    fecha_mask = df["fecha"].isna() | (df["fecha"] < FECHA_INICIO) | (df["fecha"] > FECHA_FIN)
    motivo = motivo.mask(fecha_mask & motivo.isna(), "fecha_fuera_de_rango")

    df["motivo"] = motivo
    rechazadas = df[df["motivo"].notna()].reset_index(drop=True)
    validas = df[df["motivo"].isna()].drop(columns=["motivo"]).reset_index(drop=True)
    return validas, rechazadas

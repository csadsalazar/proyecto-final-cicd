"""Transformación pura del pipeline de transacciones de TiendaNova."""
import pandas as pd

COLUMNAS_NUMERICAS = ["cantidad", "precio_unitario", "total"]


def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de columna: minúsculas, sin espacios sobrantes."""
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )
    return df


def limpiar_datos(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza columnas, tipa los campos y descarta filas inutilizables.

    Una fila se considera inutilizable (no evaluable por ninguna regla de
    negocio) cuando le falta el identificador de transacción o la categoría,
    o cuando sus columnas numéricas no son ni siquiera convertibles a número.
    """
    df = normalizar_columnas(df)

    for col in COLUMNAS_NUMERICAS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "fecha" in df.columns:
        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    if "transaccion_id" in df.columns:
        df = df[df["transaccion_id"].notna() & (df["transaccion_id"].astype(str).str.strip() != "")]

    if "categoria" in df.columns:
        df = df[df["categoria"].notna() & (df["categoria"].astype(str).str.strip() != "")]

    return df.reset_index(drop=True)


def ingresos_por_categoria(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega el total de ingresos por categoría, ordenado alfabéticamente."""
    if df.empty:
        return pd.DataFrame(columns=["categoria", "total"])

    resultado = (
        df.groupby("categoria", as_index=False)["total"]
        .sum()
        .sort_values("categoria")
        .reset_index(drop=True)
    )
    return resultado

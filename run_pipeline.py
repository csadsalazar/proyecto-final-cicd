"""CLI del pipeline de ingresos por categoría de TiendaNova."""
import argparse
import json
import os
import sys

import pandas as pd

from src.transform import limpiar_datos, ingresos_por_categoria
from src.validate import validar_entrada, separar_validas


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Pipeline de transacciones de TiendaNova")
    parser.add_argument("--input", required=True, help="Ruta al CSV de transacciones")
    parser.add_argument("--output", required=True, help="Ruta del CSV de ingresos por categoría")
    parser.add_argument(
        "--max-rechazo",
        type=float,
        default=0.15,
        help="Tasa máxima de rechazo tolerada antes de fallar (default: 0.15)",
    )
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    df_crudo = pd.read_csv(args.input)

    try:
        validar_entrada(df_crudo)
    except ValueError as error:
        print(f"ERROR de contrato de entrada: {error}", file=sys.stderr)
        return 1

    df_limpio = limpiar_datos(df_crudo)
    validas, rechazadas = separar_validas(df_limpio)

    filas_entrada = len(df_crudo)
    filas_rechazadas = len(rechazadas)
    tasa_rechazo = filas_rechazadas / filas_entrada if filas_entrada else 0.0

    ingresos = ingresos_por_categoria(validas)

    out_dir = os.path.dirname(args.output) or "."
    os.makedirs(out_dir, exist_ok=True)

    ingresos.to_csv(args.output, index=False)
    rechazadas.to_csv(os.path.join(out_dir, "rechazadas.csv"), index=False)

    resumen = {
        "filas_entrada": filas_entrada,
        "filas_rechazadas": filas_rechazadas,
        "tasa_rechazo": round(tasa_rechazo, 4),
        "categorias_publicadas": ingresos["categoria"].tolist(),
        "ingresos_totales": round(float(ingresos["total"].sum()), 2),
        "ingresos_por_categoria": {
            row["categoria"]: round(float(row["total"]), 2) for _, row in ingresos.iterrows()
        },
    }

    with open(os.path.join(out_dir, "resumen.json"), "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    print(json.dumps(resumen, indent=2, ensure_ascii=False))

    if tasa_rechazo > args.max_rechazo:
        print(
            f"ERROR: tasa de rechazo {tasa_rechazo:.4f} supera el máximo permitido "
            f"{args.max_rechazo:.4f}",
            file=sys.stderr,
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())

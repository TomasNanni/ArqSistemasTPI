import pandas as pd


def sort_csv(input_path, output_path, sort_columns=None):
    """Ordena un archivo CSV usando bubble sort por las columnas indicadas."""
    if sort_columns is None:
        sort_columns = ["PRSUC", "PRCOD", "PRFEC"]

    df = pd.read_csv(input_path).dropna()
    rows = df.to_dict(orient="records")

    length = len(rows)
    for i in range(length):
        for j in range(0, length - i - 1):
            swap = False
            for col in sort_columns:
                if rows[j][col] > rows[j + 1][col]:
                    swap = True
                    break
                elif rows[j][col] < rows[j + 1][col]:
                    break
            if swap:
                rows[j], rows[j + 1] = rows[j + 1], rows[j]

    sorted_df = pd.DataFrame(rows)
    sorted_df.to_csv(output_path, index=False)
    return output_path


if __name__ == "__main__":
    sort_csv(
        "COMPRAS_supermercado_desordenado_solo_sucursal.csv",
        "COMPRAS_supermercado_ordenado.csv",
    )

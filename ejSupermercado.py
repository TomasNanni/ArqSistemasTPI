import pandas as pd
from csvSort import sort_csv


# ── Modelos ───────────────────────────────────────────────────────────────────

class SellerPurchaseLot:
    def __init__(self, product_code, purchase_date, seller, amount, price):
        self.product_code = product_code
        self.purchase_date = purchase_date
        self.seller = seller
        self.amount = amount
        self.price = price


class Product:
    def __init__(self, code, total_price):
        self.code = code
        self.total_price = total_price


# ── Carga y escritura ─────────────────────────────────────────────────────────

def load_data(filepath):
    return pd.read_csv(filepath).dropna()


def write_output(filepath, franchise_count, total_price):
    with open(filepath, "w") as f:
        f.write(f"El supermercado tiene un total de {franchise_count} sucursales\n")
        f.write(f"La compra total en pesos de todas las sucursales es de: ${total_price}\n")


# ── Parseo de filas ───────────────────────────────────────────────────────────

def parse_purchase(row):
    return SellerPurchaseLot(
        product_code=row["PRCOD"], purchase_date=row["PRFEC"],
        seller=row["PRPROV"], amount=int(row["PRCANT"]), price=float(row["PRPRE"])
    )


def row_matches(df, k, product_code, franchise_code):
    return df.iloc[k]["PRCOD"] == product_code and df.iloc[k]["PRSUC"] == franchise_code


# ── Tracking de extremos ──────────────────────────────────────────────────────

def is_new_least(current_price, least_price):
    return (0 < current_price < least_price) or least_price == 0


def is_new_most(current_price, most_price):
    return (current_price > most_price and current_price > 0) or most_price == 0


def update_extremes(code, price, least, most):
    if is_new_least(price, least.total_price):
        least = Product(code, price)
    if is_new_most(price, most.total_price):
        most = Product(code, price)
    return least, most


# ── Nivel producto ────────────────────────────────────────────────────────────

def process_product(df, j, n, franchise_code):
    """Acumula ventas y precio de todas las filas de un producto en una sucursal."""
    product_code = df.iloc[j]["PRCOD"]
    k, sales, price = j, 0, 0.0
    while k < n and row_matches(df, k, product_code, franchise_code):
        p = parse_purchase(df.iloc[k])
        sales += p.amount
        price += p.price
        k += 1
    return k, product_code, sales, price


# ── Nivel sucursal ────────────────────────────────────────────────────────────

def process_franchise(df, start, n, franchise_code):
    """Procesa todos los productos de una sucursal e imprime el detalle por producto."""
    j, total_sales, total_price = start, 0, 0.0
    least, most = Product(0, 0), Product(0, 0)
    while j < n and df.iloc[j]["PRSUC"] == franchise_code:
        j, code, sales, price = process_product(df, j, n, franchise_code)
        total_sales += sales
        total_price += price
        least, most = update_extremes(code, price, least, most)
        print(f"  Producto: {code} | Total ventas: {sales} | Total precio: ${price}")
    return j, total_sales, total_price, least, most


# ── Nivel global ──────────────────────────────────────────────────────────────

def process_all_franchises(df):
    """Itera sobre todas las sucursales, imprime resumen por sucursal y devuelve totales."""
    i, n, count, total_price = 0, len(df), 0, 0.0
    while i < n:
        franchise_code = df.iloc[i]["PRSUC"]
        print(f"\nSucursal: {franchise_code}")
        i, sales, price, least, most = process_franchise(df, i, n, franchise_code)
        print(f"  Total de productos comprados: {sales}")
        print(f"  Producto de mayor compra: {most.code} con importe ${most.total_price}")
        print(f"  Producto de menor compra: {least.code} con importe ${least.total_price}")
        count += 1
        total_price += price
    return count, total_price


# ── Ordenamiento de CSV ───────────────────────────────────────────────────────

def sort_input_file(input_path, output_path):
    """Ordena el archivo de compras antes de procesarlo."""
    return sort_csv(input_path, output_path, ["PRSUC", "PRCOD", "PRFEC"])


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    input_path = "COMPRAS_supermercado(in).csv"
    sorted_path = "COMPRAS_supermercado_ordenado.csv"
    sort_input_file(input_path, sorted_path)

    df = load_data(sorted_path)
    franchise_count, total_price = process_all_franchises(df)
    print(f"\nEl supermercado tiene un total de {franchise_count} sucursales")
    print(f"La compra total en pesos de todas las sucursales es de: ${total_price}")
    write_output("salida.txt", franchise_count, total_price)


if __name__ == "__main__":
    main()
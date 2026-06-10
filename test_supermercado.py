import pytest
import pandas as pd
from unittest.mock import patch, mock_open
from ejSupermercado import (
    SellerPurchaseLot, Product,
    parse_purchase, row_matches,
    is_new_least, is_new_most, update_extremes,
    process_product, process_franchise,
    process_all_franchises, write_output,
)
from csvSort import sort_csv


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_row():
    return {"PRCOD": "A01", "PRFEC": "2024-01-01", "PRPROV": "Proveedor1",
            "PRCANT": "10", "PRPRE": "150.5"}

@pytest.fixture
def sample_df():
    data = {
        "PRSUC": ["S01", "S01", "S01", "S02"],
        "PRCOD": ["P01", "P01", "P02", "P01"],
        "PRFEC": ["2024-01-01"] * 4,
        "PRPROV": ["Prov1"] * 4,
        "PRCANT": [5, 3, 10, 7],
        "PRPRE":  [100.0, 200.0, 50.0, 80.0],
    }
    return pd.DataFrame(data)


# ── parse_purchase ────────────────────────────────────────────────────────────

def test_parse_purchase_returns_correct_types(sample_row):
    p = parse_purchase(sample_row)
    assert isinstance(p.amount, int)
    assert isinstance(p.price, float)

def test_parse_purchase_maps_fields(sample_row):
    p = parse_purchase(sample_row)
    assert p.product_code == "A01"
    assert p.amount == 10
    assert p.price == 150.5
    assert p.seller == "Proveedor1"


# ── row_matches ───────────────────────────────────────────────────────────────

def test_row_matches_returns_true_when_both_match(sample_df):
    assert row_matches(sample_df, 0, "P01", "S01") is True

def test_row_matches_returns_false_on_product_mismatch(sample_df):
    assert row_matches(sample_df, 2, "P01", "S01") is False

def test_row_matches_returns_false_on_franchise_mismatch(sample_df):
    assert row_matches(sample_df, 3, "P01", "S01") is False


# ── is_new_least / is_new_most ────────────────────────────────────────────────

def test_is_new_least_when_baseline_is_zero():
    assert is_new_least(50.0, 0) is True

def test_is_new_least_when_smaller():
    assert is_new_least(30.0, 50.0) is True

def test_is_new_least_when_greater():
    assert is_new_least(60.0, 50.0) is False

def test_is_new_least_ignores_zero_price():
    assert is_new_least(0, 50.0) is False

def test_is_new_most_when_baseline_is_zero():
    assert is_new_most(100.0, 0) is True

def test_is_new_most_when_greater():
    assert is_new_most(200.0, 100.0) is True

def test_is_new_most_when_smaller():
    assert is_new_most(50.0, 100.0) is False


# ── update_extremes ───────────────────────────────────────────────────────────

def test_update_extremes_sets_first_product():
    least, most = update_extremes("P01", 100.0, Product(0, 0), Product(0, 0))
    assert least.code == "P01"
    assert most.code == "P01"

def test_update_extremes_replaces_least():
    least = Product("P01", 100.0)
    most = Product("P01", 100.0)
    least, most = update_extremes("P02", 50.0, least, most)
    assert least.code == "P02"
    assert most.code == "P01"  # sin cambio

def test_update_extremes_replaces_most():
    least = Product("P01", 100.0)
    most = Product("P01", 100.0)
    least, most = update_extremes("P03", 200.0, least, most)
    assert most.code == "P03"
    assert least.code == "P01"  # sin cambio


# ── process_product ───────────────────────────────────────────────────────────

def test_process_product_returns_correct_totals(sample_df):
    k, code, sales, price = process_product(sample_df, 0, len(sample_df), "S01")
    assert code == "P01"
    assert k == 2
    assert sales == 8              # 5 + 3
    assert price == pytest.approx(300.0)  # 100 + 200

def test_process_product_single_row(sample_df):
    k, code, sales, price = process_product(sample_df, 2, len(sample_df), "S01")
    assert code == "P02"
    assert k == 3
    assert sales == 10
    assert price == pytest.approx(50.0)


# ── process_franchise ─────────────────────────────────────────────────────────

def test_process_franchise_sums_all_products(sample_df, capsys):
    j, total_sales, total_price, least, most = process_franchise(
        sample_df, 0, len(sample_df), "S01"
    )
    assert j == 3                         # avanzó hasta la fila de S02
    assert total_sales == 18              # 8 (P01) + 10 (P02)
    assert total_price == pytest.approx(350.0)  # 300 + 50

def test_process_franchise_tracks_most_and_least(sample_df, capsys):
    _, _, _, least, most = process_franchise(sample_df, 0, len(sample_df), "S01")
    assert most.code == "P01"   # precio 300 > 50
    assert least.code == "P02"  # precio 50 < 300


# ── write_output ──────────────────────────────────────────────────────────────

def test_write_output_content():
    m = mock_open()
    with patch("builtins.open", m):
        write_output("/fake/path.txt", 3, 9999.5)
    handle = m()
    written = "".join(call.args[0] for call in handle.write.call_args_list)
    assert "3 sucursales" in written
    assert "$9999.5" in written


def test_sort_csv_creates_ordered_file(tmp_path):
    data = {
        "PRSUC": ["S02", "S01", "S01"],
        "PRCOD": ["P01", "P02", "P01"],
        "PRFEC": ["2024-01-02", "2024-01-01", "2024-01-03"],
        "PRPROV": ["Prov1", "Prov2", "Prov1"],
        "PRCANT": [7, 4, 5],
        "PRPRE": [80.0, 60.0, 100.0],
    }
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.csv"
    pd.DataFrame(data).to_csv(input_path, index=False)

    sort_csv(str(input_path), str(output_path), ["PRSUC", "PRCOD", "PRFEC"])

    result = pd.read_csv(output_path)
    assert list(result["PRSUC"]) == ["S01", "S01", "S02"]
    assert list(result["PRCOD"]) == ["P01", "P02", "P01"]


def test_process_all_franchises_counts_franchises(sample_df):
    count, total_price = process_all_franchises(sample_df)
    assert count == 2
    assert total_price == pytest.approx(430.0)

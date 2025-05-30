import os
import sys
import pytest
import pandas as pd

# Put the src directory on sys.path so we can import diametrics
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from diametrics import transform

# --- open_file shape checks -----------------------------------------------

@pytest.mark.parametrize("path, rows, cols", [
    ("tests/test_data/dexcom/dexcom_eur_01.xlsx", 3866, 20),
    ("tests/test_data/libre/libre_amer_01.csv", 1342, 20),
    ("tests/test_data/example1.csv", 58, 20),
    ("tests/test_data/example1.xlsx", 58, 20),
])
def test_open_file_shape(path, rows, cols):
    df = transform.open_file(path)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (rows, cols)

# --- convert_libre ---------------------------------------------------------

def test_convert_libre_structure_and_values():
    raw = transform.open_file("tests/test_data/libre/libre_amer_02.csv")
    df = transform.convert_libre(raw)
    # Single-file converter should provide these columns
    assert set(df.columns) == {"time", "scan_glc", "glc"}
    # Spot-check glucose values (strings)
    assert df["glc"].head(5).tolist() == [
        '118', '120', '128', '137', '132'
    ]
    # Spot-check timestamps adjusted by 15 min
    times = df["time"].head(3).dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
    assert times == [
        '2021-03-23 03:26:00',
        '2021-03-23 03:41:00',
        '2021-03-23 03:56:00'
    ]

# --- convert_dexcom -------------------------------------------------------

def test_convert_dexcom_structure_and_values():
    raw = transform.open_file("tests/test_data/dexcom/dexcom_eur_02.xlsx")
    df = transform.convert_dexcom(raw)
    # Single-file converter should provide these columns
    assert set(df.columns) == {"time", "glc"}
    # Spot-check glucose values (mmol/L floats)
    assert df["glc"].head(5).tolist() == [
        10.4, 10.3, 10.2, 10.1, 9.9
    ]
    # Spot-check timestamps
    times = df["time"].head(3).dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
    assert times == [
        '2023-03-08 00:00:44',
        '2023-03-08 00:05:44',
        '2023-03-08 00:10:44'
    ]

# --- transform_directory ---------------------------------------------------

@pytest.mark.parametrize("device, expected_cols, expected_rows, expected_cols_count", [
    ("dexcom", ["time", "glc", "ID"], 11531, 3),
    ("libre", ["time", "glc", "scan_glc", "ID"], 2677, 4),
])
def test_transform_directory(device, expected_cols, expected_rows, expected_cols_count):
    path = f"tests/test_data/{device}"
    df = transform.transform_directory(path, device)
    # shape and columns
    assert df.shape == (expected_rows, expected_cols_count)
    assert list(df.columns) == expected_cols

    # Spot-check a slice
    idx = 1620
    slice_glc = df["glc"].iloc[idx:idx+3].tolist()
    slice_time = df["time"].iloc[idx:idx+3].dt.strftime("%Y-%m-%d %H:%M:%S").tolist()
    if device == "dexcom":
        assert slice_glc == [13.8, 13.6, 13.4]
        assert slice_time == [
            '2023-03-13 18:54:12',
            '2023-03-13 18:59:12',
            '2023-03-13 19:04:12'
        ]
    else:
        assert slice_glc == ['109', '108', '112']
        assert slice_time == [
            '2021-03-26 01:41:00',
            '2021-03-26 01:56:00',
            '2021-03-26 02:11:00'
        ]

# --- Smoke tests -----------------------------------------------------------

def test_smoke_convert_functions():
    # Just verify no exceptions for small slices
    raw_libre = transform.open_file("tests/test_data/libre/libre_amer_02.csv").head(5)
    raw_dex = transform.open_file("tests/test_data/dexcom/dexcom_eur_02.xlsx").head(5)
    for fn, raw in [(transform.convert_libre, raw_libre), (transform.convert_dexcom, raw_dex)]:
        out = fn(raw)
        assert isinstance(out, pd.DataFrame)
        assert "time" in out.columns and "glc" in out.columns

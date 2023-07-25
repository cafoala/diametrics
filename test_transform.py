import pandas as pd
import numpy as np
import pytest
# import os library
import sys 
#sys.path.append('..')
from datetime import datetime, timedelta
from src.diametrics import transform

# Test open_file function
def test_open_file():
    # File path
    filepath1 = 'tests/test_data/dexcom/dexcom_eur_01.xlsx'
    filepath2 = 'tests/test_data/libre/libre_amer_01.csv'
    # Read the Excel file
    df1 = transform.open_file(filepath1)
    df2 = transform.open_file(filepath2)
    # Test DataFrame shape
    assert df1.shape == (3866, 20)
    assert df2.shape == (1342, 20)


# Test convert_libre function
def test_convert_libre():
    # File path
    filepath = 'tests/test_data/libre/libre_amer_02.csv' 
    # Open file
    df = transform.open_file(filepath)
    converted = transform.convert_libre(df)
    # Check glc values
    assert converted['glc'].head().tolist() == ['114', '111', '109', '110', '114']
    # Check time values
    assert converted['time'].head().astype(str).tolist()== ['2021-03-23 01:11:00', '2021-03-23 01:26:00', '2021-03-23 01:41:00', '2021-03-23 01:56:00', '2021-03-23 02:11:00']


# Test convert_dexcom function
def test_convert_dexcom():
    # File path
    filepath = 'tests/test_data/dexcom/dexcom_eur_02.xlsx'
    # Open file
    df = transform.open_file(filepath)
    converted = transform.convert_dexcom(df)
    # Check glc values
    assert converted['glc'].head().tolist() == [10.4, 10.3, 10.2, 10.1, 9.9]
    # Check time values
    assert converted['time'].head().astype(str).tolist()== ['2023-03-08 00:00:44', '2023-03-08 00:05:44', '2023-03-08 00:10:44', '2023-03-08 00:15:44', '2023-03-08 00:20:44']


def test_transform_directory():
    # Set filepaths
    filepath1 = 'tests/test_data/dexcom'
    filepath2 = 'tests/test_data/libre'
    
    # Transform directories
    df1 = transform.transform_directory(filepath1, 'dexcom')
    df2 = transform.transform_directory(filepath2, 'libre')
    
    # Test shape
    assert df1.shape == (11531, 3)
    assert df2.shape == (2677, 4)
    
    # Test values
    assert df1.glc.iloc[1620:1625].tolist() == [13.8, 13.6, 13.4, 13.2, 12.8]
    assert df1.time.iloc[1620:1625].astype(str).tolist() == ['2023-03-13 18:54:12', '2023-03-13 18:59:12', '2023-03-13 19:04:12', '2023-03-13 19:09:12', '2023-03-13 19:14:12']
    assert df2.glc.iloc[1620:1625].tolist() == ['158', '159', '161', '166', '169']
    assert df2.time.iloc[1620:1625].astype(str).tolist() == ['2021-03-23 16:08:00', '2021-03-23 16:23:00', '2021-03-23 16:38:00', '2021-03-23 16:53:00', '2021-03-23 17:08:00']


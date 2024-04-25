import pandas as pd
import sys
import os
# Append the directory containing your module to Python's path
sys.path.append(os.path.abspath('../src/'))

from datetime import datetime, timedelta
from diametrics import transform

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


from unittest.mock import patch

def mock_read_csv(filepath):
    return pd.DataFrame({
        'time': ['2023-03-08T00:09:00', '2023-03-08T00:13:59'],
        'glc': [22.3, 22.3]
    })

@patch('pandas.read_csv', side_effect=mock_read_csv)
def test_open_csv_file(mock_read_csv):
    filepath = 'tests/test_data/example1.csv'
    df = transform.open_file(filepath)
    assert isinstance(df, pd.DataFrame)

# Test open_file
def test_open_csv_file():
    # Test reading from a CSV file
    filepath = 'tests/test_data/example1.csv'
    result = transform.open_file(filepath)
    assert isinstance(result, pd.DataFrame)  # Check if the result is a DataFrame
    assert not result.empty  # Ensure the DataFrame is not empty
    assert result.shape[1] == 20  # Assuming your file is expected to have 20 columns
    assert result.shape[0] == 58

def test_open_excel_file():
    # Test reading from an Excel file
    filepath = 'tests/test_data/example1.xlsx'
    result = transform.open_file(filepath)
    assert isinstance(result, pd.DataFrame)  # Check if the result is a DataFrame
    assert not result.empty  # Ensure the DataFrame is not empty
    assert result.shape[1] == 20  # Assuming your file is expected to have 20 columns
    assert result.shape[0] == 58


# Test convert_libre function
def test_convert_libre():
    # File path
    filepath = 'tests/test_data/libre/libre_amer_02.csv' 
    # Open file
    df = transform.open_file(filepath)
    converted = transform.convert_libre(df)
    # Check glc values
    assert converted['glc'].head().tolist() == ['118',
                                                '120',
                                                '128',
                                                '137',
                                                '132'
                                                ]
    # Check time values
    assert converted['time'].head().astype(str).tolist()== ['2021-03-23 03:26:00', '2021-03-23 03:41:00', '2021-03-23 03:56:00', '2021-03-23 04:11:00', '2021-03-23 04:26:00']


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
    print(df1)
    print(df2)
    # Test shape
    assert df1.shape == (11531, 3)
    assert df2.shape == (2677, 4)

    # Test values
    assert list(df1.columns) == ['time', 'glc', 'ID']
    assert df1.glc.iloc[1620:1625].tolist() == [13.8, 13.6, 13.4, 13.2, 12.8]
    assert df1.time.iloc[1620:1625].astype(str).tolist() == ['2023-03-13 18:54:12', '2023-03-13 18:59:12', '2023-03-13 19:04:12', '2023-03-13 19:09:12', '2023-03-13 19:14:12']
    assert list(df2.columns) == ['time', 'glc', 'scan_glc', 'ID']
    assert df2.glc.iloc[1620:1625].tolist() == ['158', '159', '161', '166', '169']
    assert df2.time.iloc[1620:1625].astype(str).tolist() == ['2021-03-23 16:08:00', '2021-03-23 16:23:00', '2021-03-23 16:38:00', '2021-03-23 16:53:00', '2021-03-23 17:08:00']


test_transform_directory()
'''@patch('pandas.read_csv')
def test_transform_directory(mock_read_csv):
    # Setup mock
    mock_read_csv.return_value = pd.DataFrame({
        'time': ['2023-03-13 18:54:12', '2023-03-13 18:59:12'],
        'glc': ['158', '159'],
        'ID': ['1', '2']
    })
    
    # Assuming 'transform_directory' reads a file using 'pd.read_csv'
    df = transform.transform_directory('dummy_path', 'libre')
    
    # Perform your assertions
    assert df.glc.iloc[0:2].tolist() == ['158', '159']'''
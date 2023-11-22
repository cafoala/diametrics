import pandas as pd
import numpy as np
import pytest
# import os library
import sys 
#sys.path.append('..')
from datetime import datetime, timedelta
from src.diametrics import preprocessing

dxcm_dt = ['2023-03-08T00:09:00',
           '2023-03-08T00:13:59', 
           '2023-03-08T00:18:59',
           '2023-03-08T00:23:59',
           '2023-03-08T00:28:59'
           ]

libre_dt = ['03-23-2021 03:41 AM',
            '03-23-2021 03:56 AM',
            '03-23-2021 04:11 AM',
            '03-23-2021 04:26 AM',
            '03-23-2021 04:41 AM',
            '03-23-2021 04:56 AM',
            '03-23-2021 05:11 AM',
            '03-23-2021 05:26 AM',
            ]


def test_check_df():
    # Test case 1: Valid DataFrame
    df = pd.DataFrame({'time': [dxcm_dt[0], dxcm_dt[1], dxcm_dt[2]], 'glc': [100, 120, 80]})
    assert preprocessing.check_df(df) == True

    # Test case 2: Invalid DataFrame (null values in 'time' column)
    df = pd.DataFrame({'time': [libre_dt[0], libre_dt[1], None], 'glc': [100, 120, 80]})
    assert preprocessing.check_df(df) == True

    # Test case 3: Invalid DataFrame (null values in 'glc' column)
    df = pd.DataFrame({'time': [dxcm_dt[0], dxcm_dt[1], dxcm_dt[2]], 'glc': [None, None, None]})
    assert preprocessing.check_df(df) == False

    # Test case 4: Invalid DataFrame (empty)
    df = pd.DataFrame(columns=['time', 'glc'])
    assert preprocessing.check_df(df) == False

    # Test case 5: Invalid input (not a DataFrame)
    not_df = 'This is not a DataFrame'
    with pytest.warns(UserWarning, match='Not a dataframe'):
        assert preprocessing.check_df(not_df) == False


# Test replace_cutoffs function
def test_replace_cutoffs():
    # Create a sample DataFrame
    df_dx = pd.DataFrame({'glc': ['High', 26, 10,'LO', np.nan], 'time': dxcm_dt})
    df_lib = pd.DataFrame({'glc':  ['High', 'Low', 'high', 'low', 'HI', 'LO', 'hi', 'lo'],
                       'time': libre_dt})
    
    # Test removing non-numeric values 
    result = preprocessing.replace_cutoffs(df_dx, remove=True)
    assert result['glc'].tolist() == [26, 10]

    # Test capping with unique cutoffs
    result = preprocessing.replace_cutoffs(df_dx, cap=True, hi_cutoff=27.8, lo_cutoff=2.2)
    assert result['glc'].tolist() == [27.8, 26, 10, 2.2]

    # Test capping at default
    result = preprocessing.replace_cutoffs(df_dx, cap=True)
    assert result['glc'].tolist() == [22.3, 22.3, 10, 2.1]

    # Test all low/high values
    result = preprocessing.replace_cutoffs(df_lib, cap=True)
    assert result['glc'].tolist() == [22.3, 2.1, 22.3, 2.1, 22.3, 2.1, 22.3, 2.1]


def test_fill_missing_data():
    # Create a sample DataFrame with missing data
    df_lib = pd.DataFrame({'time': libre_dt,
                       'glc': [6.3, 6.3, None,  6.5,  np.nan, np.nan, np.nan,6.5]})
    df_lib['time'] = pd.to_datetime(df_lib['time'])
    df_dx = pd.DataFrame({'time': dxcm_dt,
                       'glc': [6.4, 6.5, np.nan, np.nan, 6.3]})
    df_dx['time'] = pd.to_datetime(df_dx['time'], dayfirst=True)

    # Test interpolation using default parameters
    result = preprocessing.fill_missing_data(df_dx)
    expected_values = [6.4, 6.5, 6.5, 6.4, 6.3]
    assert result['glc'].tolist() == expected_values

    # Test interpolation using default parameters
    result = preprocessing.fill_missing_data(df_lib, interval=15, method='linear', limit=30)
    result = result.fillna(-1)
    expected_values = [6.3, 6.3, 6.4, 6.5, -1, -1, -1, 6.5]
    assert result['glc'].tolist() == expected_values

def test_set_time_frame():
    df_lib = pd.DataFrame({'time': libre_dt, 
                           'glc': [6.3, 6.3, 6.4, 6.5,
                                   6.4, 6.3, 6.4, 6.5]})
    df_lib['time'] = pd.to_datetime(df_lib['time'])
    cut_df = preprocessing.set_time_frame(df_lib, ['03-23-2021 04:11 AM', '03-23-2021 05:11 AM'])
    
    assert cut_df['time'].astype(str).tolist() == ['2021-03-23 04:11:00', '2021-03-23 04:26:00',
                                                    '2021-03-23 04:41:00', '2021-03-23 04:56:00'] 
    

# Test detect_units function
def test_detect_units():
    # Sample data
    df1 = pd.DataFrame({'glc': [22.3, 22.3, 10, 2.1]})
    df2 = pd.DataFrame({'glc': [75, 81, 84,np.nan, 86]})
    result1 = preprocessing.detect_units(df1)
    
    # Test for 'mmol/L'
    assert result1 == 'mmol/L'

    # Test for 'mg/dL'
    result2 = preprocessing.detect_units(df2)
    assert result2 == 'mg/dL'

# Test change_units function
def test_change_units():
    # Sample data
    df1 = pd.DataFrame({'glc': [22.3, 22.3, 10, 2.1]})
    df2 = pd.DataFrame({'glc': [75, 81, 84, np.nan, 86]})

    # Test for 'mg/dL' unit
    result1 = preprocessing.change_units(df1)
    expected_values1 = [400, 400, 180, 38]
    assert result1['glc'].tolist() == expected_values1

    # Test for 'mmol/L' unit
    result2 = preprocessing.change_units(df2)
    result2 = result2.fillna(-1)
    expected_values2 = [4.2, 4.5, 4.7, -1, 4.8]
    assert result2['glc'].tolist() == expected_values2
import pandas as pd
import pytest
# import os library
import sys 
#sys.path.append('..')
from datetime import datetime, timedelta

from src.diametrics import preprocessing

def test_check_df():
    # Test case 1: Valid DataFrame
    df = pd.DataFrame({'time': [1, 2, 3], 'glc': [100, 120, 80]})
    assert preprocessing.check_df(df) == True

    # Test case 2: Invalid DataFrame (null values in 'time' column)
    df = pd.DataFrame({'time': [1, 2, None], 'glc': [100, 120, 80]})
    assert preprocessing.check_df(df) == True

    # Test case 3: Invalid DataFrame (null values in 'glc' column)
    df = pd.DataFrame({'time': [1, 2, 3], 'glc': [100, None, 80]})
    assert preprocessing.check_df(df) == True

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
    df = pd.DataFrame({'glc': ['High', 'Low', 10, 'HI', 25, 'NaN'], 'time': pd.date_range(start='2023-06-01', periods=6, freq='15T')})

    # Test removing non-numeric values and capping
    result = preprocessing.replace_cutoffs(df, remove=True, cap=True)
    assert result['glc'].tolist() == [2.1, 2.1, 10, 22.3, 22.3]

    # Test converting 'glc' column to numeric values
    assert result['glc'].dtype == float

    # Test converting 'time' column to datetime
    assert result['time'].dtype == datetime
import pandas as pd
import numpy as np
import pytest
import sys
import os
from diametrics import preprocessing

# --- Fixtures --------------------------------------------------------------

dxcm_dt = [
    '2023-03-08T00:09:00',
    '2023-03-08T00:13:59',
    '2023-03-08T00:18:59',
    '2023-03-08T00:23:59',
    '2023-03-08T00:28:59'
]

libre_dt = [
    '03-23-2021 03:41 AM',
    '03-23-2021 03:56 AM',
    '03-23-2021 04:11 AM',
    '03-23-2021 04:26 AM',
    '03-23-2021 04:41 AM',
    '03-23-2021 04:56 AM',
    '03-23-2021 05:11 AM',
    '03-23-2021 05:26 AM',
]
@pytest.fixture
def dxcm_df():
    df = pd.DataFrame({
        'time': pd.to_datetime(dxcm_dt),
        'glc': [22.3, 22.3, 10.0, 2.1, np.nan]
    })
    return df

def test_check_df():
    # Case 1: valid DataFrame
    df = pd.DataFrame({'time': dxcm_dt[:3], 'glc': [100,120,80]})
    assert preprocessing.check_df(df) is True

    # Case 2: null time but valid glucose
    df = pd.DataFrame({'time': [libre_dt[0], libre_dt[1], None], 'glc': [100,120,80]})
    assert preprocessing.check_df(df) is True

    # Case 3: all glc null
    df = pd.DataFrame({'time': dxcm_dt[:3], 'glc': [None,None,None]})
    assert preprocessing.check_df(df) is False

    # Case 4: empty
    df = pd.DataFrame(columns=['time','glc'])
    assert preprocessing.check_df(df) is False

    # Case 5: not a DataFrame
    with pytest.warns(UserWarning, match='Not a dataframe'):
        assert preprocessing.check_df("foobar") is False


def test_replace_cutoffs():
    # recreate exactly how original test did
    df_dx = pd.DataFrame({
        'glc': ['High', 26, 10, 'LO', np.nan],
        'time': dxcm_dt
    })
    df_lib = pd.DataFrame({
        'glc': ['High','Low','high','low','HI','LO','hi','lo'],
        'time': libre_dt
    })

    # remove non-numeric
    out = preprocessing.replace_cutoffs(df_dx, remove=True)
    assert out['glc'].tolist() == [26, 10]

    # cap with custom cutoffs
    out = preprocessing.replace_cutoffs(df_dx, cap=True, hi_cutoff=27.8, lo_cutoff=2.2)
    assert out['glc'].tolist() == [27.8, 26, 10, 2.2]

    # cap with defaults
    out = preprocessing.replace_cutoffs(df_dx, cap=True)
    assert out['glc'].tolist() == [22.3, 22.3, 10, 2.1]

    # all low/high variants
    out = preprocessing.replace_cutoffs(df_lib, cap=True)
    assert out['glc'].tolist() == [22.3,2.1,22.3,2.1,22.3,2.1,22.3,2.1]


def test_fill_missing_data():
    # dxcm style
    df_dx = pd.DataFrame({
        'time': dxcm_dt,
        'glc': [6.4,6.5,np.nan,np.nan,6.3]
    })
    df_dx['time'] = pd.to_datetime(df_dx['time'])
    out = preprocessing.fill_missing_data(df_dx)
    assert out['glc'].tolist() == [6.4,6.5,6.5,6.4,6.3]

    # libre style
    df_lib = pd.DataFrame({
        'time': libre_dt,
        'glc': [6.3,6.3,None,6.5,np.nan,np.nan,np.nan,6.5]
    })

# --- Structural / Smoke Tests --------------------------------------------
def test_smoke_check_df(dxcm_df):
    assert isinstance(preprocessing.check_df(dxcm_df), bool)

def test_smoke_replace_cutoffs(dxcm_df):
    df = dxcm_df.copy()
    df.loc[1, 'glc'] = 'High'
    out = preprocessing.replace_cutoffs(df, cap=True)
    assert isinstance(out, pd.DataFrame)
    assert 'glc' in out.columns

def test_smoke_fill_missing_data(dxcm_df):
    out = preprocessing.fill_missing_data(dxcm_df)
    assert isinstance(out, pd.DataFrame)
    assert {'time','glc'}.issubset(out.columns)

def test_smoke_set_time_frame(dxcm_df):
    times = dxcm_df['time'].iloc[[0, -1]].astype(str).tolist()
    out = preprocessing.set_time_frame(dxcm_df, times)
    assert isinstance(out, pd.DataFrame)
    assert 'time' in out.columns

def test_smoke_detect_units(dxcm_df):
    units = preprocessing.detect_units(dxcm_df)
    assert isinstance(units, str)
    assert units in {'mmol','mg'}

def test_smoke_change_units(dxcm_df):
    # drop NaNs so change_units can cast to int without failure
    clean = dxcm_df.dropna(subset=['glc']).copy()
    out = preprocessing.change_units(clean)
    assert isinstance(out, pd.DataFrame)
    assert 'glc' in out.columns

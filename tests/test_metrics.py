import pytest
import pandas as pd
import numpy as np
from diametrics import metrics

# --- Fixtures --------------------------------------------------------------

@pytest.fixture
def df1():
    df = pd.DataFrame({
        'time': [
            '2023-03-08T00:09:00',
            '2023-03-08T00:13:59',
            '2023-03-08T00:18:59',
            '2023-03-08T00:23:59',
        ],
        'glc': [22.3, 22.3, 10.0, 2.1]
    })
    df['time'] = pd.to_datetime(df['time'])
    return df

@pytest.fixture
def df2():
    times = [
        '03-23-2021 03:41 AM','03-23-2021 03:56 AM','03-23-2021 04:11 AM',
        '03-23-2021 04:26 AM','03-23-2021 04:41 AM','03-23-2021 04:56 AM',
        '03-23-2021 05:11 AM','03-23-2021 05:26 AM','03-29-2021 03:41 AM',
        '03-29-2021 03:56 AM','03-29-2021 04:11 AM','03-29-2021 04:26 AM',
        '03-29-2021 04:41 AM','03-29-2021 04:56 AM','03-29-2021 05:11 AM',
        '03-29-2021 05:26 AM',
    ]
    glc = [75,81,84,np.nan,86,86,95,110,280,290,300,310,320,320,400,np.nan]
    df = pd.DataFrame({'time': pd.to_datetime(times), 'glc': glc})
    return df

@pytest.fixture
def df3():
    df = pd.read_csv('tests/test_data/example1.csv', dayfirst=True)
    df['time'] = pd.to_datetime(df['time'], dayfirst=True)
    return df

# --- Value Tests for Key Metrics -----------------------------------------

def test_average_glc(df1, df2):
    avg1 = metrics.average_glc(df1)['avg_glc'].iloc[0]
    assert avg1 == pytest.approx(14.175, rel=1e-6)

    avg2 = metrics.average_glc(df2)['avg_glc'].iloc[0]
    assert avg2 == pytest.approx(202.64285714285714, rel=1e-6)

def test_glycemic_variability_cv(df1):
    cv1 = metrics.glycemic_variability(df1)['cv'].iloc[0]
    assert cv1 == pytest.approx(69.9880878924, rel=1e-6)

def test_auc(df1):
    auc1 = metrics.auc(df1)['auc'].iloc[0]
    # trapezoidal average: pairwise means [22.3+22.3, 22.3+10, 10+2.1] /2, then mean
    expected = 0.5 * np.mean([22.3+22.3, 22.3+10, 10+2.1])
    assert auc1 == pytest.approx(expected, rel=1e-6)

def test_mage(df1):
    m1 = metrics.mage(df1)['mage'].iloc[0]
    assert m1 == pytest.approx(20.2, rel=1e-3)

def test_time_in_range_values(df1):
    tir = metrics.time_in_range(df1, units='mmol')
    # it's a Series for single-user
    assert tir['tir_lv2_hypo'] == pytest.approx(25.0, rel=1e-6)
    assert tir['tir_lv2_hyper'] == pytest.approx(50.0, rel=1e-6)

def test_glycemic_episodes_counts(df1):
    episodes = metrics.glycemic_episodes(
        df1, units='mmol',
        hypo_lv1_thresh=3.9, hypo_lv2_thresh=3.0,
        hyper_lv1_thresh=10, hyper_lv2_thresh=13.9
    )
    # single-user returns a Series
    assert episodes['number_lv2_hypos'] == 0
    assert episodes['number_lv2_hypers'] == 0

@pytest.mark.parametrize("units,expected", [
    ('mmol', 3.31 + 0.02392 * (14.175*18.0182)),
    ('mg',   3.31 + 0.02392 * 14.175),
])
def test_gmi(df1, units, expected):
    g = metrics.gmi(df1, units=units)['gmi'].iloc[0]
    assert g == pytest.approx(expected, rel=1e-3)

# --- Multi‐user aggregation spot‐checks -----------------------------------

def test_multi_user_aggregation(df3):
    res = metrics.all_standard_metrics(df3, units='mmol', gap_size=5)
    row = res.set_index('ID').loc[1049]

    # avg_glc ~3.8665
    assert row['avg_glc'] == pytest.approx(3.86653846, rel=1e-6)
    # exactly one hypo
    assert row['number_lv1_hypos'] == 1
    # AUC is roughly ~3.75
    assert row['auc'] == pytest.approx(3.75, rel=1e-2)

# --- Structural / Smoke Tests --------------------------------------------

def test_time_in_range_structure(df1, df2, df3):
    # df1 → Series
    tir1 = metrics.time_in_range(df1, units='mmol')
    assert isinstance(tir1, pd.Series)
    for key in ['tir_normal','tir_lv2_hypo','tir_lv2_hyper']:
        assert key in tir1.index

    # df2 → maybe DataFrame or Series
    tir2 = metrics.time_in_range(df2, units='mg')
    if isinstance(tir2, pd.DataFrame):
        tir2 = tir2.iloc[0]
    assert isinstance(tir2, pd.Series)
    assert 'tir_norm_tight' in tir2.index

    # df3 → DataFrame
    tir3 = metrics.time_in_range(df3, units='mmol')
    assert isinstance(tir3, pd.DataFrame)
    assert 'ID' in tir3.columns

def test_glycemic_risk_index_structure(df1):
    gri_df = metrics.glycemic_risk_index(df1, units='mmol')
    assert isinstance(gri_df, pd.DataFrame)
    # coerce to float
    val = float(gri_df['gri'].iloc[0])
    assert 0.0 <= val <= 100.0

def test_glycemic_episodes_structure(df1):
    out = metrics.glycemic_episodes(
        df1, units='mmol',
        hypo_lv1_thresh=3.9, hypo_lv2_thresh=3.0,
        hyper_lv1_thresh=10, hyper_lv2_thresh=13.9
    )
    # must contain these keys
    keys = ['number_lv1_hypos','number_lv2_hypos','number_lv1_hypers']
    if isinstance(out, pd.Series):
        for k in keys:
            assert k in out.index
    else:
        for k in keys:
            assert k in out.columns

def test_all_standard_metrics_minimal(df1):
    res = metrics.all_standard_metrics(df1, units='mmol', gap_size=5)
    assert isinstance(res, pd.DataFrame)
    assert res.shape[0] == 1
    for col in ['start_dt','avg_glc','sd','tir_normal','gmi']:
        assert col in res.columns

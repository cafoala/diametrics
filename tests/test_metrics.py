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
def df3(tmp_path):
    # load the example1.csv from test_data
    path = tmp_path / "example1.csv"
    # you might copy it there or adjust as needed
    orig = pd.read_csv('tests/test_data/example1.csv')
    orig.to_csv(path, index=False)
    df = pd.read_csv(path, dayfirst=True)
    df['time'] = pd.to_datetime(df['time'], dayfirst=True)
    return df

# --- Tests --------------------------------------------------------------

def test_average_glc(df1, df2, df3):
    # single-user
    avg1 = metrics.average_glc(df1)['avg_glc'].iloc[0]
    assert avg1 == pytest.approx(14.175, rel=1e-6)
    avg2 = metrics.average_glc(df2)['avg_glc'].iloc[0]
    assert avg2 == pytest.approx(202.64285714285714, rel=1e-6)

    # multi-user
    df3_res = metrics.average_glc(df3)
    assert list(df3_res.columns) == ['ID','avg_glc']
    # check one row
    row = df3_res.set_index('ID').loc[1001,'avg_glc']
    assert row == pytest.approx(8.298666666666666, rel=1e-6)

def test_percentiles(df1, df2, df3):
    p1 = metrics.percentiles(df1).iloc[0]
    assert p1['min_glc'] == pytest.approx(2.1)
    assert p1['percentile_50'] == pytest.approx(16.15)

    p2 = metrics.percentiles(df2).iloc[0]
    assert p2['percentile_90'] == pytest.approx(320.0)

    p3 = metrics.percentiles(df3)
    assert set(p3.columns) >= {'ID','min_glc','max_glc','percentile_25'}
    # spot-check one cell
    assert p3.set_index('ID').loc[1049,'percentile_50'] == pytest.approx(2.94)

def test_glycemic_variability(df1, df2, df3):
    v1 = metrics.glycemic_variability(df1).iloc[0]
    assert v1['sd'] == pytest.approx(9.9208114587, rel=1e-6)
    assert v1['cv'] == pytest.approx(69.988087892, rel=1e-6)

    v3 = metrics.glycemic_variability(df3).set_index('ID').loc[2017,'cv']
    assert v3 == pytest.approx(2.388618412, rel=1e-6)

def test_ea1c(df1, df2, df3):
    # mmol
    e1 = metrics.ea1c(df1, units='mmol')['ea1c'].iloc[0]
    assert e1 == pytest.approx((14.175+2.59)/1.59, rel=1e-6)
    # mg (convert internally)
    e2 = metrics.ea1c(df2, units='mg')['ea1c'].iloc[0]
    assert e2 == pytest.approx((202.64285714285714+46.7)/28.7, rel=1e-6)

    # multi-ID
    e3 = metrics.ea1c(df3, units='mmol').set_index('ID').loc[2017,'ea1c']
    assert isinstance(e3, float)

@pytest.mark.parametrize("units,expected_gmi", [
    ('mmol', 3.31 + 0.02392 * (14.175 * 18.0182)),
    ('mg', 3.31 + 0.02392 * 14.175),
])
def test_gmi(df1, units, expected_gmi):
    g = metrics.gmi(df1, units=units)['gmi'].iloc[0]
    assert g == pytest.approx(expected_gmi, rel=1e-3)

def test_auc(df1, df2):
    auc1 = metrics.auc(df1)['auc'].iloc[0]
    # for df1 with four points: avg of pairwise means
    expected1 = 0.5 * np.mean([22.3+22.3,22.3+10,10+2.1])
    assert auc1 == pytest.approx(expected1, rel=1e-6)

    auc2 = metrics.auc(df2)['auc'].iloc[0]
    assert isinstance(auc2, float)

def test_mage(df1):
    m1 = metrics.mage(df1)['mage'].iloc[0]
    # peaks/troughs algorithm gives an average diff ~20.2
    assert m1 == pytest.approx(20.2, rel=1e-3)

def test_time_in_range(df1, df2, df3):
    tir1 = metrics.time_in_range(df1, units='mmol')
    assert set(tir1.index) >= {'tir_normal','tir_lv2_hypo','tir_lv2_hyper'}

    tir2 = metrics.time_in_range(df2, units='mg').iloc[0]
    assert np.isclose(tir2['tir_norm_tight'], 43.75)

def test_glycemic_risk_index(df1):
    gri1 = metrics.glycemic_risk_index(df1, units='mmol')['gri'].iloc[0]
    assert isinstance(gri1, float)
    assert 0 <= gri1 <= 100

def test_glycemic_episodes_structure(df1):
    out = metrics.glycemic_episodes(df1, units='mmol', hypo_lv1_thresh=3.9, hypo_lv2_thresh=3, hyper_lv1_thresh=10, hyper_lv2_thresh=13.9)
    # must have lv1 and lv2 counts
    for k in ['number_lv1_hypos','number_lv2_hypos','number_lv1_hypers']:
        assert k in out.index if out.ndim==1 else k in out.columns

def test_all_standard_metrics_minimal(df1):
    # supply units to avoid ValueError in gmi
    df = df1.copy()
    res = metrics.all_standard_metrics(df, units='mmol', gap_size=5)
    # should return a one-row DataFrame
    assert hasattr(res, 'loc')
    assert res.shape[0] == 1
    # check some expected columns
    assert set(res.columns) >= {'start_dt','avg_glc','sd','tir_normal','gmi'}
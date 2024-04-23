import pandas as pd
import numpy as np
import sys
import os
# Append the directory containing your module to Python's path
sys.path.append(os.path.abspath('../src/'))
from diametrics import metrics

# Data for tests

df1 = pd.DataFrame({'time':['2023-03-08T00:09:00',
                            '2023-03-08T00:13:59', 
                            '2023-03-08T00:18:59',
                            '2023-03-08T00:23:59'],
                    'glc': [22.3, 22.3, 10, 2.1]})
df1['time'] = pd.to_datetime(df1['time'])


df2 = pd.DataFrame({'time':
                            ['03-23-2021 03:41 AM',
                            '03-23-2021 03:56 AM',
                            '03-23-2021 04:11 AM',
                            '03-23-2021 04:26 AM',
                            '03-23-2021 04:41 AM',
                            '03-23-2021 04:56 AM',
                            '03-23-2021 05:11 AM',
                            '03-23-2021 05:26 AM',
                            '03-29-2021 03:41 AM',
                            '03-29-2021 03:56 AM',
                            '03-29-2021 04:11 AM',
                            '03-29-2021 04:26 AM',
                            '03-29-2021 04:41 AM',
                            '03-29-2021 04:56 AM',
                            '03-29-2021 05:11 AM',
                            '03-29-2021 05:26 AM',],
                    'glc': [75, 81, 84, np.nan, 86, 86, 95, 110,
                            280, 290, 300, 310, 320, 320, 400, np.nan]})
df2['time'] = pd.to_datetime(df2['time'])

df3 = pd.read_csv('tests/test_data/example1.csv')
df3['time'] = pd.to_datetime(df3['time'], dayfirst=True)


def test_average_glc():
    assert metrics.average_glc(df1).to_dict() == {'avg_glc': {0: 14.175}}
    assert metrics.average_glc(df2).to_dict() == {'avg_glc': {0: 202.64285714285714}}
    assert metrics.average_glc(df3).to_dict() == {'ID': {0: 1001, 1: 1049, 2: 2017}, 'avg_glc': {0: 8.298666666666666, 1: 3.8665384615384615, 2: 10.450624999999999}}


def test_percentiles():
   # Check that the non-id dfs are producing the correct series
    assert metrics.percentiles(df1).to_dict() == {'min_glc': {0: 2.1}, 'percentile_10': {0: 4.470000000000001}, 'percentile_25': {0: 8.025}, 'percentile_50': {0: 16.15}, 'percentile_75': {0: 22.3}, 'percentile_90': {0: 22.3}, 'max_glc': {0: 22.3}}
    assert metrics.percentiles(df2).to_dict() == {'min_glc': {0: 75.0}, 'percentile_10': {0: 81.9}, 'percentile_25': {0: 86.0}, 'percentile_50': {0: 195.0}, 'percentile_75': {0: 307.5}, 'percentile_90': {0: 320.0}, 'max_glc': {0: 400.0}}

    # Check that the id dfs are producing the correct df
    assert metrics.percentiles(df3).to_dict() == {'ID': {0: 1001, 1: 1049, 2: 2017}, 'min_glc': {0: 7.16, 1: 2.2, 2: 10.11}, 'percentile_10': {0: 7.204, 1: 2.2, 2: 10.14}, 'percentile_25': {0: 7.74, 1: 2.5675, 2: 10.33}, 'percentile_50': {0: 8.16, 1: 2.94, 2: 10.39}, 'percentile_75': {0: 8.96, 1: 3.7175, 2: 10.600000000000001}, 'percentile_90': {0: 9.166, 1: 7.545, 2: 10.83}, 'max_glc': {0: 9.27, 1: 10.54, 2: 10.89}}


def test_glycemic_variability():
    assert metrics.glycemic_variability(df1).to_dict() == {'sd': {0: 9.920811458746709}, 'cv': {0: 69.988087892393}}
    assert metrics.glycemic_variability(df2).to_dict() == {'sd': {0: 122.05333458581327}, 'cv': {0: 60.2307608107644}}
    assert metrics.glycemic_variability(df3).to_dict() == {'ID': {0: 1001, 1: 1049, 2: 2017}, 'sd': {0: 0.7703511876936079, 1: 2.283337806471381, 2: 0.24962555291209024}, 'cv': {0: 9.282830828570148, 1: 59.053797839705474, 2: 2.3886184119331646}}


def test_ea1c():
    assert metrics.ea1c(df1).to_dict() == {'ea1c': {0: 10.544025157232705}}
    assert metrics.ea1c(df1, 'mmol').to_dict() == {'ea1c': {0: 10.544025157232705}}

    assert metrics.ea1c(df2).to_dict() == {'ea1c': {0: 8.687904430064709}}
    assert metrics.ea1c(df2, 'mg').to_dict() == {'ea1c': {0: 8.687904430064709}}

    assert metrics.ea1c(df3).to_dict() == {'ID': {0: 1001, 1: 1049, 2: 2017}, 'ea1c': {0: 6.848218029350104, 1: 4.060716013546202, 2: 8.201650943396226}}


def test_auc():
    assert metrics.auc(df1).to_dict() == {'auc': {0: 14.833333333333334}}
    assert metrics.auc(df2).to_dict() == {'auc': {0: 199.96153846153845}}
    assert metrics.auc(df3).to_dict() == {'ID': {0: 1001, 1: 1049, 2: 2017}, 'auc': {0: 6.831874999999999, 1: 6.831874999999999, 2: 6.831874999999999}}

def test_mage():
    assert metrics.mage(df1).to_dict() == {'mage': {0: 20.2}}
    assert metrics.mage(df2).to_dict() == {'mage': {0: 325.0}}
    assert metrics.mage(df3).to_dict() == {'ID': {0: 1001, 1: 1049, 2: 2017}, 'mage': {0: 1.9399999999999995, 1: 7.539999999999999, 2: 0.7200000000000006}}

def test_time_in_range():
    assert metrics.time_in_range(df1).to_dict() == {'tir_normal': 25.0, 'tir_norm_tight': 0.0, 'tir_lv1_hypo': 0.0, 'tir_lv2_hypo': 25.0, 'tir_lv1_hyper': 0.0, 'tir_lv2_hyper': 50.0}
    assert metrics.time_in_range(df2).to_dict() == {'tir_normal': 43.75, 'tir_norm_tight': 43.75, 'tir_lv1_hypo': 0.0, 'tir_lv2_hypo': 0.0, 'tir_lv1_hyper': 0.0, 'tir_lv2_hyper': 43.75}
    assert metrics.time_in_range(df3).to_dict() == {'ID': {0: 1001, 1: 1049, 2: 2017}, 'tir_normal': {0: 100.0, 1: 23.076923076923077, 2: 0.0}, 'tir_norm_tight': {0: 26.666666666666668, 1: 15.384615384615385, 2: 0.0}, 'tir_lv1_hypo': {0: 0.0, 1: 19.230769230769234, 2: 0.0}, 'tir_lv2_hypo': {0: 0.0, 1: 53.84615384615385, 2: 0.0}, 'tir_lv1_hyper': {0: 0.0, 1: 3.8461538461538463, 2: 100.0}, 'tir_lv2_hyper': {0: 0.0, 1: 0.0, 2: 0.0}}

def test_bgi():
    assert metrics.bgi(df1).to_dict() == {'lbgi': 10.179682586842274, 'hbgi': 30.687883308432397}
    assert metrics.bgi(df2).to_dict() == {'lbgi': 1.3110411478724404, 'hbgi': 18.95927184136593}
    assert metrics.bgi(df3).to_dict() == {'ID': {0: 1001, 1: 1049, 2: 2017}, 'lbgi': {0: 0.0, 1: 18.91588111178242, 2: 0.0}, 'hbgi': {0: 3.0453950982702223, 1: 0.6302309984464775, 2: 9.3347223623822}}

    assert metrics.bgi(df1, 'mmol').to_dict() == {'lbgi': 10.179682586842274, 'hbgi': 30.687883308432397}
    assert metrics.bgi(df2, 'mg').to_dict() == {'lbgi': 1.3110411478724404, 'hbgi': 18.95927184136593}
    assert metrics.bgi(df3, 'mmol').to_dict() == {'ID': {0: 1001, 1: 1049, 2: 2017}, 'lbgi': {0: 0.0, 1: 18.91588111178242, 2: 0.0}, 'hbgi': {0: 3.0453950982702223, 1: 0.6302309984464775, 2: 9.3347223623822}}

def test_data_sufficiency():
    assert metrics.data_sufficiency(df1, gap_size=5).to_dict() == {'start_dt': '2023-03-08 00:09:00', 'end_dt': '2023-03-08 00:24:00', 'num_days': 0.010405092592592593, 'data_sufficiency': 100}
    assert metrics.data_sufficiency(df2, gap_size=15).to_dict() == {'start_dt': '2021-03-23 03:41:00', 'end_dt': '2021-03-29 05:26:00', 'num_days': 6.072916666666667, 'data_sufficiency': 2.4}
    assert metrics.data_sufficiency(df3, gap_size=5).to_dict() == {'ID': {0: 1001, 1: 1049, 2: 2017}, 'start_dt': {0: '2018-01-09 01:30:00', 1: '2018-04-06 12:17:00', 2: '2018-11-14 06:12:00'}, 'end_dt': {0: '2018-01-09 02:40:00', 1: '2018-04-06 14:22:00', 2: '2018-11-14 07:27:00'}, 'num_days': {0: 0.04861111111111111, 1: 0.08680555555555555, 2: 0.052083333333333336}, 'data_sufficiency': {0: 100, 1: 100, 2: 100}}


def test_glycemic_episodes():
    assert metrics.glycemic_episodes(df1).to_dict() == {'number_hypos': 0, 'number_lv2_hypos': 0, 'number_prolonged_hypos': 0, 'avg_length_hypos': 0, 'total_time_in_hypo': 0, 'number_hypers': 0, 'number_lv2_hypers': 0, 'number_prolonged_hypers': 0, 'avg_length_hypers': 0, 'total_time_in_hyper': 0}
    assert metrics.glycemic_episodes(df2).to_dict() == {'number_hypos': 0, 'number_lv2_hypos': 0, 'number_prolonged_hypos': 0, 'avg_length_hypos': 0, 'total_time_in_hypo': 0, 'number_hypers': 1, 'number_lv2_hypers': 1, 'number_prolonged_hypers': 0, 'avg_length_hypers': '0 days 01:30:00', 'total_time_in_hyper': '0 days 01:30:00'}
    assert metrics.glycemic_episodes(df3).to_dict() == {'number_hypos': {1001: 0, 1049: 1, 2017: 0}, 'number_lv2_hypos': {1001: 0, 1049: 1, 2017: 0}, 'number_prolonged_hypos': {1001: 0, 1049: 0, 2017: 0}, 'avg_length_hypos': {1001: 0, 1049: '0 days 01:35:00', 2017: 0}, 'total_time_in_hypo': {1001: 0, 1049: '0 days 01:35:00', 2017: 0}, 'number_hypers': {1001: 0, 1049: 0, 2017: 1}, 'number_lv2_hypers': {1001: 0, 1049: 0, 2017: 0}, 'number_prolonged_hypers': {1001: 0, 1049: 0, 2017: 0}, 'avg_length_hypers': {1001: 0, 1049: 0, 2017: '0 days 01:15:00'}, 'total_time_in_hyper': {1001: 0, 1049: 0, 2017: '0 days 01:15:00'}}

    # Changing the thresholds
    assert metrics.glycemic_episodes(df3, hypo_lv1_thresh=5, hypo_lv2_thresh=3.9, hyper_lv1_thresh=13.9, hyper_lv2_thresh=15,).to_dict() == {'number_hypos': {1001: 0, 1049: 1, 2017: 0}, 'number_lv2_hypos': {1001: 0, 1049: 1, 2017: 0}, 'number_prolonged_hypos': {1001: 0, 1049: 0, 2017: 0}, 'avg_length_hypos': {1001: 0, 1049: '0 days 01:45:00', 2017: 0}, 'total_time_in_hypo': {1001: 0, 1049: '0 days 01:45:00', 2017: 0}, 'number_hypers': {1001: 0, 1049: 0, 2017: 0}, 'number_lv2_hypers': {1001: 0, 1049: 0, 2017: 0}, 'number_prolonged_hypers': {1001: 0, 1049: 0, 2017: 0}, 'avg_length_hypers': {1001: 0, 1049: 0, 2017: 0}, 'total_time_in_hyper': {1001: 0, 1049: 0, 2017: 0}}
    # Changing the prolonged mins
    assert metrics.glycemic_episodes(df2, long_mins=45).to_dict() == {'number_hypos': 0, 'number_lv2_hypos': 0, 'number_prolonged_hypos': 0, 'avg_length_hypos': 0, 'total_time_in_hypo': 0, 'number_hypers': 1, 'number_lv2_hypers': 1, 'number_prolonged_hypers': 1, 'avg_length_hypers': '0 days 01:30:00', 'total_time_in_hyper': '0 days 01:30:00'}
    # Changing the mins
    assert metrics.glycemic_episodes(df2, mins=30).to_dict() == {'number_hypos': 0, 'number_lv2_hypos': 0, 'number_prolonged_hypos': 0, 'avg_length_hypos': 0, 'total_time_in_hypo': 0, 'number_hypers': 1, 'number_lv2_hypers': 1, 'number_prolonged_hypers': 0, 'avg_length_hypers': '0 days 01:30:00', 'total_time_in_hyper': '0 days 01:30:00'}


def test_all_metrics():
    assert metrics.all_standard_metrics(df1, gap_size=5).to_dict() == {'start_dt': {0: '2023-03-08 00:09:00'}, 'end_dt': {0: '2023-03-08 00:24:00'}, 'num_days': {0: 0.010405092592592593}, 'data_sufficiency': {0: 100}, 'avg_glc': {0: 14.175}, 'ea1c': {0: 10.544025157232705}, 'sd': {0: 9.920811458746709}, 'cv': {0: 69.988087892393}, 'auc': {0: 14.833333333333334}, 'lbgi': {0: 10.179682586842274}, 'hbgi': {0: 30.687883308432397}, 'mage': {0: 20.2}, 'tir_normal': {0: 25.0}, 'tir_norm_tight': {0: 0.0}, 'tir_lv1_hypo': {0: 0.0}, 'tir_lv2_hypo': {0: 25.0}, 'tir_lv1_hyper': {0: 0.0}, 'tir_lv2_hyper': {0: 50.0}, 'number_hypos': {0: 0}, 'number_lv2_hypos': {0: 0}, 'number_prolonged_hypos': {0: 0}, 'avg_length_hypos': {0: 0}, 'total_time_in_hypo': {0: 0}, 'number_hypers': {0: 0}, 'number_lv2_hypers': {0: 0}, 'number_prolonged_hypers': {0: 0}, 'avg_length_hypers': {0: 0}, 'total_time_in_hyper': {0: 0}}
    assert metrics.all_standard_metrics(df2, gap_size=15).to_dict() == {'start_dt': {0: '2021-03-23 03:41:00'}, 'end_dt': {0: '2021-03-29 05:11:00'}, 'num_days': {0: 6.0625}, 'data_sufficiency': {0: 2.4}, 'avg_glc': {0: 202.64285714285714}, 'ea1c': {0: 8.687904430064709}, 'sd': {0: 122.05333458581327}, 'cv': {0: 60.2307608107644}, 'auc': {0: 199.96153846153845}, 'lbgi': {0: 1.3110411478724404}, 'hbgi': {0: 18.959271841365926}, 'mage': {0: 325.0}, 'tir_normal': {0: 50.0}, 'tir_norm_tight': {0: 50.0}, 'tir_lv1_hypo': {0: 0.0}, 'tir_lv2_hypo': {0: 0.0}, 'tir_lv1_hyper': {0: 0.0}, 'tir_lv2_hyper': {0: 50.0}, 'number_hypos': {0: 0}, 'number_lv2_hypos': {0: 0}, 'number_prolonged_hypos': {0: 0}, 'avg_length_hypos': {0: 0}, 'total_time_in_hypo': {0: 0}, 'number_hypers': {0: 1}, 'number_lv2_hypers': {0: 1}, 'number_prolonged_hypers': {0: 0}, 'avg_length_hypers': {0: '0 days 01:30:00'}, 'total_time_in_hyper': {0: '0 days 01:30:00'}}
    assert metrics.all_standard_metrics(df3, gap_size=5).to_dict() == {'ID': {0: 1001, 1: 1049, 2: 2017}, 'start_dt': {0: '2018-01-09 01:30:00', 1: '2018-04-06 12:17:00', 2: '2018-11-14 06:12:00'}, 'end_dt': {0: '2018-01-09 02:40:00', 1: '2018-04-06 14:22:00', 2: '2018-11-14 07:27:00'}, 'num_days': {0: 0.04861111111111111, 1: 0.08680555555555555, 2: 0.052083333333333336}, 'data_sufficiency': {0: 100, 1: 100, 2: 100}, 'avg_glc': {0: 8.298666666666666, 1: 3.8665384615384615, 2: 10.450624999999999}, 'ea1c': {0: 6.848218029350104, 1: 4.060716013546202, 2: 8.201650943396226}, 'sd': {0: 0.7703511876936079, 1: 2.283337806471381, 2: 0.24962555291209024}, 'cv': {0: 9.282830828570148, 1: 59.053797839705474, 2: 2.3886184119331646}, 'auc': {0: 8.310714285714285, 1: 3.7503999999999995, 2: 10.44533333333333}, 'lbgi': {0: 0.0, 1: 18.91588111178242, 2: 0.0}, 'hbgi': {0: 3.0453950982702223, 1: 0.6302309984464775, 2: 9.3347223623822}, 'mage': {0: 1.9399999999999995, 1: 7.539999999999999, 2: 0.7200000000000006}, 'tir_normal': {0: 100.0, 1: 23.076923076923077, 2: 0.0}, 'tir_norm_tight': {0: 26.666666666666668, 1: 15.384615384615385, 2: 0.0}, 'tir_lv1_hypo': {0: 0.0, 1: 19.230769230769234, 2: 0.0}, 'tir_lv2_hypo': {0: 0.0, 1: 53.84615384615385, 2: 0.0}, 'tir_lv1_hyper': {0: 0.0, 1: 3.8461538461538463, 2: 100.0}, 'tir_lv2_hyper': {0: 0.0, 1: 0.0, 2: 0.0}, 'number_hypos': {0: 0, 1: 1, 2: 0}, 'number_lv2_hypos': {0: 0, 1: 1, 2: 0}, 'number_prolonged_hypos': {0: 0, 1: 0, 2: 0}, 'avg_length_hypos': {0: 0, 1: '0 days 01:35:00', 2: 0}, 'total_time_in_hypo': {0: 0, 1: '0 days 01:35:00', 2: 0}, 'number_hypers': {0: 0, 1: 0, 2: 1}, 'number_lv2_hypers': {0: 0, 1: 0, 2: 0}, 'number_prolonged_hypers': {0: 0, 1: 0, 2: 0}, 'avg_length_hypers': {0: 0, 1: 0, 2: '0 days 01:15:00'}, 'total_time_in_hyper': {0: 0, 1: 0, 2: '0 days 01:15:00'}}

    assert metrics.all_standard_metrics(df3, units='mmol', gap_size=5, lv1_hypo=5, lv2_hypo=3.9, lv1_hyper=13.9, lv2_hyper=15, event_mins=30, event_long_mins=45).to_dict() == {'ID': {0: 1001, 1: 1049, 2: 2017}, 'start_dt': {0: '2018-01-09 01:30:00', 1: '2018-04-06 12:17:00', 2: '2018-11-14 06:12:00'}, 'end_dt': {0: '2018-01-09 02:40:00', 1: '2018-04-06 14:22:00', 2: '2018-11-14 07:27:00'}, 'num_days': {0: 0.04861111111111111, 1: 0.08680555555555555, 2: 0.052083333333333336}, 'data_sufficiency': {0: 100, 1: 100, 2: 100}, 'avg_glc': {0: 8.298666666666666, 1: 3.8665384615384615, 2: 10.450624999999999}, 'ea1c': {0: 6.848218029350104, 1: 4.060716013546202, 2: 8.201650943396226}, 'sd': {0: 0.7703511876936079, 1: 2.283337806471381, 2: 0.24962555291209024}, 'cv': {0: 9.282830828570148, 1: 59.053797839705474, 2: 2.3886184119331646}, 'auc': {0: 8.310714285714285, 1: 3.7503999999999995, 2: 10.44533333333333}, 'lbgi': {0: 0.0, 1: 18.91588111178242, 2: 0.0}, 'hbgi': {0: 3.0453950982702223, 1: 0.6302309984464775, 2: 9.3347223623822}, 'mage': {0: 1.9399999999999995, 1: 7.539999999999999, 2: 0.7200000000000006}, 'tir_normal': {0: 100.0, 1: 23.076923076923077, 2: 0.0}, 'tir_norm_tight': {0: 26.666666666666668, 1: 15.384615384615385, 2: 0.0}, 'tir_lv1_hypo': {0: 0.0, 1: 19.230769230769234, 2: 0.0}, 'tir_lv2_hypo': {0: 0.0, 1: 53.84615384615385, 2: 0.0}, 'tir_lv1_hyper': {0: 0.0, 1: 3.8461538461538463, 2: 100.0}, 'tir_lv2_hyper': {0: 0.0, 1: 0.0, 2: 0.0}, 'number_hypos': {0: 0, 1: 1, 2: 0}, 'number_lv2_hypos': {0: 0, 1: 1, 2: 0}, 'number_prolonged_hypos': {0: 0, 1: 1, 2: 0}, 'avg_length_hypos': {0: 0, 1: '0 days 01:40:00', 2: 0}, 'total_time_in_hypo': {0: 0, 1: '0 days 01:40:00', 2: 0}, 'number_hypers': {0: 0, 1: 0, 2: 0}, 'number_lv2_hypers': {0: 0, 1: 0, 2: 0}, 'number_prolonged_hypers': {0: 0, 1: 0, 2: 0}, 'avg_length_hypers': {0: 0, 1: 0, 2: 0}, 'total_time_in_hyper': {0: 0, 1: 0, 2: 0}}

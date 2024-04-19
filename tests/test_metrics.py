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

df3 = pd.read_csv('test_data/example1.csv')


def test_average_glc():
    assert metrics.average_glc(df1) == {'Average glucose (mmol/L)': 14.175}
    assert metrics.average_glc(df2) == {'Average glucose (mg/dL)': 202.64285714285714}
    assert metrics.average_glc(df3).ID.tolist() == [1001, 1049, 2017]
    assert metrics.average_glc(df3)['Average glucose (mmol/L)'].tolist() == [8.298666666666666, 3.8665384615384615, 10.450624999999999]


def test_percentiles():
    # Check that the non-id dfs are producing the correct dictionary
    assert metrics.percentiles(df1) == {'Min. glucose': 2.1, '10th percentile': 4.470000000000001, '25th percentile': 8.025, '50th percentile': 16.15, '75th percentile': 22.3, '90th percentile': 22.3, 'Max. glucose': 22.3}
    assert metrics.percentiles(df2) == {'Min. glucose': 75.0, '10th percentile': 81.9, '25th percentile': 86.0, '50th percentile': 195.0, '75th percentile': 307.5, '90th percentile': 320.0, 'Max. glucose': 400.0}
    
    # Check that the id dfs are producing the correct df
    perc_d3 = metrics.percentiles(df3)
    assert perc_d3['ID'].tolist() == [1001, 1049, 2017]
    assert perc_d3['90th percentile'].tolist() == [9.166, 7.545, 10.83]
    assert perc_d3['50th percentile'].tolist() == [8.16, 2.94, 10.39]


def test_glycemic_variability():
    assert metrics.glycemic_variability(df1) == {'SD (mmol/L)': 9.920811458746709, 'CV (%)': 69.988087892393}
    assert metrics.glycemic_variability(df2) == {'SD (mg/dL)': 122.05333458581327, 'CV (%)': 60.2307608107644}
    
    glyc_var_d3 = metrics.glycemic_variability(df3)
    assert glyc_var_d3['ID'].tolist() == [1001, 1049, 2017]

    assert metrics.glycemic_variability(df3)['SD (mmol/L)'].to_list() == [0.7703511876936079, 2.283337806471381, 0.24962555291209024]
    assert metrics.glycemic_variability(df3)['CV (%)'].to_list() == [9.282830828570148, 59.053797839705474, 2.3886184119331646]

    

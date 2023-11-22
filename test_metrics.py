import pandas as pd
import numpy as np
import pytest
# import os library
import sys 
#sys.path.append('..')
from datetime import datetime, timedelta
from src.diametrics import metrics

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
                            280, 290 , 300, 310, 320, 320, 400, np.nan]})

df3 = pd.read_csv('tests/test_data/example1.csv')

def test_check_df():
    df_empty = pd.DataFrame({'time':['2023-03-08T00:09:00',
                            '2023-03-08T00:13:59', 
                            '2023-03-08T00:18:59',
                            '2023-03-08T00:23:59'],
                    'glc': [np.nan]*4})
    assert metrics.check_df(df1) == True
    assert metrics.check_df(np.nan) == False
    assert metrics.check_df(df_empty) == False


def test_average_glc():
    assert metrics.average_glc(df1) == {'Average glucose (mmol/L)': 14.175}
    assert metrics.average_glc(df2) == {'Average glucose (mg/dL)': 202.64285714285714}
    assert metrics.average_glc(df3).ID.tolist() == [1001, 1049, 2017]
    assert metrics.average_glc(df3)['Average glucose (mmol/L)'].tolist() == [8.298666666666666, 3.8665384615384615, 10.450624999999999]


def test_percentiles():
    print(metrics.percentiles(df1))
    print(metrics.percentiles(df2))
    print(metrics.percentiles(df3))
    assert metrics.percentiles(df1) == {'Average glucose (mmol/L)': 14.175}
    assert metrics.percentiles(df2) == {'Average glucose (mg/dL)': 202.64285714285714}
    #assert metrics.percentiles(df3).ID.tolist() == [1001, 1049, 2017]
    #assert metrics.percentiles(df3)['Average glucose (mmol/L)'].tolist() == [8.298666666666666, 3.8665384615384615, 10.450624999999999]

test_percentiles()
import pandas as pd
import numpy as np
import sys
import os
# Append the directory containing your module to Python's path
sys.path.append(os.path.abspath('../src/'))
from diametrics import visualizations

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

df3 = pd.read_csv('test_data/example1.csv')
df3['time'] = pd.to_datetime(df3['time'], dayfirst=True)

print(visualizations.agp(df1))
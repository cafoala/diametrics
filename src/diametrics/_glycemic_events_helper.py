import pandas as pd
from datetime import timedelta
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def calc_diff(group):
    row1 = group.iloc[0].copy()
    endtime = group.iloc[-1]['time_rep']
    starttime = row1['time_rep']
    diff = endtime-starttime
    row1['diff'] = diff
    return row1

def collapse_bool_array(df, bool_array):
    unique_num = bool_array.ne(bool_array.shift()).cumsum()
    number_consec = unique_num.map(unique_num.value_counts()).where(bool_array)
    df_unique = pd.DataFrame({'time_rep': df['time'], 'glc_rep':
                            df['glc'], 'unique_number': unique_num,
                            'consec_readings': number_consec})
    df_unique['time_rep'] = pd.to_datetime(df_unique['time_rep'])
    # Drop any null glucose readings and reset index
    df_unique.dropna(subset=['glc_rep'], inplace=True)
    df_unique.reset_index(inplace=True, drop=True)
    diff = df_unique.groupby('unique_number').apply((lambda group: calc_diff(group)), include_groups=False)
    diff = diff.drop(columns=['glc_rep'])#.reset_index()
    return diff

def calc_duration(unique_min, mins):
    # Only keep hypos that are 15 mins or longer (smaller than this doesn't count)
    results = unique_min[unique_min['diff'] >= timedelta(minutes=mins)].copy()

    # Fill the consec readings with binary value to show whether they are hypos or
    # the periods between hypos
    results['consec_readings'] = results['consec_readings'].fillna(-1)
    results['event'] = results['consec_readings'] > 0

    # Merge any consecutive values left by removal of too-short episodes using
    # a new unique number
    results['unique'] = results['event'].ne(results['event'].shift()).cumsum()
    return results

def merge_events(results, mins):
    # Group by the unique number, select the min values and select relevant columns
    results_grouped = results.groupby('unique').min()[['time_rep',  'event', 'diff']].copy() #'glc_rep',
    results_grouped['diff2'] = results_grouped['time_rep'].diff().shift(-1)
    # Drop the non-hypo periods and then drop the hypo column
    final_results = results_grouped.loc[results_grouped['event'] ==
                                        True].drop(columns=['event'])
                                        # Rename columns
    final_results.columns = ['start_time',  'initial_duration', 'duration'] # 'min_glc',

    # Fill final hypo with previous duration value in diff col then drop initial
    # duration
    final_results['duration'] = final_results['duration'].fillna(final_results['initial_duration'])
    final_results.drop(columns=['initial_duration'], inplace=True)
    # Drop the final column if it's less than 15 mins
    final_results = final_results.loc[final_results['duration']>=
                                        timedelta(minutes=mins)]
    final_results['end_time'] = final_results['start_time'] + final_results['duration']
    # Reset index
    final_results.reset_index(drop=True, inplace=True)
    return final_results


def calculate_episodes(df, hypo, thresh, thresh_lv2, mins, long_mins):
    if hypo:
        bool_array_lv1 = df['glc'] < thresh
        bool_array_lv2 = df['glc'] < thresh_lv2
    else:
        bool_array_lv1 = df['glc'] > thresh
        bool_array_lv2 = df['glc'] > thresh_lv2

    # Level 1 events
    unique_min_lv1 = collapse_bool_array(df, bool_array_lv1)
    results_lv1 = calc_duration(unique_min_lv1, mins)
    final_results_lv1 = merge_events(results_lv1, mins)
    number_of_lv1 = final_results_lv1.shape[0]

    # Level 2 events
    unique_min_lv2 = collapse_bool_array(df, bool_array_lv2)
    results_lv2 = calc_duration(unique_min_lv2, mins)
    final_results_lv2 = merge_events(results_lv2, mins)
    number_of_lv2 = final_results_lv2.shape[0]

    # Prolonged events
    if hypo:
        number_extended = (final_results_lv1['duration'] >= timedelta(minutes=long_mins)).sum()
    else:
        number_extended = (final_results_lv2['duration'] >= timedelta(minutes=long_mins)).sum()
    print(f'Number of level 1 events: {number_of_lv1}, number of level 2 events: {number_of_lv2}, number of prolonged events: {number_extended}')
    return number_of_lv1, number_of_lv2, number_extended
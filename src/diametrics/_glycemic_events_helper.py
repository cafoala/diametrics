import pandas as pd
from datetime import timedelta
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def calc_diff(group):
    """
    Calculate the duration (difference) between the first and last timestamp within a group.

    Parameters:
        group (pd.DataFrame): Group of rows with timestamps.

    Returns:
        pd.Series: The first row of the group with an added 'diff' column indicating the time difference.
    """
    row1 = group.iloc[0].copy()
    endtime = group.iloc[-1]['time_rep']
    starttime = row1['time_rep']
    diff = endtime - starttime
    row1['diff'] = diff
    return row1

def collapse_bool_array(df, bool_array):
    """
    Collapse consecutive boolean array values, marking unique episodes and counting consecutive readings.

    Parameters:
        df (pd.DataFrame): DataFrame containing 'time' and 'glc' columns.
        bool_array (pd.Series): Boolean series indicating episodes (True) or non-episodes (False).

    Returns:
        pd.DataFrame: DataFrame with unique episodes and consecutive reading counts.
    """
    unique_num = bool_array.ne(bool_array.shift()).cumsum()
    number_consec = unique_num.map(unique_num.value_counts()).where(bool_array)

    df_unique = pd.DataFrame({
        'time_rep': df['time'],
        'glc_rep': df['glc'],
        'unique_number': unique_num,
        'consec_readings': number_consec
    })
    df_unique['time_rep'] = pd.to_datetime(df_unique['time_rep'])

    # Remove null glucose readings and reset index
    df_unique.dropna(subset=['glc_rep'], inplace=True)
    df_unique.reset_index(inplace=True, drop=True)

    diff = df_unique.groupby('unique_number').apply(lambda group: calc_diff(group), include_groups=False)
    diff = diff.drop(columns=['glc_rep'])

    return diff

def calc_duration(unique_min, mins):
    """
    Filter episodes based on a minimum duration.

    Parameters:
        unique_min (pd.DataFrame): DataFrame with unique episodes and their durations.
        mins (int): Minimum duration (in minutes) for episodes to be valid.

    Returns:
        pd.DataFrame: Filtered episodes with durations greater than or equal to the minimum.
    """
    results = unique_min[unique_min['diff'] >= timedelta(minutes=mins)].copy()
    results['consec_readings'] = results['consec_readings'].fillna(-1)
    results['event'] = results['consec_readings'] > 0

    results['unique'] = results['event'].ne(results['event'].shift()).cumsum()

    return results

def merge_events(results, mins):
    """
    Merge consecutive valid events and finalize event timings.

    Parameters:
        results (pd.DataFrame): DataFrame containing episode markers and durations.
        mins (int): Minimum duration threshold for event filtering.

    Returns:
        pd.DataFrame: Finalized DataFrame with start, end times, and durations of episodes.
    """
    results_grouped = results.groupby('unique').min()[['time_rep', 'event', 'diff']].copy()
    results_grouped['diff2'] = results_grouped['time_rep'].diff().shift(-1)

    # Keep only event periods
    final_results = results_grouped.loc[results_grouped['event'] == True].drop(columns=['event'])
    final_results.columns = ['start_time', 'initial_duration', 'duration']

    # Set duration for the last event
    final_results['duration'] = final_results['duration'].fillna(final_results['initial_duration'])
    final_results.drop(columns=['initial_duration'], inplace=True)

    # Remove events shorter than minimum duration
    final_results = final_results.loc[final_results['duration'] >= timedelta(minutes=mins)]
    final_results['end_time'] = final_results['start_time'] + final_results['duration']
    final_results.reset_index(drop=True, inplace=True)

    return final_results

def calculate_episodes(df, hypo, thresh, thresh_lv2, mins, long_mins):
    """
    Calculate and count the number of level 1, level 2, and prolonged glycemic episodes.

    Parameters:
        df (pd.DataFrame): DataFrame with glucose ('glc') readings and timestamps ('time').
        hypo (bool): True if analyzing hypoglycemic episodes; False for hyperglycemic.
        thresh (float): Threshold value for level 1 episodes.
        thresh_lv2 (float): Threshold value for level 2 episodes.
        mins (int): Minimum duration (in minutes) to qualify as an episode.
        long_mins (int): Duration threshold for episodes to qualify as prolonged.

    Returns:
        tuple: Counts of (level 1 episodes, level 2 episodes, prolonged episodes).
    """
    # Create boolean arrays based on thresholds
    if hypo:
        bool_array_lv1 = df['glc'] < thresh
        bool_array_lv2 = df['glc'] < thresh_lv2
    else:
        bool_array_lv1 = df['glc'] > thresh
        bool_array_lv2 = df['glc'] > thresh_lv2

    # Level 1 episode calculations
    unique_min_lv1 = collapse_bool_array(df, bool_array_lv1)
    results_lv1 = calc_duration(unique_min_lv1, mins)
    final_results_lv1 = merge_events(results_lv1, mins)
    number_of_lv1 = final_results_lv1.shape[0]

    # Level 2 episode calculations
    unique_min_lv2 = collapse_bool_array(df, bool_array_lv2)
    results_lv2 = calc_duration(unique_min_lv2, mins)
    final_results_lv2 = merge_events(results_lv2, mins)
    number_of_lv2 = final_results_lv2.shape[0]

    # Prolonged episode calculations
    if hypo:
        number_extended = (final_results_lv1['duration'] >= timedelta(minutes=long_mins)).sum()
    else:
        number_extended = (final_results_lv2['duration'] >= timedelta(minutes=long_mins)).sum()

    return number_of_lv1, number_of_lv2, number_extended

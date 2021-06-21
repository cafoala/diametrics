import copy
import pandas as pd
import numpy as np
import scipy
import warnings
from datetime import timedelta as time

warnings.filterwarnings('ignore')

fift_mins = time(minutes=15)
thirt_mins = time(minutes=30)


def tir_helper(series):
    """
    Helper function for time in range calculation with normal thresholds. Calculates the percentage of readings within
    each threshold by dividing number of readings within range by total length of series
    """
    df_len = series.size
    tir_hypo = series.loc[series < 3.9].size * 100 / df_len

    tir_lv1_hypo = (series.loc[(series < 3.9) & (series >= 3)]).size * 100 / df_len

    tir_lv2_hypo = series.loc[series < 3].size * 100 / df_len

    tir_norm = (series.loc[(series >= 3.9) & (series <= 10)]).size * 100 / df_len

    tir_hyper = series.loc[series > 10].size * 100 / df_len

    tir_lv1_hyper = (series.loc[(series <= 13.9) & (series > 10)]).size * 100 / df_len

    tir_lv2_hyper = series.loc[series > 13.9].size * 100 / df_len

    return [tir_lv2_hypo, tir_lv1_hypo, tir_hypo, tir_norm, tir_hyper, tir_lv1_hyper, tir_lv2_hyper]


def tir_exercise(series):
    """
    Helper function for time in range calculation with exercise thresholds. Same process as function above.
    """
    df_len = series.size
    tir_hypo_ex = series.loc[series < 7].size * 100 / df_len

    tir_norm_ex = (series.loc[(series >= 7) & (series <= 15)]).size * 100 / df_len

    tir_hyper_ex = series.loc[series > 15].size * 100 / df_len

    return [tir_hypo_ex, tir_norm_ex, tir_hyper_ex]


def helper_hypo_episodes(df, breakdown, gap_size, interpolate, interp_method, exercise):
    """
    Helper function for hypoglycemic_episodes.
    """
    # Setting a copy so the df isn't altered in the following forloop
    df = copy.copy(df)
    # Convert time column to datetime and sort by time then reset index
    df['time'] = pd.to_datetime(df['time'])
    df.sort_values('time', inplace=True)
    df.reset_index(drop=True)

    # Calls the interpolate function if interpolate==True
    if interpolate:
        df.set_index('time', inplace=True)
        df = df.resample(rule='min', origin='start').asfreq()
        df['glc'] = df['glc'].interpolate(method=interp_method, limit_area='inside',
                                          limit_direction='forward', limit=fill_gap_size)
        df.reset_index(inplace=True)

    # set a boolean array where glc goes below 3.9, unless exercise thresholds are set then it's 7
    if exercise:
        bool_array = df.glc < 7
    else:
        bool_array = df.glc < 3.9
    # gives a consecutive unique number to every bout below 3.9
    unique_consec_number = bool_array.ne(bool_array.shift()).cumsum()
    # the number of consecutive readings below 3.9
    number_consec_readings = unique_consec_number.map(unique_consec_number.value_counts()).where(bool_array)
    # set up a df using these values to identify each bout of hypogylcaemia
    df_full = pd.DataFrame({'time': df.time, 'glc': df.glc,
                            'unique_number': unique_consec_number,
                            'consec_readings': number_consec_readings})
    # drop nulls and reset index to only get bouts below 3.9 in df
    df_full.dropna(inplace=True)
    df_full.reset_index(inplace=True, drop=True)
    # create 2 new columns which will be used to identify the lowest reading in the bout (low)
    # and lv2 to identify whether the bout was a lv2 hypo
    df_full['low'] = np.nan
    df_full['lv2'] = np.nan
    # loop through all of the unique numbers that signify the bouts to calculate the low value
    # and whether it was a lv2 hypo
    for num in set(df_full.unique_number.values):
        # set the values of low at the unique number equal to the min glc for that bout
        df_full['low'].iloc[df_full[df_full['unique_number'] == num].index] = df_full[
            df_full['unique_number'] == num].glc.min()
        # calculate whether the bout was a lv_2 hypo by calling the lv2_calc function
        lv2 = lv2_calc(df_full[df_full['unique_number'] == num])
        # set the lv2 column equal to the boolean value
        df_full['lv2'].iloc[df_full[df_full['unique_number'] == num].index] = lv2

    list_results = []
    for num in set(df_full['unique_number'].values):
        # print(num)
        sub_df = df_full[df_full['unique_number'] == num]
        sub_df.sort_values('time', inplace=True)
        sub_df.reset_index(inplace=True)

        start_time = sub_df['time'].iloc[0]
        end_time = sub_df['time'].iloc[-1]
        low = sub_df['low'].iloc[0]
        lv2 = sub_df['lv2'].iloc[0]

        list_results.append([start_time, end_time, low, lv2])

    df_start_end = pd.DataFrame(list_results, columns=['start', 'end', 'low', 'lv2'])
    df_start_end.sort_values('start', inplace=True)
    df_start_end.reset_index(inplace=True, drop=True)

    # this section confirms whether the episode is actually a hypo and joins other
    # hypos that are less than 15 mins apart
    hypos_list = []
    i = 0
    # use a while loop to go through every hypo
    while i < df_start_end.shape[0]:
        row = df_start_end.iloc[i]
        diff = row.end - row.start
        # only considered a hypo if the duration of hypo is >= 15 mins
        # if it's longer than 15 mins, allocate the variables to equal the row
        if (diff >= time(minutes=15)) & (diff > time(0)):
            start = row.start
            end = row.end
            low = row.low
            lv2 = row.lv2

            # before entering this section, check that there's at least 2 entries left to compare
            if i < df_start_end.shape[0] - 1:
                # loops through remaining hypos, connecting it to the current hypo if they are less than 15 min apart
                for n in range(1, df_start_end.shape[0] - i):
                    nxt_row = df_start_end.iloc[i + n]
                    # the difference between hypos is less than 15 mins + 2 * time interval between readings
                    # end of the hypo is changed to end of next row, low is made lowest of both
                    # and lv2 is true if either one is true
                    if nxt_row.start - end < time(minutes=15 + 2 * gap_size):  #
                        end = nxt_row.end
                        if low > nxt_row.low:
                            low = nxt_row.low
                        if nxt_row.lv2:
                            lv2 = True
                        # if it's the last entry, there'll be nothing to compare to so add the results to the list here
                        # before the while loop is stopped with the n+1 line
                        if n + i == df_start_end.shape[0] - 1:
                            hypos_list.append([start, end, low, lv2])
                            i += n + 1

                    else:
                        # if there isn't a hypo within 15 mins of this hypo, add the results to the list
                        # increase i by as many iterations (n) of the forloop that have run
                        # break the forloop to move on to next hypo
                        hypos_list.append([start, end, low, lv2])
                        i += n
                        break
            # this is the last hypo in the df, so no need to check if there's another hypo 15 mins apart
            # but hypo is over 15 mins so gets added to the results list
            else:
                hypos_list.append([start, end, low, lv2])
                i += 1
        # hypo is shorter than 15 mins so it doesn't get added to the results list
        else:
            i += 1

    # convert the results list into a dataframe
    results = pd.DataFrame(hypos_list, columns=['start_time', 'end_time', 'low', 'lv2']).reset_index(drop=True)

    # calculate overview statistics, number of hypos, avg length of hypos, number lv2 hypos
    duration = results.end_time - results.start_time
    number_hypos = results.shape[0]
    avg_length = duration.mean()
    total_time_hypo = duration.sum()
    number_lv2_hypos = results[results['lv2']].shape[0]

    # if breakdown hasn't been selected, return overview statistics
    if not breakdown:
        return pd.DataFrame([[number_hypos, avg_length, total_time_hypo, number_lv2_hypos]],
                            columns=['number hypos', 'avg length', 'total time in hypo', 'number lv2 hypos'])

    # if breakdown has been selected, gives a breakdown of all the hypoglycaemic episodes start and finish time
    else:
        return results


def lv2_calc(df):
    """
    Determines whether a hypoglycaemic episode is a level 2 hypoglycaemic episode. Lv2 is when glc drops below
    3.0mmol/L for at least 15 consecutive mins
    """
    # lv2 is false unless proven otherwise
    lv2 = False
    # gives a unique number to all episodes where glc drops below 3
    bool_array = df.glc < 3
    unique_consec_number = bool_array.ne(bool_array.shift()).cumsum()
    number_consec_values = unique_consec_number.map(unique_consec_number.value_counts()).where(bool_array)
    df_comb = pd.DataFrame({'time': df.time, 'unique_lv2': unique_consec_number,
                            'consec_readings': number_consec_values, 'glc': df.glc})
    df_comb.dropna(inplace=True)

    # loop through all of these bouts below 3 and see if any last at least 15 mins, if so lv2 = True
    for num in set(df_comb['unique_lv2'].values):
        sub_df = df_comb[df_comb['unique_lv2'] == num]
        sub_df.sort_values('time', inplace=True)
        sub_df.reset_index(inplace=True)

        start_time = sub_df['time'].iloc[0]
        end_time = sub_df['time'].iloc[-1]
        if end_time - start_time >= time(minutes=15):
            lv2 = True

    return lv2


def helper_missing(df, gap_size, start_time, end_time):
    """
    Helper for percent_missing function
    """
    # dropping nulls in glc
    df = df.dropna(subset=['glc'])

    # create dataframe if start & end times are given
    if (start_time is not None) & (end_time is not None):
        cut_df = df[(df['time'] >= start_time) & (df['time'] <= end_time)]
        non_null = cut_df.glc.count()
        total = (end_time - start_time) / gap_size
        perc_missing = ((total - non_null) * 100) / total

    # calculate the missing data based on start and end of df
    else:
        start_time = df.time.iloc[0]
        end_time = df.time.iloc[-1]
        series = df.set_index('time')
        non_null = series.shape[0]
        # use resampling to calculate total number of points
        resampled_series = series.resample(rule='min', origin='start').asfreq()
        total = (resampled_series.shape[0] + gap_size - 1) / gap_size
        # perc missing is nulls/total
        perc_missing = (total - non_null) * 100 / total
    return [perc_missing, start_time, end_time, str(gap_size) + ' mins']

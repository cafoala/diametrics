import copy
import pandas as pd
import numpy as np
import scipy
from scipy import signal
import warnings
from datetime import timedelta
import statistics
from sklearn.metrics import auc

fift_mins = timedelta(minutes=15)
thirt_mins = timedelta(minutes=30)


def check_df(df):
    '''
    Check if the file given is a valid dataframe
    '''
    if not isinstance(df, pd.DataFrame):
        # I want to return this info to user somehow??
        warnings.warn('Not a dataframe')
        return False
    else:
        # drop any null values in the glc column
        df = df.dropna(subset=['time', 'glc'])
        if df.empty:
            warnings.warn('Empty dataframe')
            return False
        else:
            return True


def auc_helper(dataframe, time, glc):
    return auc(dataframe[time], dataframe[glc])

def mage_helper(dataframe, time, glc):
    '''
    Calculates the mage using Scipy's signal class
    '''
    # Find peaks and troughs using scipy signal
    peaks, properties = signal.find_peaks(dataframe[glc], prominence=dataframe[glc].std())
    troughs, properties = signal.find_peaks(-dataframe[glc], prominence=dataframe[glc].std())
    # Create dataframe with peaks and troughs in order
    single_indexes = dataframe.iloc[np.concatenate((peaks, troughs, [0, -1]))]
    single_indexes.sort_values(time, inplace=True)
    # Make a difference column between the peaks and troughs
    single_indexes['diff'] = single_indexes[glc].diff()
    # Calculate the positive and negative mage and mean
    mage_positive = single_indexes[single_indexes['diff'] > 0]['diff'].mean()
    mage_negative = single_indexes[single_indexes['diff'] < 0]['diff'].mean()
    if pd.notnull(mage_positive) & pd.notnull(mage_negative):
        mage_mean = statistics.mean([mage_positive, abs(mage_negative)])
    elif pd.notnull(mage_positive):
        mage_mean = mage_positive
    elif pd.notnull(mage_negative):
        mage_mean = abs(mage_negative)
    else:
        mage_mean = 0  # np.nan
    return pd.DataFrame([[mage_mean]], columns=['mage_mean'])

def convert_to_rounded_percent(value, length):
    return round(value * 100 / length, 2)

def tir_helper(series):
    """
    Helper function for time in range calculation with normal thresholds. Calculates the percentage of readings within
    each threshold by divSiding number of readings within range by total length of series
    """
    df_len = series.size
    tir_hypo = convert_to_rounded_percent(series.loc[series < 3.9].size, df_len)

    tir_lv1_hypo = convert_to_rounded_percent(series.loc[(series < 3.9) & (series >= 3)].size, df_len)

    tir_lv2_hypo = convert_to_rounded_percent(series.loc[series < 3].size, df_len)

    tir_norm = convert_to_rounded_percent(series.loc[(series >= 3.9) & (series <= 10)].size, df_len)
    
    tir_hyper = convert_to_rounded_percent(series.loc[series > 10].size, df_len)

    tir_lv1_hyper = convert_to_rounded_percent(series.loc[(series <= 13.9) & (series > 10)].size, df_len)

    tir_lv2_hyper = convert_to_rounded_percent(series.loc[series > 13.9].size, df_len)
    '''
    tir_norm_1 = (series.loc[(series >= 3.9) & (series <= 7.8)]).size, df_len)

    tir_norm_2 = (series.loc[(series >= 7.8) & (series <= 10)]).size, df_len)
    
    tir_hypo_ex = series.loc[series < 5].size, df_len)

    tir_norm_ex = (series.loc[(series >= 5) & (series <= 15)]).size, df_len)

    tir_hyper_ex = series.loc[series > 15].size, df_len)
    '''
    return [tir_norm, tir_hypo, tir_lv1_hypo, tir_lv2_hypo, tir_hyper, tir_lv1_hyper, tir_lv2_hyper]

def number_of_hypos(df, time='time', glc='glc'):
    '''
    Replacement helper for number of hypos
    '''
    # Set the time column to datetime and sort by it
    df['time'] = pd.to_datetime(df['time'])
    df.sort_values('time', inplace=True)

    # Gives a consecutive unique number to each set of consecutive readings below
    # 3.9mmol/L
    bool_array = df['glc'] < 3.9
    unique_num = bool_array.ne(bool_array.shift()).cumsum()
    number_consec = unique_num.map(unique_num.value_counts()).where(bool_array)
    df_unique = pd.DataFrame({'time_rep': df['time'], 'glc_rep':
                            df['glc'], 'unique_number_low': unique_num,
                            'consec_readings_low': number_consec})

    # Drop any null glucose readings and reset index
    df_unique.dropna(subset=['glc_rep'], inplace=True)
    df_unique.reset_index(inplace=True, drop=True)

    # Group by the unique number to collapse into episodes, then use min to
    # calculate the minimum glucose for each bout and the start time
    unique_min = df_unique.groupby('unique_number_low').min()

    # Use the start time of bouts and periods between bouts to calculate duration
    # of episodes
    unique_min['diff'] = unique_min.time_rep.diff().shift(-1)

    # Only keep hypos that are 15 mins or longer (smaller than this doesn't count)
    results = unique_min[unique_min['diff'] >= timedelta(minutes=15)]

    # Fill the consec readings with binary value to show whether they are hypos or
    # the periods between hypos
    results.consec_readings_low = results.consec_readings_low.fillna(-1)
    results['hypo'] = results['consec_readings_low'] > 0

    # Merge any consecutive values left by removal of too-short episodes using
    # a new unique number
    results['unique'] = results['hypo'].ne(results['hypo'].shift()).cumsum()

    # Group by the unique number, select the min values and select relevant columns
    final_results = results.groupby('unique').min()[['time_rep', 'glc_rep', 'hypo', 'diff']]

    # Calculate difference between hypo and non-hypo periods and shift column up to
    # get the final duration of the periods
    final_results['diff2'] = final_results['time_rep'].diff().shift(-1)

    # Drop the non-hypo periods and then drop the hypo column
    final_results = final_results.loc[final_results['hypo'] ==
                                      True].drop(columns=['hypo'])

    # Rename columns
    final_results.columns = ['start_time', 'min_glc', 'initial_duration', 'duration']

    # Fill final hypo with previous duration value in diff col then drop initial
    # duration
    finaL_results = final_results['duration'].fillna(final_results['initial_duration'])
    final_results.drop(columns=['initial_duration'], inplace=True)
    final_results.reset_index(drop=True, inplace=True)
    # Drop the final column if it's less than 15 mins
    final_results = final_results.loc[final_results['duration']>=
                                      timedelta(minutes=15)]

    # Create new column identifying if the hypo is level 2 (<3mmol/L)
    final_results['lv2'] = final_results['min_glc'] < 3
    
    # Reset index
    final_results.reset_index(drop=True, inplace=True)
    
    # Calculate overview statistics
    number_hypos = final_results.shape[0]
    avg_length = final_results.duration.mean().round('1s')
    total_time_hypo = final_results.duration.sum()
    
    # Return 0s if no hypos and nan if something weird happens
    if pd.notnull(avg_length):
        avg_length = avg_length#.total_seconds() / 60
        total_time_hypo = total_time_hypo#.total_seconds() / 60
    elif number_hypos == 0:
        avg_length = 0
        total_time_hypo = 0
    else:
        avg_length = np.nan
        total_time_hypo = np.nan
        
    # Divide total hypos into number of level 1 and level 2 hypos
    number_lv2_hypos = final_results[final_results['lv2']].shape[0]
    number_lv1_hypos = number_hypos - number_lv2_hypos
    
    # Save as dataframe and return
    frame = pd.DataFrame([[number_hypos, number_lv1_hypos, number_lv2_hypos,
                           avg_length, total_time_hypo]],
                         columns=['number_hypos','number_lv1_hypos',
                                  'number_lv2_hypos', 'avg_length_of_hypo',
                                  'total_time_in_hypos'])
    
    return frame

def helper_hypo_episodes(df, time, glc, breakdown, gap_size, interpolate, interp_method, exercise):
    """
    Helper function for hypoglycemic_episodes.
    """
    # Setting a copy so the df isn't altered in the following forloop
    df = copy.copy(df)
    # Convert time column to datetime and sort by time then reset index
    df[time] = pd.to_datetime(df[time])
    df.sort_values(time, inplace=True)
    df.reset_index(drop=True)

    # Calls the interpolate function if interpolate==True
    if interpolate:
        df.set_index(time, inplace=True)
        df = df.resample(rule='min', origin='start').asfreq()
        df[glc] = df[glc].interpolate(method=interp_method, limit_area='inside',
                                      limit_direction='forward', limit=gap_size)
        df.reset_index(inplace=True)
        gap_size = 1

    # set a boolean array where glc goes below 3.9, unless exercise thresholds are set then it's 7
    if exercise:
        bool_array = df[glc] < 7
    else:
        bool_array = df[glc] < 3.9
    # gives a consecutive unique number to every bout below 3.9
    unique_consec_number = bool_array.ne(bool_array.shift()).cumsum()
    # the number of consecutive readings below 3.9
    number_consec_readings = unique_consec_number.map(unique_consec_number.value_counts()).where(bool_array)
    # set up a df using these values to identify each bout of hypogylcaemia
    df_full = pd.DataFrame({'time_rep': df[time], 'glc_rep': df[glc],
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
            df_full['unique_number'] == num]['glc_rep'].min()
        # calculate whether the bout was a lv_2 hypo by calling the lv2_calc function
        lv2 = lv2_calc(df_full[df_full['unique_number'] == num], 'time_rep', 'glc_rep')
        # set the lv2 column equal to the boolean value
        df_full['lv2'].iloc[df_full[df_full['unique_number'] == num].index] = lv2

    list_results = []
    for num in set(df_full['unique_number'].values):
        # print(num)
        sub_df = df_full[df_full['unique_number'] == num]
        sub_df.sort_values('time_rep', inplace=True)
        sub_df.reset_index(inplace=True)

        start_time = sub_df['time_rep'].iloc[0]
        end_time = sub_df['time_rep'].iloc[-1]
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
        if (diff >= timedelta(minutes=15)) & (diff > timedelta(0)):
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
                    if nxt_row.start - end < timedelta(minutes=(6 - gap_size / 5) * gap_size):  #
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
    if pd.notnull(avg_length):
        avg_length = avg_length.total_seconds() / 60
        total_time_hypo = total_time_hypo.total_seconds() / 60
    elif number_hypos == 0:
        avg_length = 0
        total_time_hypo = 0
    else:
        avg_length = np.nan
        total_time_hypo = np.nan

    number_lv2_hypos = results[results['lv2']].shape[0]
    number_lv1_hypos = number_hypos - number_lv2_hypos

    # if breakdown hasn't been selected, return overview statistics
    if not breakdown:
        return pd.DataFrame([[number_hypos, avg_length, total_time_hypo, number_lv1_hypos, number_lv2_hypos]],
                            columns=['number_hypos', 'avg_length_of_hypo', 'total_time_in_hypos', 'number_lv1_hypos',
                                     'number_lv2_hypos'])

    # if breakdown has been selected, gives a breakdown of all the hypoglycaemic episodes start and finish time
    else:
        return results


def lv2_calc(df, time, glc):
    """
    Determines whether a hypoglycaemic episode is a level 2 hypoglycaemic
    episode. Lv2 is when glc drops below 3.0mmol/L for at least 15 consecutive 
    mins
   
    """
    # lv2 is false unless proven otherwise
    lv2 = False
    # gives a unique number to all episodes where glc drops below 3
    bool_array = df[glc] < 3
    unique_consec_number = bool_array.ne(bool_array.shift()).cumsum()
    number_consec_values = unique_consec_number.map(unique_consec_number.value_counts()).where(bool_array)
    df_comb = pd.DataFrame({'time_rep': df[time], 'unique_lv2': unique_consec_number,
                            'consec_readings': number_consec_values, 'glc_rep': df[glc]})
    df_comb.dropna(inplace=True)

    # loop through all of these bouts below 3 and see if any last at least 15 mins, if so lv2 = True
    for num in set(df_comb['unique_lv2'].values):
        sub_df = df_comb[df_comb['unique_lv2'] == num]
        sub_df.sort_values('time_rep', inplace=True)
        sub_df.reset_index(inplace=True)

        start_time = sub_df[time].iloc[0]
        end_time = sub_df[time].iloc[-1]
        if end_time - start_time >= timedelta(minutes=15):
            lv2 = True

    return lv2


def helper_missing(df, time, glc, gap_size, start_time, end_time):
    """
    Helper for percent_missing function
    """
    # dropping nulls in glc and time and returning 100% missing if df is empty
    df = df.dropna(subset=[glc, time]).sort_values(time)
    if df.empty:
        return 100

    # calculate the missing data based on start and end of df
    if start_time is None:
        start_time = df[time].iloc[0]
    if end_time is None:
        end_time = df[time].iloc[-1]

    # calculate the number of non-null values
    cut_df = df.loc[(df[time] >= start_time) & (df[time] <= end_time)]
    # print(cut_df)
    if gap_size == 5:
        freq = '5min'
    else:
        freq = '15min'
    number_readings = sum(cut_df.set_index(time).groupby(pd.Grouper(freq=freq)).count()[glc] > 0)
    time_diff = (end_time - start_time)
    total_readings = time_diff.total_seconds() / (60 * gap_size)
    if number_readings >= total_readings:
        perc_missing = 0
    else:
        perc_missing = (total_readings - number_readings) * 100 / total_readings
    '''
    df_resampled = cut_df.drop_duplicates(subset='time').set_index('time').resample(rule='min', origin='start').asfreq()
    df_resampled['interp'] = df_resampled[glc].interpolate(method='zero', limit_area='inside',
                                                           limit_direction='forward', limit=gap_size)
    #df_resampled = df_resampled.append([df_resampled.iloc[-1]]*(gap_size-1), ignore_index=True)
    #df_resampled = df_resampled[:-1] #.drop(index=df_resampled.iloc[-1].index, inplace=True)
    total_readings = df_resampled.shape[0] #cut_df.shape[0]
    non_null = df_resampled.dropna(subset=['interp']).shape[0]
    #non_null = df_resampled.loc[pd.notnull(df_resampled['interp'])].shape[0]
    print(df_resampled)
    print(non_null)
    #non_null = cut_df.shape[0]
    # calculate number of total readings
    #total_minutes = (end_time - start_time).total_seconds()/60
    #total_readings = 1+total_minutes/gap_size
    #print(total_readings)
    
    if (total_readings == 0) | (non_null == 0):
        return 100
    nulls = total_readings-non_null
    
    perc_missing = 100*nulls/total_readings
    '''
    if perc_missing > 100:
        perc_missing = 100
    return perc_missing

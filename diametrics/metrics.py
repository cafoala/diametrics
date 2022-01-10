#!/usr/bin/env python
# coding: utf-8
import pandas as pd
import numpy as np
import scipy
from functools import reduce
import helper
import warnings
from datetime import timedelta as time

# warnings are the worst
warnings.filterwarnings('ignore')

# setting up some regularly used timedeltas
fift_mins = time(minutes=15)
thirt_mins = time(minutes=30)


def all_metrics(df, time='time', glc='glc', ID=None, interval_size=5, start_time=None, end_time=None, by_day=False,
                exercise_thresholds=False):
    """
    Calculates all available CGM metrics in one go. Time in range, hypoglycemic episodes, average glucose, glycemic
    variability and ea1c.

    :param df: Pandas DataFrame
        Glucose monitor time series, must contain columns titled 'time' and 'glc', 'ID' optional

    :param time: String
        Name of columns with time data

    :param glc : String
        Name of column with glucose data

    :param ID : String
        Name of column with patient ID (optional)

    :param start_time: Timedelta
        Start of time-period (optional)

    :param start_time: Timedelta
        End of time-period (optional)

    :param interval_size: Int
        The length of time between glucose readings

    :param by_day: Bool
        Gives a breakdown of all metrics by day

    :param exercise_thresholds: Bool
        Sets the thresholds for time in range to exercise, <7 for hypoglycemia and >15 for hyperglycemia

    :return: Pandas DataFrame
        Contains all of the metric columns along with ID and exercise_thresholds if selected
    """
    df.dropna(subset=[time, glc], inplace=True)
    df.sort_values(time, inplace=True)

    df[time] = pd.to_datetime(df[time])

    id_bool = ID is not None
    if df.empty & id_bool:
        return pd.DataFrame([[np.nan]*20 + [100]], columns =
                                      ['ID', 'TIR_lv2_hypo', 'TIR_lv1_hypo',
                                       'TIR_hypo', 'TIR_norm', 'TIR_hyper',
                                       'TIR_lv1_hyper', 'TIR_lv2_hyper',
                                       'number_hypos', 'avg_length_of_hypo',
                                       'total_time_in_hypos',
                                       'number_lv1_hypos', 'number_lv2_hypos',
                                      'sd', 'cv', 'minimum_glucose',
                                      'maximum_glucose', 'average_glucose',
                                      'mage_mean', 'ea1c', 'percent_missing'])
    elif df.empty & (not id_bool):
        return pd.DataFrame([[np.nan]*19 + [100]],
                            columns = ['TIR_lv2_hypo', 'TIR_lv1_hypo', 'TIR_hypo', 'TIR_norm',
       'TIR_hyper', 'TIR_lv1_hyper', 'TIR_lv2_hyper', 'number_hypos',
       'avg_length_of_hypo', 'total_time_in_hypos', 'number_lv1_hypos',
       'number_lv2_hypos', 'sd', 'cv', 'minimum_glucose', 'maximum_glucose',
       'average_glucose', 'mage_mean', 'ea1c', 'percent_missing'])
    # by_day_id = True
    # if by_day breakdown selected, add the date to id
    if by_day & id_bool:
        df[ID] = df[ID].astype(str) + '$' + df[time].dt.date.astype(str)
    elif by_day:
        df[ID] = df[time].dt.date.astype(str)
        id_bool = True
        # by_day_id = False

    # calls all of functions in the package
    tir = time_in_range(df, glc, ID)
    glc_var = glycemic_variability(df, glc, ID)
    mage_results = mage(df, time, glc, ID)
    avg = average_glucose(df, glc, ID)
    ea1c_val = ea1c(df, glc, ID)
    hypos = hypoglycemic_episodes(df, time, glc, ID, interval_size=interval_size)
    perc_missing = percent_missing(df, time=time, glc=glc, ID=ID, interval_size=interval_size,
                                   start_datetime=start_time, end_datetime=end_time)

    # if exercise_thresholds are True, calculate time in range and number of hypoglycemic episodes for exercise
    if exercise_thresholds:
        tir_ex = time_in_range(df, glc, ID, exercise_thresholds=True)
        hypos_ex = hypoglycemic_episodes(df, time, glc, ID, interval_size=interval_size, exercise_thresholds=True)
        # dataframes to concatenate
        data_frames = [tir, tir_ex, hypos, hypos_ex, glc_var, avg, mage_results, ea1c_val, perc_missing]

    else:
        data_frames = [tir, hypos, glc_var, avg, mage_results, ea1c_val, perc_missing]
    # If ID column is present, merge all of the dataframes on ID
    if id_bool:
        df_merged = reduce(lambda left, right: pd.merge(left, right, on=['ID'],
                                                        how='outer'), data_frames)
        if by_day:
            df_merged[[ID, 'date']] = df_merged[ID].str.split('$', n=1, expand=True)
            df_merged[ID] = df_merged[ID].astype(df[ID].dtype)
        else:
            df_merged.rename({ID: 'date'})
    else:
        df_merged = pd.concat(data_frames)

    return df_merged


def mage(df, time='time', glc='glc', ID=None):
    """
    Calculate the mage - positive, negative and mean, , can be used on a dataset from a single person or combined dataset
    with IDs present df has to be have timestamp and glucose columns

    Parameters
    ----------
    df : Pandas DataFrame
        Glucose monitor time series, must contain columns titled 'time' and 'glc', 'ID' optional

    glc : String
        Name of column with glucose data

    time : String
        Name of column with time data

    ID : String
        Name of column with patient ID (optional)
    """
    # Drop null values and raise exception if df is then empty
    df.dropna(subset=[time, glc], inplace=True)
    df = df.loc[:,[ID, time, glc]]
    df.columns = ['ID', time, glc]
    '''if df.empty:
        raise Exception('Empty dataframe')'''
    # Make time into datetime format and sort by it
    df[time] = pd.to_datetime(df[time])
    df.sort_values(time, inplace=True)
    # Call the mage_helper function for all IDs with groupby
    if ID is not None:
        results = df.groupby('ID').apply(lambda group: helper.mage_helper(group, time, glc)).reset_index().drop(
            columns='level_1')
    # Call mage_helper for just the 1 ID
    else:
        results = helper.mage_helper(df, time)
    return results


def time_in_range(df, glc='glc', ID=None, exercise_thresholds=False):
    """
    Calculates the time in range for various set ranges option to select exercise thresholds which are
    different to regular thresholds, can be used on a dataset from a single person or combined dataset
    with IDs present df has to be have 'time' (timestamp) and 'glc' (glucose) columns

    Parameters
    ----------
    df : Pandas DataFrame
        Glucose monitor time series, must contain columns titled 'time' and 'glc', 'ID' optional

    glc : String
        Name of column with glucose data

    ID : String
        Name of column with patient ID (optional)

    exercise_thresholds : Bool
        Sets the thresholds for time in range to exercise, <7 for hypoglycemia and >15 for hyperglycemia


    Returns
    -------
    Pandas DataFrame.
        Returned results contain the time in hypoglycemia (level 1 and level 2 if exercise_threshold=False),
        time in normal range, time in hyperglycemSia (if exercise_threshold=False). If ID column is provided
        this will contain results for each ID.

    """
    # create a list to add the results to
    list_results = []
    # drop any null values in the glc column
    df = df.dropna(subset=[glc])
    # calculate the total number of readings
    df_len = df.shape[0]

    # check that there's readings in the df
    if df_len == 0:
        warnings.warn('Empty dataframe')
        # Throw some kind of error!!!???

    # if the df has an id column
    if ID is not None:
        # exercise thresholds aren't selected
        # loop through all of the IDs making slice of dataframe then run through the tir_helper function
        # tir_helper is in helper.py
        # add the resulting list to the results along with the ID, convert to dataframe and return

        if not exercise_thresholds:
            for id_var in set(df[ID].values):
                id_glc = df.loc[df[ID] == id_var][glc]
                ranges = helper.tir_helper(id_glc)
                ranges.insert(0, id_var)
                list_results.append(ranges)
            results = pd.DataFrame(list_results, columns=['ID', 'TIR_lv2_hypo', 'TIR_lv1_hypo', 'TIR_hypo', 'TIR_norm',
                                                          'TIR_hyper', 'TIR_lv1_hyper', 'TIR_lv2_hyper'])
        # exercise thresholds are selected
        # same as above but uses tir_exercise function with different thresholds
        else:
            for id_var in set(df[ID].values):
                id_glc = df.loc[df[ID] == id_var][glc]
                ranges = helper.tir_exercise(id_glc)
                ranges.insert(0, id_var)
                list_results.append(ranges)

            results = pd.DataFrame(list_results, columns=['ID', 'TIR_hypo_exercise', 'TIR_normal_exercise',
                                                          'TIR_hyper_exercise'])

    # df doesn't have an id column
    else:
        # normal thresholds
        # same as 1st block, just need to run for once rather than for all IDs
        if not exercise_thresholds:
            list_results.append([helper.tir_helper(df[glc])])
            results = pd.DataFrame(list_results,
                                   columns=['TIR_lv2_hypo', 'TIR_lv1_hypo', 'TIR_hypo',
                                            'TIR_norm', 'TIR_hyper',
                                            'TIR_lv1_hyper', 'TIR_lv2_hyper'])
        # exercise thresholds
        # same as 2nd block but only need to run once
        else:
            list_results.append(helper.tir_exercise(df[glc]))
            results = pd.DataFrame(list_results, columns=['TIR_hypo_exercise', 'TIR_normal_exercise',
                                                          'TIR_hyper_exercise'])
    return results


def ea1c(df, glc='glc', ID=None):
    """
    Calculates ea1c for glucose data from a Pandas Dataframe. The dataframe must contain  works for df with an ID column
    or without.
    :param df: Pandas DataFrame
        Glucose monitor time series, must contain columns titled 'time' and 'glc', 'ID' optional

    :param glc : String
        Name of column with glucose data

    :param ID : String
        Name of column with patient ID (optional)

    :return: Pandas DataFrame
        Contains ea1c and ID if present
    """
    '''if df.empty:
        raise Exception('Empty dataframe')'''
    list_results = []
    # loops through IDs calculating ea1c and returning
    if ID is not None:
        for id_var in set(df[ID].values):
            id_glc = df.loc[df[ID] == id_var][glc]
            mean = id_glc.mean()
            ea1c_value = (mean + 2.59) / 1.59
            list_results.append([id_var, ea1c_value])
        return pd.DataFrame(list_results, columns=['ID', 'ea1c'])
    # calculates ea1c and returns for single dataset
    else:
        mean = df[glc].mean()
        ea1c_value = (mean + 2.59) / 1.59
        return pd.DataFrame(ea1c_value, columns=['ea1c'])


def glycemic_variability(df, glc='glc', ID=None):
    """
    Calculates glycemic variability (SD, CD, min and max glucose) values for glucose data from a Pandas Dataframe. The
    dataframe must contain 'time' (timestamp) and 'glc' (glucose) columns, works for df with or without an 'ID' column

    :param df: Pandas DataFrame
        Glucose monitor time series, must contain columns titled 'time' and 'glc', 'ID' optional

    :param glc : String
        Name of column with glucose data

    :param ID : String
        Name of column with patient ID (optional)

    :return: Pandas DataFrame
        Contains SD, CD, min and max glucose and ID if present
    """
    list_results = []
    # if df has an id column, set has_id to either true or false
    if ID is not None:
        for id_var in set(df[ID].values):
            id_glc = df.loc[df[ID] == id_var][glc]  # added loc rather than slice

            mean = id_glc.mean()
            sd = id_glc.std()
            cv = sd * 100 / mean
            min_glc = id_glc.min()
            max_glc = id_glc.max()

            list_results.append([id_var, sd, cv, min_glc, max_glc])
            # returns df with IDs and glyc var values
        return pd.DataFrame(list_results, columns=['ID', 'sd', 'cv', 'minimum_glucose', 'maximum_glucose'])
    # no IDs in df
    else:
        mean = df[glc].mean()
        sd = df.glc.std()
        cv = sd * 100 / mean
        min_glc = df.min()
        max_glc = df.max()
        list_results.append([sd, cv, min_glc, max_glc])
        # returns df with glyc var values
        return pd.DataFrame(list_results, columns=['sd', 'cv', 'minimum_glucose', 'maximum_glucose'])


def average_glucose(df, glc='glc', ID=None):
    """
    Calculates average (mean) glucose for glucose data from a Pandas Dataframe. The dataframe must contain 'time'
    (timestamp) and 'glc' (glucose) columns, works for df with or without an 'ID' column.

    :param df: Pandas DataFrame
        Glucose monitor time series, must contain columns titled 'time' and 'glc', 'ID' optional

    :param glc : String
        Name of column with glucose data

    :param ID : String
        Name of column with patient ID (optional)

    :return: Pandas DataFrame
        Contains average glucose and ID if present
    """
    '''if df.empty:
        raise Exception('Empty dataframe')'''

    list_results = []
    # if df has an id column, set has_id to either true or false
    if ID is not None:
        for id_var in set(df[ID].values):
            id_glc = df[df[ID] == id_var][glc]
            mean = id_glc.mean()
            list_results.append([id_var, mean])
        return pd.DataFrame(list_results, columns=['ID', 'average_glucose'])

    else:
        mean = df[glc].mean()
        return pd.DataFrame(mean, columns='average_glucose')


def hypoglycemic_episodes(df, time='time', glc='glc', ID=None, interval_size=5, breakdown=False,
                          exercise_thresholds=False, interpolate=False, interp_method='pchip'):
    """
    Calculates the number of level 1 and level 2 hypoglycemic episodes from the glucose data in a Pandas DataFrame. The
    results can either be an overview of episodes or a breakdown of each episode with a start and end time. Threshold
    can be set to exercise threshold (<7mmol/L). This method gives the option of interpolating and allows the selection
    of the interpolation method. The dataframe must contain 'time' (timestamp) and 'glc' (glucose) columns, works for
    df with or without an 'ID' column.

    :param df: Pandas DataFrame
        Glucose monitor time series, must contain columns titled 'time' and 'glc', 'ID' optional

    :param time: String
        Name of columns with time data

    :param glc : String
        Name of column with glucose data

    :param ID : String
        Name of column with patient ID (optional)

    :param interval_size: Int
        The length of time between glucose readings

    :param exercise_thresholds: Bool
        Whether exercise threshold (<7mmol/L) should be used to determine a hypoglycemic episode. If False, regular
        thresholds of 3.9mmol/L and 3mmol/L will be used to determine level 1 and level 2 episodes.

    :param breakdown: Bool
        Whether an episode by episode breakdown of the results should be returned or an overview of episodes for each ID

    :param interpolate: Bool
        Whether the data should be interpolated before the hypoglycemic episodes are calculated

    :param interp_method:
        The interpolation method used if interpolation is True

    :return: Pandas DataFrame
        If breakdown is False, will return an overview with the number of hypoglycemic episodes (level 1 & 2 or
        <7mmol/L), mean length of episode, total time in hypoglycemia for each ID.
        If breakdown is True, will return a breakdown of each episode with start time, end time, whether it is a level 2
        episode and the min glucose for each ID
    """
    '''if df.empty:
        raise Exception('Empty dataframe')'''
    # has an id column to loop through ids
    if ID is not None:
        df_dropped = df[[ID, glc, time]].dropna()
        df_dropped.columns = ['ID', glc, time]
        # loop through all ids applying helper_hypo_episodes function, found in helper.py
        # returned in a multi-index format so need to select level
        results = df_dropped.groupby('ID').apply(
            lambda group: helper.helper_hypo_episodes(group, time=time, glc=glc, gap_size=interval_size,
                                                      breakdown=breakdown,
                                                      interpolate=interpolate, exercise=exercise_thresholds,
                                                      interp_method=interp_method)).reset_index().drop(
            columns='level_1')
        if exercise_thresholds & (breakdown is False):
            results.drop(columns=['number_lv1_hypos', 'number_lv2_hypos'], inplace=True)
            results.columns = ['ID', 'number_hypos_below_5', 'avg_length_hypo_below_5',
                               'total_time_in_hypos_below_5']
        return results

    else:
        df_dropped = df[[glc, time]].dropna()
        results = helper.helper_hypo_episodes(df_dropped, interpolate=interpolate, interp_method=interp_method,
                                              exercise=exercise_thresholds, gap_size=interval_size, breakdown=breakdown)
        #results = results.rename(columns={ID: 'ID'})
        return results


def percent_missing(df, time='time', glc='glc', ID=None, interval_size=5, start_datetime=None, end_datetime=None):
    """
    Calculates the percentage of missing data from the glucose data in a Pandas DataFrame. Can enter start and end time
    to assess over a period of time how much data is missing, otherwise will just do from start to end of dataset.
    :param df: Pandas DataFrame
        Glucose monitor time series, must contain columns titled 'time' and 'glc', 'ID' optional

    :param time: String
        Name of columns with time data

    :param glc : String
        Name of column with glucose data

    :param ID : String
        Name of column with patient ID (optional)

    :param interval_size: Int
        The length of time between glucose readings

    :param start_datetime: String or Datetime
        The start datetime when setting a period to check for missing data

    :param end_datetime: String or Datetime
        The end datetime when setting a period to check for missing data

    :return: Pandas DataFrame
        Contains percentage of missing data, start time, end time and interval size
    """
    if df.empty:
        return pd.DataFrame([[ID, 100]], columns=['ID', 'percent_missing'])
        #raise Exception('Empty dataframe')

    df[time] = pd.to_datetime(df[time])

    # Some check that checks start_time and end_time are dt objects
    start_datetime = pd.to_datetime(start_datetime)
    end_datetime = pd.to_datetime(end_datetime)
    list_results = []
    '''if df.empty:
        return 100'''
    if ID is not None:
        for id_var in set(df[ID].values):
            id_time = df[df[ID] == id_var]
            list_results.append([id_var, helper.helper_missing(id_time, time, glc, gap_size=interval_size,
                                                               start_time=start_datetime, end_time=end_datetime)])
        df_results = pd.DataFrame(list_results, columns=['ID', 'percent_missing']).round(2)
        return df_results
    else:
        return pd.DataFrame([helper.helper_missing(df, time, glc, gap_size=interval_size, start_time=start_datetime,
                                                   end_time=end_datetime)], columns=['percent_missing']).round(2)

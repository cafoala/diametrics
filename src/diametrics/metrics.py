import copy
import pandas as pd
import numpy as np
from scipy import signal
import warnings
from datetime import timedelta
import statistics
from sklearn import metrics
# ASK MIKE/MICHAEL ABOUT THIS
#from src.diametrics 
from diametrics import _glycemic_events_helper, preprocessing
#import src.diametrics._glycemic_events_helper as _glycemic_events_helper, preprocessing
#import src.diametrics._glycemic_events_dicts as _glycemic_events_dicts

#fift_mins = timedelta(minutes=15)
#thirt_mins = timedelta(minutes=30)

UNIT_THRESHOLDS = {
    'mmol': {
        'norm_tight': 7.8,
        'hypo_lv1': 3.9,
        'hypo_lv2': 3,
        'hyper_lv1': 10,
        'hyper_lv2': 13.9
    },
    'mg': {
        'norm_tight': 140,
        'hypo_lv1': 70,
        'hypo_lv2': 54,
        'hyper_lv1': 180,
        'hyper_lv2': 250
    }
}

    
def all_standard_metrics(df, units=None, gap_size=5, start_dt=None, end_dt=None, lv1_hypo=None, lv2_hypo=None, lv1_hyper=None, lv2_hyper=None, event_mins=15, event_long_mins=120):
    """
    Calculate standard metrics of glycemic control for glucose data.

    Args:
        df (DataFrame): Input DataFrame containing glucose data.
        return_df (bool, optional): Flag indicating whether to return the results as a DataFrame. Defaults to True.
        lv1_hypo (float, optional): Level 1 hypoglycemia threshold. Defaults to None.
        lv2_hypo (float, optional): Level 2 hypoglycemia threshold. Defaults to None.
        lv1_hyper (float, optional): Level 1 hyperglycemia threshold. Defaults to None.
        lv2_hyper (float, optional): Level 2 hyperglycemia threshold. Defaults to None.
        additional_tirs (list, optional): Additional time in range thresholds. Defaults to None.
        event_mins (int, optional): Duration in minutes for identifying glycemic events. Defaults to 15.
        event_long_mins (int, optional): Duration in minutes for identifying long glycemic events. Defaults to 120.

    Returns:
        DataFrame or dict: Calculated standard metrics as a DataFrame if return_df is True, or as a dictionary if return_df is False.

    Raises:
        Exception: If the input DataFrame fails the data check.

    """
    def run(df, units, gap_size, start_dt, end_dt, lv1_hypo, lv2_hypo, lv1_hyper, lv2_hyper, event_mins, event_long_mins):
        if preprocessing.check_df(df):
            results = {}
            # Drop rows with missing time or glucose values
            df = df.dropna(subset=['time', 'glc']).reset_index(drop=True)
            # Amount of data available
            data_suff = data_sufficiency(df, start_dt, end_dt, gap_size=gap_size)
            results.update(data_suff)
            
            # Average glucose
            avg_glc_result = average_glc(df)
            results.update(avg_glc_result)

            # eA1c
            ea1c_result = ea1c(df, units)
            results.update(ea1c_result)
            
            # Glycemic variability
            glyc_var = glycemic_variability(df)
            results.update(glyc_var)
            
            # AUC
            auc_result = auc(df)
            results.update(auc_result)
            
            # LBGI and HBGI
            bgi_results = bgi(df, units)
            results.update(bgi_results)
            
            # MAGE
            mage_results = mage(df)
            results.update(mage_results)

            # Time in ranges
            ranges = time_in_range(df, units)
            results.update(ranges)

            # glycemic index (GRI)
            gri_results = glycemic_risk_index(df, units)
            results.update(gri_results)

            # New method
            hypos = glycemic_episodes(df, units, lv1_hypo, lv2_hypo, lv1_hyper, lv2_hyper, event_mins, event_long_mins)
            results.update(hypos)
            
            results = pd.DataFrame(results)

            return results
        
        else:
            raise Exception("Data check failed. Please ensure the input DataFrame is valid.")
    
    if 'ID' in df.columns:
        results = df.groupby('ID').apply((lambda group: run(group, units, gap_size, start_dt, end_dt, lv1_hypo, lv2_hypo, lv1_hyper, lv2_hyper, event_mins, event_long_mins)), include_groups=False)
        results = pd.DataFrame(results).reset_index().drop(columns='level_1')
        return results
    else:    
        results = run(df, units, gap_size, start_dt, end_dt, lv1_hypo, lv2_hypo, lv1_hyper, lv2_hyper, event_mins, event_long_mins)
        return results    
    

def average_glc(df):
    """
    Calculate the average glucose reading from the 'glc' column in the DataFrame.

    Args:
        df (pandas.DataFrame): The DataFrame containing a 'glc' column with glucose readings.

    Returns:
        pandas.DataFrame: A DataFrame containing the average glucose reading.
    """
    def run(group):
        # Calculate the mean of the 'glc' column in the DataFrame
        average = group['glc'].mean()
        return pd.Series({'avg_glc': average})
    
    if 'ID' in df.columns:
        # Group by 'ID' and apply the run function, ensuring the output is a DataFrame
        results = df.groupby('ID').apply(run, include_groups=False).reset_index()
    else:    
        # Apply function directly and convert the resulting Series to a DataFrame
        results = run(df)
        results = pd.DataFrame([results])  # Convert Series to a single-row DataFrame

    return results


def percentiles(df):
    """
    Calculate various percentiles of glucose readings in the DataFrame.

    Args:
        df (pandas.DataFrame): The DataFrame containing a 'glc' column with glucose readings.

    Returns:
        pandas.DataFrame: A DataFrame containing the calculated percentiles of glucose readings.
    """
    def run(group):
        # Drop NaN values in 'glc' column to ensure percentile calculations are accurate
        valid_data = group.dropna(subset=['glc'])

        # Calculate the specified percentiles
        percentiles = np.percentile(valid_data['glc'], [0, 10, 25, 50, 75, 90, 100])
        labels = [
            'min_glc',
            'percentile_10',
            'percentile_25',
            'percentile_50',
            'percentile_75',
            'percentile_90',
            'max_glc'
        ]
        return pd.Series(percentiles, index=labels)

    if 'ID' in df.columns:
        # Group by 'ID' and apply the run function, ensuring the output is a DataFrame
        results = df.groupby('ID').apply(run, include_groups=False).reset_index()
    else:
        # Apply function directly and convert the resulting Series to a DataFrame
        results = run(df)
        results = pd.DataFrame([results])  # Convert Series to a single-row DataFrame

    return results



def glycemic_variability(df):
    """
    Calculate the glycemic variability metrics for glucose readings in the DataFrame.

    Args:
        df (pandas.DataFrame): The DataFrame containing a 'glc' column with glucose readings.

    Returns:
        pandas.DataFrame: A DataFrame containing the calculated glycemic variability metrics.
    """

    def run(group):
        avg_glc = group['glc'].mean()
        sd = group['glc'].std()
        cv = (sd * 100) / avg_glc
        return pd.Series({
            'sd': sd,
            'cv': cv
        })

    if 'ID' in df.columns:
        # Apply run function and convert Series to DataFrame
        results = df.groupby('ID').apply(run, include_groups=False).reset_index()
    else:
        # Apply run function to the whole DataFrame without grouping
        results = run(df)
        results = pd.DataFrame([results])  # Convert Series to a single-row DataFrame

    return results


def ea1c(df, units=None):
    """
    Calculate estimated average HbA1c (eA1c) based on the average glucose readings in the DataFrame.

    Args:
        df (pandas.DataFrame): The DataFrame containing a 'glc' column with glucose readings.
        units (str): The units of the glucose readings, 'mmol' for mmol/L or any other string for mg/dL.

    Returns:
        pandas.DataFrame: A DataFrame containing the estimated average HbA1c (eA1c) value.
    """
    def run(group, units):
        avg_glc = group['glc'].mean()

        # Check the units of glucose readings if not provided
        if units is None:
            units = preprocessing.detect_units(group)  # Assuming 'preprocessing.detect_units' is implemented
        
        # Determine the eA1c based on units
        if units == 'mmol':
            ea1c_result = (avg_glc + 2.59) / 1.59
        elif units == 'mg':
            ea1c_result = (avg_glc + 46.7) / 28.7
        else:
            raise ValueError(f"Unsupported units '{units}'. Supported units are 'mmol' and 'mg'.")

        return pd.Series({'ea1c': ea1c_result})
    
    if 'ID' in df.columns:
        # Group by 'ID' and apply the run function, pass units to the function
        results = df.groupby('ID').apply(run, units=units, include_groups=False).reset_index()
    else:
        # Apply function directly and convert the resulting Series to a DataFrame
        results = run(df, units)
        results = pd.DataFrame([results])  # Convert Series to a single-row DataFrame

    return results


    
def auc(df):
    """
    Calculate the area under the curve (AUC) for glucose readings in the DataFrame.

    Args:
        df (pandas.DataFrame): The DataFrame containing a 'glc' column with glucose readings and a 'time' column with timestamps.

    Returns:
        pandas.DataFrame: A DataFrame containing the AUC value with units.
        
    Note:
        - The function calculates the AUC by approximating the integral using the trapezoidal rule.
        - Assumes glucose readings are sorted by time.
        - Units are converted based on the detected glucose measurement units.
    """
    def run(group):
        
        if group.shape[0] < 2:
            overall_auc = np.nan  # Not enough data to calculate AUC
        else:
            # Calculate AUC using the trapezoidal rule
            overall_auc = 0.5 * (df['glc'].values[1:] + df['glc'].values[:-1]).mean()

        return pd.Series({'auc': overall_auc})
    
    # Ensure dataframe is copied if needed to avoid modifying original unintentionally
    df = df.dropna(subset=['time', 'glc'])

    if 'ID' in df.columns:
        # Apply the run function to each group and include include_groups=False
        results = df.groupby('ID').apply(run, include_groups=False).reset_index()
    else:
        # Apply function directly and convert the resulting Series to a DataFrame
        results = run(df)
        results = pd.DataFrame([results])  # Convert Series to a single-row DataFrame

    return results
    


def mage(df):
    """
    Calculate the mean amplitude of glycemic excursions (MAGE) using scipy's signal class.

    Args:
        df (pandas.DataFrame): The DataFrame containing a 'glc' column with glucose readings and a 'time' column with timestamps.

    Returns:
        pandas.DataFrame: A DataFrame containing the MAGE value.
    """
    def run(group):
        # Find peaks and troughs
        peaks, _ = signal.find_peaks(group['glc'], prominence=group['glc'].std())
        troughs, _ = signal.find_peaks(-group['glc'], prominence=group['glc'].std())

        # Consolidate peaks and troughs, and sort by time
        points = np.sort(np.concatenate((peaks, troughs, [0, len(group) - 1])))
        selected_points = group.iloc[points].copy()

        # Calculate differences between consecutive points
        selected_points['diff'] = selected_points['glc'].diff().abs()

        # Calculate MAGE
        mage_value = selected_points['diff'].mean()

        return pd.Series({'mage': mage_value})

    df = df.dropna(subset=['time', 'glc'])  # Work on a copy of the DataFrame to avoid modifying the original
    if 'ID' in df.columns:
        results = df.groupby('ID').apply(run, include_groups=False).reset_index()
    else:
        results = run(df)
        results = pd.DataFrame([results])  # Convert Series to a single-row DataFrame

    return results


def time_in_range(df, units=None):
    """
    Helper function for time in range calculation with normal thresholds. Calculates the percentage of readings within
    each threshold by dividing the number of readings within range by total length of the series.

    Args:
        df (pandas.DataFrame): The DataFrame containing a 'glc' column with glucose readings.

    Returns:
        df (pandas.DataFrame): A DataFrame containing the percentages of readings within each threshold range.

    Note:
        - The function calculates the percentage of readings within different threshold ranges for time in range (TIR) analysis.
        - TIR normal represents the percentage of readings within the range [3.9, 10].
        - TIR normal 1 represents the percentage of readings within the range [3.9, 7.8].
        - TIR normal 2 represents the percentage of readings within the range [7.8, 10].
        - TIR level 1 hypoglycemia represents the percentage of readings within the range [3, 3.9].
        - TIR level 2 hypoglycemia represents the percentage of readings below 3.
        - TIR level 1 hyperglycemia represents the percentage of readings within the range (10, 13.9].
        - TIR level 2 hyperglycemia represents the percentage of readings above 13.9.
    """
    def run(df, units):
        # Convert input series to NumPy array for vectorized calculations
        series = np.array(df['glc']) 
        # Get length of the series
        df_len = len(series)

        # Check the units of glucose readings if not provided
        if units is None:
            units = preprocessing.detect_units(df)  # Assuming 'preprocessing.detect_units' is implemented
        
        # Use this to get the thresholds from the global dictionary
        thresholds = UNIT_THRESHOLDS.get(units, {})
        norm_tight = thresholds.get('norm_tight')
        hypo_lv1 = thresholds.get('hypo_lv1')
        hypo_lv2 = thresholds.get('hypo_lv2')
        hyper_lv1 = thresholds.get('hyper_lv1')
        hyper_lv2 = thresholds.get('hyper_lv2')

        # Calculate the percentage of readings within each threshold range
        tir_norm = np.sum((series >= hypo_lv1) & (series <= hyper_lv1)) / df_len * 100
        tir_norm_1 = np.sum((series >= hypo_lv1) & (series <= norm_tight)) / df_len * 100
        #tir_norm_2 = np.around(np.sum((series >= norm_tight) & (series <= hyper_lv1)) / df_len * 100, decimals=2)
        tir_lv1_hypo = np.sum((series < hypo_lv1) & (series >= hypo_lv2)) / df_len * 100
        tir_lv2_hypo = np.sum(series < hypo_lv2) / df_len * 100
        tir_lv1_hyper = np.sum((series <= hyper_lv2) & (series > hyper_lv1)) / df_len * 100
        tir_lv2_hyper = np.sum(series > hyper_lv2) / df_len * 100
        
        # Return the calculated values as a dictionary
        return pd.Series({
            'tir_normal': tir_norm,
            'tir_norm_tight': tir_norm_1,
            #'TIR normal 2 (%)': tir_norm_2,
            'tir_lv1_hypo': tir_lv1_hypo,
            'tir_lv2_hypo': tir_lv2_hypo,
            'tir_lv1_hyper': tir_lv1_hyper,
            'tir_lv2_hyper': tir_lv2_hyper
        })
    
    if 'ID' in df.columns:
        results = df.groupby('ID').apply((lambda group: run(group, units=units)), include_groups=False).reset_index()        
        return results
    else:    
        results = run(df, units)
        return results


def glycemic_risk_index(df, units=None):
    """
    Calculate the Glycemia Risk Index (GRI) based on glucose readings and time-in-range metrics.

    Args:
        df (pandas.DataFrame): The DataFrame containing a 'glc' column with glucose readings.
        units (str): The units of glucose readings, 'mmol' for mmol/L or 'mg' for mg/dL.

    Returns:
        pandas.DataFrame: A DataFrame containing the GRI score.
    """
    # Define the GRI weights for each glucose range
    GRI_WEIGHTS = {
        'severe_hypoglycemia': 50,  # <54 mg/dL
        'hypoglycemia': 20,        # 54–69 mg/dL
        'euglycemia': 0,           # 70–180 mg/dL
        'hyperglycemia': 20,       # 181–250 mg/dL
        'severe_hyperglycemia': 50 # >250 mg/dL
    }

    # Check the units of glucose readings if not provided
    if units is None:
        units = preprocessing.detect_units(df)  # Assuming 'preprocessing.detect_units' is implemented

    def run(df, units):
        # Calculate time-in-range metrics using the existing function
        tir_results = time_in_range(df, units)
        
        # Extract the relevant percentages
        severe_hypo = tir_results['tir_lv2_hypo']  # <54 mg/dL
        hypo = tir_results['tir_lv1_hypo']         # 54–69 mg/dL
        euglycemia = tir_results['tir_normal']     # 70–180 mg/dL
        hyper = tir_results['tir_lv1_hyper']       # 181–250 mg/dL
        severe_hyper = tir_results['tir_lv2_hyper'] # >250 mg/dL

        # Calculate the GRI score based on weights
        gri_score = (
            (severe_hypo * GRI_WEIGHTS['severe_hypoglycemia']) +
            (hypo * GRI_WEIGHTS['hypoglycemia']) +
            (euglycemia * GRI_WEIGHTS['euglycemia']) +
            (hyper * GRI_WEIGHTS['hyperglycemia']) +
            (severe_hyper * GRI_WEIGHTS['severe_hyperglycemia'])
        ) / 100  # Normalize to a scale of 0–100
        
        return pd.Series({'gri': gri_score})

    if 'ID' in df.columns:
        # Apply the function to each group if the DataFrame is grouped by 'ID'
        results = df.groupby('ID').apply((lambda group: run(group, units=units)), include_groups=False).reset_index()
        return results
    else:
        # Apply the function directly if there are no groups
        results = run(df, units)
        return pd.DataFrame([results])  # Convert to a DataFrame for consistency



def glycemic_episodes(df, units=None, hypo_lv1_thresh=None, hypo_lv2_thresh=None, hyper_lv1_thresh=None, hyper_lv2_thresh=None, mins=15, long_mins=120):
    """
    Calculate the statistics of glycemic episodes (hypoglycemic and hyperglycemic events) based on glucose readings.

    Args:
        df (pandas.DataFrame): The DataFrame containing a 'glc' column with glucose readings and a 'time' column with timestamps.
        hypo_lv1_thresh (float, optional): Level 1 hypoglycemic threshold. If not provided, it will be determined based on the units detected. Default is None.
        hypo_lv2_thresh (float, optional): Level 2 hypoglycemic threshold. If not provided, it will be determined based on the units detected. Default is None.
        hyper_lv1_thresh (float, optional): Level 1 hyperglycemic threshold. If not provided, it will be determined based on the units detected. Default is None.
        hyper_lv2_thresh (float, optional): Level 2 hyperglycemic threshold. If not provided, it will be determined based on the units detected. Default is None.
        mins (int, optional): Minimum duration in minutes for an episode to be considered. Default is 15.
        long_mins (int, optional): Minimum duration in minutes for a prolonged episode to be considered. Default is 120.

    Returns:
        df (pandas.DataFrame): A DataFrame containing the statistics of glycemic episodes.

    Note:
        - The function detects the units of glucose readings in the DataFrame.
        - The threshold values for hypoglycemic and hyperglycemic episodes are determined based on the detected units, unless explicitly provided.
        - The function calculates the statistics of glycemic episodes using the '_glycemic_events_helper.calculate_episodes' helper function.
        - The calculated statistics include the total number, LV1 (Level 1) events, LV2 (Level 2) events, prolonged events, average length, and total time spent in episodes for both hypoglycemic and hyperglycemic events.
    """
    def run(df, units, hypo_lv1_thresh, hypo_lv2_thresh, hyper_lv1_thresh, hyper_lv2_thresh, mins, long_mins):
        # Identify the units of the dataframe
        if units is None:
            units = preprocessing.detect_units(df)

        # Determine threshold values if not provided
        thresholds = UNIT_THRESHOLDS.get(units, {})
        hypo_lv1_thresh = hypo_lv1_thresh or thresholds.get('hypo_lv1')
        hypo_lv2_thresh = hypo_lv2_thresh or thresholds.get('hypo_lv2')
        hyper_lv1_thresh = hyper_lv1_thresh or thresholds.get('hyper_lv1')
        hyper_lv2_thresh = hyper_lv2_thresh or thresholds.get('hyper_lv2')

        # Calculate statistics for hypoglycemic events
        total_hypos, lv1_hypos, lv2_hypos, prolonged_hypos, avg_length_hypos, total_time_hypos = _glycemic_events_helper.calculate_episodes(df, True, hypo_lv1_thresh, hypo_lv2_thresh, mins, long_mins)

        # Calculate statistics for hyperglycemic events
        total_hypers, lv1_hypers, lv2_hypers, prolonged_hypers, avg_length_hypers, total_time_hypers = _glycemic_events_helper.calculate_episodes(df, False, hyper_lv1_thresh, hyper_lv2_thresh, mins, long_mins)

        # Prepare results dictionary
        results = pd.Series({'number_hypos': total_hypos, 
                    #'Number LV1 hypoglycemic events': lv1_hypos, 
                    'number_lv2_hypos':lv2_hypos, 
                    'number_prolonged_hypos':prolonged_hypos, 
                    'avg_length_hypos': avg_length_hypos, 
                    'total_time_in_hypo':total_time_hypos,
                    'number_hypers':total_hypers, 
                    #'Number LV1 hyperglycemic events':lv1_hypers,
                    'number_lv2_hypers':lv2_hypers,
                    'number_prolonged_hypers':prolonged_hypers, 
                    'avg_length_hypers':avg_length_hypers,
                    'total_time_in_hyper':total_time_hypers})
        return results
    
    if 'ID' in df.columns:
        results = df.groupby('ID').apply((lambda group: run(group, units, hypo_lv1_thresh, hypo_lv2_thresh, hyper_lv1_thresh, hyper_lv2_thresh, mins, long_mins)), include_groups=False)
        return results
    else:    
        results = run(df, units, hypo_lv1_thresh, hypo_lv2_thresh, hyper_lv1_thresh, hyper_lv2_thresh, mins, long_mins)
        return results


def data_sufficiency(df, start_time=None, end_time=None, gap_size=None):
    """
    Calculate the data sufficiency percentage based on the provided DataFrame, gap size, and time range.

    Args:
        df (pandas.DataFrame): The DataFrame containing a 'glc' column with glucose readings and a 'time' column with timestamps.
        gap_size (int): The size of the gap in minutes to check for data sufficiency.
        start_time (datetime.datetime, optional): The start time of the time range. If not provided, it will be determined from the DataFrame. Default is None.
        end_time (datetime.datetime, optional): The end time of the time range. If not provided, it will be determined from the DataFrame. Default is None.

    Returns:
        df (pandas.DataFrame): A DataFrame containing the start and end datetimes of the time range and the data sufficiency percentage.

    Raises:
        ValueError: If the gap size is not 5 or 15.

    Note:
        - The function calculates the data sufficiency based on the number of non-null values within the specified gap size intervals.
        - The start and end times of the time range are either provided or determined from the DataFrame.
        - The gap size must be either 5 or 15. Otherwise, a ValueError is raised.
        - The data sufficiency percentage is calculated as the ratio of non-null values to the total expected values.
    """
    def run(df, gap_size, start_time, end_time):
        # Determine start and end time from the DataFrame if not provided
        start_time = start_time or df['time'].iloc[0]
        end_time = end_time or df['time'].iloc[-1]
        days = (end_time-start_time).total_seconds()/86400

        # Subset the DataFrame based on the provided time range
        df = df.loc[(df['time'] >= start_time) & (df['time'] <= end_time)]

        # Calculate the interval size
        if gap_size == None:
            df['time'].diff().mode().iloc[0]
        else:
            gap_size = timedelta(minutes=gap_size)
            
        # If it doesn't conform to 5 or 15 then don't count it
        if ((timedelta(minutes=4) < gap_size) & (gap_size < timedelta(minutes=6))):
            freq = '5min'
        elif ((timedelta(minutes=14) < gap_size) & (gap_size < timedelta(minutes=16))):
            freq = '15min'
        else:
            raise ValueError('Invalid gap size. Gap size must be 5 or 15.')

        # Calculate the number of non-null values
        number_readings = sum(df.set_index('time').groupby(pd.Grouper(freq=freq)).count()['glc'] > 0)
        # Calculate the total expected readings based on the start and end of the time range
        total_readings = ((end_time - start_time) + gap_size) / gap_size

        # Calculate the data sufficiency percentage
        if number_readings >= total_readings:
            data_sufficiency = 100
        else:
            data_sufficiency = number_readings * 100 / total_readings


        return pd.Series({
            'start_dt': str(start_time.round('min')),
            'end_dt': str(end_time.round('min')),
            'num_days':days,
            'data_sufficiency': np.round(data_sufficiency, 1)
        })
    
    if 'ID' in df.columns:
        results = df.groupby('ID').apply((lambda group: run(group, gap_size, start_time, end_time)), include_groups=False).reset_index()
        return results
    else:    
        results = run(df, gap_size, start_time, end_time)
        return results


def calc_bgi(glucose, units):
    """
    Calculate the Blood Glucose Index (BGI) based on glucose readings.

    Args:
        glucose (float): Glucose reading.
        units (str): Units of glucose measurement ('mmol/L' or 'mg/dL').

    Returns:
        float: Blood Glucose Index (BGI) value.

    Note:
        - The BGI calculation depends on the units of glucose.
        - The formula for BGI differs for 'mmol/L' and 'mg/dL'.
    """
    if units == 'mmol':
        num1 = 1.794
        num2 = 1.026
        num3 = 1.861
    else:
        num1 = 1.509
        num2 = 1.084
        num3 = 5.381
    bgi = num1 * (np.log(glucose) ** num2 - num3)
    return bgi

def lbgi(glucose, units):
    """
    Calculate the Low Blood Glucose Index (LBGI) based on glucose readings.

    Args:
        glucose (float): Glucose reading.
        units (str): Units of glucose measurement ('mmol/L' or 'mg/dL').

    Returns:
        float: Low Blood Glucose Index (LBGI) value.

    Note:
        - The LBGI is calculated using the BGI value.
        - The LBGI is a measure of the risk associated with low blood glucose levels.
    """
    bgi = calc_bgi(glucose, units)
    lbgi = 10 * (min(bgi, 0) ** 2)
    return lbgi

def hbgi(glucose, units):
    """
    Calculate the High Blood Glucose Index (HBGI) based on glucose readings.

    Args:
        glucose (float): Glucose reading.
        units (str): Units of glucose measurement ('mmol/L' or 'mg/dL').

    Returns:
        float: High Blood Glucose Index (HBGI) value.

    Note:
        - The HBGI is calculated using the BGI value.
        - The HBGI is a measure of the risk associated with high blood glucose levels.
    """
    bgi = calc_bgi(glucose, units)
    hbgi = 10 * (max(bgi, 0) ** 2)
    return hbgi

def bgi(df, units=None):
    """
    Calculate the Blood Glucose Index (BGI) metrics for a DataFrame of glucose readings.

    Args:
        df (pandas.DataFrame): The DataFrame containing a 'glc' column with glucose readings.

    Returns:
        df (pandas.DataFrame): A DataFrame containing the Low Blood Glucose Index (LBGI) and High Blood Glucose Index (HBGI) values.

    Note:
        - The function calculates the LBGI and HBGI based on the glucose readings and detects the units of measurement.
        - The LBGI and HBGI are average values calculated from individual readings using the 'lbgi' and 'hbgi' functions.
    """
    def run(df, units):
        if units is None:
            units = preprocessing.detect_units(df)
        lbgi_result = df['glc'].apply(lambda x: lbgi(x, units)).mean()
        hbgi_result = df['glc'].apply(lambda x: hbgi(x, units)).mean()
        return pd.Series({'lbgi': lbgi_result, 'hbgi': hbgi_result})
    
    if 'ID' in df.columns:
        results = df.groupby('ID').apply(run, units=units, include_groups=False).reset_index()        
        return results
    else:    
        results = run(df, units)
        return results

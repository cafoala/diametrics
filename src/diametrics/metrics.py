import copy
import pandas as pd
import numpy as np
#import scipy
from scipy import signal
import warnings
from datetime import timedelta
import statistics
from sklearn import metrics
# ASK MIKE/MICHAEL ABOUT THIS
from src.diametrics import _glycemic_events_helper
#import src.diametrics._glycemic_events_helper as _glycemic_events_helper
#import src.diametrics._glycemic_events_dicts as _glycemic_events_dicts

fift_mins = timedelta(minutes=15)
thirt_mins = timedelta(minutes=30)

def all_metrics(df, return_df=True,units='mmol/L', interval=15, additional_tirs=None, lv1_hypo=3.9, lv2_hypo=3.0, lv1_hyper=10, lv2_hyper=13.9,  event_mins=15, event_long_mins=120):    
    factor = 0.0557
    if check_df(df):
        # create a list to add the results to
        results = {}#{'ID': ID}
        results_mg = {}#{'ID': ID}
        df = df.dropna(subset=['time', 'glc']).reset_index(drop=True)
        
        # Convert to mmol/L
        if units == 'mg/dL':
            df['glc'] = df['glc']*factor
        
        # Amount of data available
        data_suff = data_sufficiency(df,  gap_size=interval)
        data_suff['Days'] = str(pd.to_datetime(data_suff['End DateTime']) - pd.to_datetime(data_suff['Start DateTime']))

        results.update(data_suff)
        
        # Basic metrics
        avg_glc = df.glc.mean()
        sd = df.glc.std()
        cv = (sd * 100 / avg_glc)
        min_glc = df.glc.min() # not necessary... but useful maybe?
        max_glc = df.glc.max() # same
        ea1c = (avg_glc + 2.59) / 1.59 # mmol right?
        auc_result, daily_breakdown, hourly_breakdown = auc(df)
        
        glyc_var = {'Average glucose':avg_glc, 'SD':sd, 'CV (%)':cv, 'eA1c (%)':ea1c, 
                    'Min. glucose':min_glc, 'Max. glucose':max_glc, 'AUC': auc_result}
        results.update(glyc_var)
        glyc_var_mg =  {}
        
        for i in glyc_var:
            if (i=='CV (%)') or (i=='eA1c (%)'):
                glyc_var_mg[i] = glyc_var[i]
            else:
                glyc_var_mg[i] = glyc_var[i]/factor
        results_mg.update(glyc_var_mg)

        # LBGI and HBGI
        bgi_results = bgi(df['glc'], 'mmol/L')
        results.update(bgi_results)
        #bgi_mg = metrics_helper.helper_bgi(df['glc'], 'mg/dL')
        results_mg.update(bgi_results)
        
        # MAGE
        mage_results = mage(df)
        results.update(mage_results)
        mage_mg = {'MAGE':mage_results['MAGE']/factor}
        results_mg.update(mage_mg)

        # Time in ranges
        ranges = time_in_range(df.glc)
        results.update(ranges)
        results_mg.update(ranges)

        unique_ranges = unique_time_in_range(df.glc, additional_tirs, units)
        results.update(unique_ranges)
        results_mg.update(unique_ranges)
        
        # New method
        hypos = glycemic_episodes(df, lv1_hypo, lv2_hypo, lv1_hyper, lv2_hyper, event_mins, event_long_mins)
        results.update(hypos)
        results_mg.update(hypos)
        
        if return_df: 
            # Convert to df
            results = pd.DataFrame.from_dict([results])
            results_mg = pd.DataFrame.from_dict([results_mg])

        return results #, results_mg
    
    else:
        return None #, None

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
            
def calculate_auc(df):
    if df.shape[0]>1:
        start_time = df.time.iloc[0]
        mins_from_start = df.time.apply(lambda x: x-start_time)
        df['hours_from_start'] = mins_from_start.apply(lambda x: (x.total_seconds()/60)/60)
        avg_auc = metrics.auc(df['hours_from_start'], df['glc'])#/24
        return avg_auc
    else:
        return np.nan

def auc(df):
    df['date'] = df['time'].dt.date
    df['hour'] = df['time'].dt.hour
    hourly_breakdown = df.groupby([df.date, df.hour]).apply(lambda group: calculate_auc(group)).reset_index()
    hourly_breakdown.columns = ['date', 'hour', 'auc']
    daily_breakdown = hourly_breakdown.groupby('date').auc.mean()
    hourly_avg = hourly_breakdown['auc'].mean()
    #daily_auc = df.groupby(df['time'].dt.date).apply(lambda group: calculate_auc(group))/24 # .reset_index()
    #daily_avg = daily_auc.mean()
    return  hourly_avg, daily_breakdown, hourly_breakdown 
    
def mage(df):
    '''
    Calculates the mage using Scipy's signal class
    '''
    # Find peaks and troughs using scipy signal
    peaks, properties = signal.find_peaks(df['glc'], prominence=df['glc'].std())
    troughs, properties = signal.find_peaks(-df['glc'], prominence=df['glc'].std())
    # Create dataframe with peaks and troughs in order
    single_indexes = df.iloc[np.concatenate((peaks, troughs, [0, -1]))]
    single_indexes.sort_values('time', inplace=True)
    # Make a difference column between the peaks and troughs
    single_indexes['diff'] = single_indexes['glc'].diff()
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
    return {'MAGE':mage_mean}

def convert_to_rounded_percent(value, length):
    return round(value * 100 / length, 2)

# NumPy
def time_in_range(series):
    """
    Helper function for time in range calculation with normal thresholds. Calculates the percentage of readings within
    each threshold by dividing the number of readings within range by total length of series
    """
    series = np.array(series) # Convert input series to NumPy array for vectorized calculations
    df_len = len(series) # Get length of the series

    # Calculate the percentage of readings within each threshold range
    tir_norm = np.around(np.sum((series >= 3.9) & (series <= 10)) / df_len * 100, decimals=2)
    tir_lv1_hypo = np.around(np.sum((series < 3.9) & (series >= 3)) / df_len * 100, decimals=2)
    tir_lv2_hypo = np.around(np.sum(series < 3) / df_len * 100, decimals=2)
    tir_lv1_hyper = np.around(np.sum((series <= 13.9) & (series > 10)) / df_len * 100, decimals=2)
    tir_lv2_hyper = np.around(np.sum(series > 13.9) / df_len * 100, decimals=2)

    # Return the calculated values as a dictionary
    return {'TIR normal': tir_norm, 'TIR level 1 hypoglycemia': tir_lv1_hypo, 'TIR level 2 hypoglycemia': tir_lv2_hypo,
            'TIR level 1 hyperglycemia': tir_lv1_hyper, 'TIR level 2 hyperglycemia': tir_lv2_hyper}


def tir_helper(series):
    """
    Helper function for time in range calculation with normal thresholds. Calculates the percentage of readings within
    each threshold by divSiding number of readings within range by total length of series
    """
    df_len = series.size
    #tir_hypo = convert_to_rounded_percent(series.loc[series < 3.9].size, df_len)

    tir_lv1_hypo = convert_to_rounded_percent(series.loc[(series < 3.9) & (series >= 3)].size, df_len)

    tir_lv2_hypo = convert_to_rounded_percent(series.loc[series < 3].size, df_len)

    tir_norm = convert_to_rounded_percent(series.loc[(series >= 3.9) & (series <= 10)].size, df_len)
    
    #tir_hyper = convert_to_rounded_percent(series.loc[series > 10].size, df_len)

    tir_lv1_hyper = convert_to_rounded_percent(series.loc[(series <= 13.9) & (series > 10)].size, df_len)

    tir_lv2_hyper = convert_to_rounded_percent(series.loc[series > 13.9].size, df_len)
    
    #tir_norm_1 = convert_to_rounded_percent((series.loc[(series >= 3.9) & (series < 7.8)]).size, df_len)

    #tir_norm_2 = convert_to_rounded_percent((series.loc[(series >= 7.8) & (series <= 10)]).size, df_len)
    '''
    tir_hypo_ex = series.loc[series < 5].size, df_len)

    tir_norm_ex = (series.loc[(series >= 5) & (series <= 15)]).size, df_len)

    tir_hyper_ex = series.loc[series > 15].size, df_len)
    '''
    #'TIR hypoglycemia':tir_hypo,'TIR hyperglycemia':tir_hyper, 
    return {'TIR normal': tir_norm,  'TIR level 1 hypoglycemia':tir_lv1_hypo, 'TIR level 2 hypoglycemia':tir_lv2_hypo, #'TIR normal (3.9-7.8)': tir_norm_1, 'TIR normal (7.8-10)': tir_norm_2, 
            'TIR level 1 hyperglycemia':tir_lv1_hyper, 'TIR level 2 hyperglycemia':tir_lv2_hyper}

def unique_tir_helper(glc_series, lower_thresh, upper_thresh):
    df_len = glc_series.size
    if lower_thresh==2.2:
        tir = convert_to_rounded_percent(glc_series.loc[glc_series <= upper_thresh].size, df_len)
    elif upper_thresh==22.2:
        tir = convert_to_rounded_percent(glc_series.loc[glc_series >= lower_thresh].size, df_len)
    else:
        tir = convert_to_rounded_percent(glc_series.loc[(glc_series <= upper_thresh) & (glc_series >= lower_thresh)].size, df_len)
    return tir

def unique_time_in_range(glc_series, thresholds, units):
    if thresholds is None:
        return {}
    results_dict = {}
    for i in thresholds:
        name = f'TIR {i[0]}-{i[1]}{units} (%)'
        tir = unique_tir_helper(glc_series, i[0], i[1])
        results_dict[name] = tir
    return results_dict
        
def glycemic_episodes(df, hypo_lv1_thresh=3.9, hypo_lv2_thresh=3, hyper_lv1_thresh=10, hyper_lv2_thresh=13.9, mins=15, long_mins=120):
    total_hypos, lv1_hypos, lv2_hypos, prolonged_hypos, avg_length_hypos, total_time_hypos = _glycemic_events_helper.calculate_episodes(df, True, hypo_lv1_thresh, hypo_lv2_thresh, mins, long_mins)
    total_hypers, lv1_hypers, lv2_hypers, prolonged_hypers, avg_length_hypers, total_time_hypers = _glycemic_events_helper.calculate_episodes(df, False, hyper_lv1_thresh, hyper_lv2_thresh, mins, long_mins)
    results = {'Total number hypoglycemic events': total_hypos, 
                'Number LV1 hypoglycemic events': lv1_hypos, 
                'Number LV2 hypoglycemic events':lv2_hypos, 
                'Number prolonged hypoglycemic events':prolonged_hypos, 
                'Avg. length of hypoglycemic events': avg_length_hypos, 
                'Total time spent in hypoglycemic events':total_time_hypos,
                'Total number hyperglycemic events':total_hypers, 
                'Number LV1 hyperglycemic events':lv1_hypers,
                'Number LV2 hyperglycemic events':lv2_hypers,
                'Number prolonged hyperglycemic events':prolonged_hypers, 
                'Avg. length of hyperglycemic events':avg_length_hypers,
                'Total time spent in hyperglycemic events':total_time_hypers}
    return results


def data_sufficiency(df, gap_size, start_time=None, end_time=None):
    """
    Helper for percent_missing function
    """
    # Calculate start and end time from dataframe
    if start_time is None:
        start_time = df['time'].iloc[0]
    if end_time is None:
        end_time = df['time'].iloc[-1]
    
    # Subsection of df with start and end times provided
    df = df.loc[(df['time']>=start_time)&(df['time']<=end_time)]

    if gap_size == 5:
        freq = '5min'
    elif gap_size==15:
        freq = '15min'
    else:
        return print('YOU CAN\'T USE THAT INTERVAL!')
    
    # calculate the number of non-null values
    number_readings = sum(df.set_index('time').groupby(pd.Grouper(freq=freq)).count()['glc'] > 0)
    # calculate the missing data based on start and end of df
    total_readings = ((end_time - start_time)+timedelta(minutes=gap_size))/+timedelta(minutes=gap_size)

    if number_readings >= total_readings:
        data_sufficiency = 100
    else:
        data_sufficiency = number_readings*100/total_readings
    
    return {'Start DateTime': str(start_time.round('min')), 'End DateTime':str(end_time.round('min')), 'Data Sufficiency (%)':np.round(data_sufficiency, 1)}

# LBGI and HBGI
def calc_bgi(glucose, units):
    if units=='mmol/L':
        num1=1.794
        num2=1.026
        num3=1.861
    else:
        num1=1.509
        num2=1.084
        num3=5.381
    bgi = num1*(np.log(glucose)**num2 - num3)
    return bgi
    
def calc_lbgi(glucose, units):
    bgi = calc_bgi(glucose, units)
    lbgi = 10*(min(bgi, 0)**2)
    return lbgi

def calc_hbgi(glucose, units):
    bgi = calc_bgi(glucose, units)
    hbgi = 10*(max(bgi, 0)**2)
    return hbgi

def bgi(glc_series, units):
    lbgi = glc_series.apply(lambda x: calc_lbgi(x, units)).mean()
    hbgi = glc_series.apply(lambda x: calc_hbgi(x, units)).mean()
    return {'LBGI': lbgi, 'HBGI':hbgi}
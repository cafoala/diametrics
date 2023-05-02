import pandas as pd
import datetime
import numpy as np
import warnings

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
        
def replace_cutoffs(dm_obj, remove=False, cap=True, lo_cutoff=2.1, hi_cutoff=22.3):
    '''
    
    '''
    if remove:
        dm_obj.data['glc']= pd.to_numeric(dm_obj.data['glc'].replace({'High': lo_cutoff, 'Low': lo_cutoff, 'high': hi_cutoff, 'low': lo_cutoff, 
                             'HI':hi_cutoff, 'LO':lo_cutoff, 'hi':hi_cutoff, 'lo':lo_cutoff}))

        if cap:
            dm_obj.data['glc'][dm_obj.data['glc']>hi_cutoff] = hi_cutoff
            dm_obj.data['glc'][dm_obj.data['glc']<lo_cutoff] = lo_cutoff

    dm_obj.data = dm_obj.data[pd.to_numeric(dm_obj.data['glc'], errors='coerce').notnull()]
    dm_obj.data['glc'] = pd.to_numeric(dm_obj.data['glc'])
    dm_obj.data['time'] = pd.to_datetime(dm_obj.data['time'])
    dm_obj.data = dm_obj.data.reset_index(drop=True)
    return dm_obj
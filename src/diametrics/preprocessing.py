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
        
def replace_cutoffs(df, remove=False, cap=True, lo_cutoff=2.1, hi_cutoff=22.3):
    '''
    
    '''
    if remove:
        df['glc']= pd.to_numeric(df['glc'].replace({'High': lo_cutoff, 'Low': lo_cutoff, 'high': hi_cutoff, 'low': lo_cutoff, 
                             'HI':hi_cutoff, 'LO':lo_cutoff, 'hi':hi_cutoff, 'lo':lo_cutoff}))

        if cap:
            df['glc'][df['glc']>hi_cutoff] = hi_cutoff
            df['glc'][df['glc']<lo_cutoff] = lo_cutoff

    df = df[pd.to_numeric(df['glc'], errors='coerce').notnull()]
    df['glc'] = pd.to_numeric(df['glc'])
    df['time'] = pd.to_datetime(df['time'])
    df = df.reset_index(drop=True)
    return df
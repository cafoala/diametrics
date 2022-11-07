from datetime import datetime
import pandas as pd
import autoprocessing
import transformData


def calculate_time_interval(df):
    diff = df.dropna(subset=['time','glc'])
    diff = df.time.diff().mode()
    diff_mins = int(diff[0].total_seconds())
    return diff_mins


# let's assume we're getting 1 file in and it's already been confirmed that it's a df
def preprocess_df(df, filename):
    # Replace high and low values for different devices 
    # ?DOUBLE CHECK THESE VALUES?
    df.replace({'High': 22.2, 'Low': 2.2, 'HI':22.2, 'LO':2.2, 'hi':22.2, 'lo':2.2}, inplace=True)
    i = transformData.transformData(df)
    if i.usable:
        # Check that the whole datetime works
        try:
            i.data['time'] = pd.to_datetime(i.data['time'])
        except:
            # log that there is a non-dt item in the col
            print('datetime didnt work')
            return None
        try:
            i.data['glc'] = pd.to_numeric(i.data['glc'])
        except:    
            # log that there is a non-float item in the col
            print('glc didnt work')
            return None
        if 'scan_glc' in i.data.columns:
            try:
                i.data['scan_glc'] = pd.to_numeric(i.data['scan_glc'])
            except:
                print('scan_glc didnt work')
                return None

        # Calculate if mmol/L or mg/dL
        i.units = autoprocessing.assert_units(i.data['glc'])

        # Check if there's an id
        if i.id is None:
            i.id = filename.rsplit('.', 1)[0] ## had .name previously
        # Check if there's an interval
        if i.interval is None:
            i.interval = calculate_time_interval(i.data)
        return i
    else:
        # Log the errors?
        return None
    
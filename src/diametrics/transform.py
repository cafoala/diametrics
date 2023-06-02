import pandas as pd
import datetime
import numpy as np
import os 

def open_file(filepath):
    try:
        if 'csv' in filepath:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(filepath, header=None, names = [i for i in range(0, 20)])
        elif 'xls' in filepath:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(filepath, header=None, names = [i for i in range(0, 20)])
        elif 'txt' or 'tsv' in filepath:
            # Assume that the user upl, delimiter = r'\s+'oaded an excel file
            df = pd.read_table(filepath, header=None, names = [i for i in range(0, 20)])
        return df
    except Exception as e:
        print(e)

def convert_libre(df):
    # Set third row as column headers
    df.columns = df.iloc[2]
    # Drop top rows
    df = df.iloc[3:]
    df.reset_index(inplace=True, drop=True)
    # Keep important columns
    if 'Historic Glucose(mmol/L)' in df.columns:
        df = df.loc[:,('Meter Timestamp', 'Historic Glucose(mmol/L)', 'Scan Glucose(mmol/L)')]
    elif 'Historic Glucose(mg/dL)' in df.columns:
        df = df.loc[:,('Meter Timestamp', 'Historic Glucose(mg/dL)', 'Scan Glucose(mg/dL)')]
    elif 'Historic Glucose mmol/L' in df.columns:
        df = df.loc[:,('Device Timestamp', 'Historic Glucose mmol/L', 'Scan Glucose mmol/L')]
    else:
        df = df = df.loc[:,('Device Timestamp', 'Historic Glucose mg/dL', 'Scan Glucose mg/dL')]

    # Rename cols
    df.columns = ['time', 'glc', 'scan_glc']
    
    # Convert to datetime
    df['time'] = pd.to_datetime(df['time'])

    # Drop and sort
    df = df.dropna(subset=['time', 'glc']).sort_values('time').reset_index(drop=True)
    
    return df


def convert_dexcom(df):
    # Set first row as column headers
    df.columns = df.iloc[0]
    # Drop top rows
    df = df.iloc[1:]
    cols = [str(col) for col in df]
    filter_col = [col for col in cols if col.startswith('Timestamp')]
    #df.drop(index=[2], inplace=True)
    
    if 'GlucoseValue' in df.columns:
        # Keep important columns
        df = df.loc[:,('GlucoseDisplayTime', 'GlucoseValue')]
    elif 'Glucose Value (mmol/L)' in df.columns:
        df = df.loc[:,(filter_col[0], 'Glucose Value (mmol/L)')]
        df = df.dropna(subset=[filter_col[0]])

    elif 'Glucose Value (mg/dL)' in df.columns:
        df = df.loc[:,(filter_col[0], 'Glucose Value (mg/dL)')]
        df = df.dropna(subset=[filter_col[0]])
    
    # Rename cols
    df.columns = ['time', 'glc']
    # Convert to datetime
    df['time'] = pd.to_datetime(df['time'])
    
    # Drop and sort
    df = df.dropna(subset=['time', 'glc']).sort_values('time').reset_index(drop=True)
    
    return df


def convert_medtronic(df):
    # Set first row as column headers
    df.columns = df.iloc[5]
    # Drop top rows
    df = df.iloc[6:]
    #df.drop(index=[2], inplace=True)
    df.reset_index(inplace=True, drop=True)
    if 'BG Reading (mmol/L)' in df.columns:
        # Keep important columns
        df = df.loc[:,('Date', 'Time', 'BG Reading (mmol/L)')]
    elif 'BG Reading (mg/dL)' in df.columns:
        df = df.loc[:,('Date', 'Time', 'BG Reading (mg/dL)')]
    
    df.columns = ['date', 'time', 'glc']
    df = df.dropna()
    df['time'] = pd.to_datetime(df.apply(lambda x: combine_datetime(x['date'], x['time']), axis=1))
    
    # Drop and sort
    df = df.dropna(subset=['time', 'glc']).sort_values('time').reset_index(drop=True)
    
    return df


def combine_datetime(date, time):
    dt = f'{date} {time}'
    try:
        dt = pd.to_datetime(dt)
    except:
        dt = np.nan
    return dt

def transform_directory(directory, device):
    total_cgm = []
    for filename in os.listdir(directory):
        # Read the file using pandas
        filepath =  directory  + '/' + filename
        df = open_file(filepath)

        # Convert to standard format
        if device == 'libre':
            df_std = convert_libre(df)
            
        elif device == 'dexcom':
            df_std = convert_dexcom(df)

        elif device == 'medtronic':
            df_std = convert_medtronic(df)

        else:
            print('autoprocessing')

        # Set ID
        df_std['ID'] = filename.split('.')[0]

        # Append
        total_cgm.append(df_std)
    
    return pd.concat(total_cgm)
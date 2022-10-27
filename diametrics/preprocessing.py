from datetime import datetime
import pandas as pd
import autoprocessing

def autoprocess_df(df, has_id):
    # Calculate the max number of rows datetime and glucose should be the max... oh shit
    max_rows = df.shape[0]
    # Keep cols that have over 70% of max rows
    cols_to_keep = df.count()[df.count() > max_rows * 0.7].index
    # Select the central rows to avoid issues with headers and footers
    middle_rows = autoprocessing.select_middle_rows(df, cols_to_keep, max_rows)
    # Identify which cols are datetime and glucose
    col_types = autoprocessing.identify_key_columns(middle_rows, cols_to_keep)
    df_processed = autoprocessing.select_final_columns(df, col_types)
    '''
    if has_id:
        df_processed = df_processed.join(df['ID'], how='left')
    df_processed.reset_index(drop=True, inplace=True)
    '''
    return df_processed


def calculate_time_interval(time):
    diff = pd.to_datetime(time.dropna()).diff().mode()
    diff_mins = int(diff[0].total_seconds())
    return diff_mins


def assert_complete_format(df):
    if 'ID' in df.columns:
        if all(x in ['time','glc'] for x in df.columns):
            return 'complete'
        else:
            return 'id'
    else:
        return 'no_id'
    

# let's assume we're getting 1 file in and it's already been confirmed that it's a df
def preprocess_file(df, filename):
    # checkCompleteFormat()
    # checkDevices()
    # autoprocessing()
    # Replace high and low values for different devices 
    # ?DOUBLE CHECK THESE VALUES?
    df.replace({'High': 22.2, 'Low': 2.2, 'HI':22.2, 'LO':2.2, 'hi':22.2, 'lo':2.2}, inplace=True)
    # 
    # Check if it's already in the right format
    if assert_column_names(df)=='complete':
        return df
    elif assert_column_names(df)=='id':
        has_id = True
    else:
        has_id = False

    # Preprocess
    df_preprocessed = autoprocess_df(df, has_id)
    # If there's no ID column, use filename as ID
    if not has_id:
        df_preprocessed['ID'] = filename.name.rsplit('.', 1)[0]
    # Calculate metrics
    # ?THROW AN ERROR?
    #df_preprocessed.glc = pd.to_numeric(df_preprocessed.glc)
    # Calculate time interval
    if time_int is None:
        time_int = calculate_time_interval(df_preprocessed.time)
    results = cgm.all_metrics(df_preprocessed, 'time', 'glc', 'ID', time_int, start_datetime, end_datetime, by_day=by_day)
    #st.write(results)
    results_frame = results_frame.append(results)
    #results_frame = pd.DataFrame(results_list)
    results_frame.reset_index(drop=True, inplace=True)
    return results_frame
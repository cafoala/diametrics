from datetime import datetime
import pandas as pd
import sys

def find_header(df):
    dropped = df.dropna()
    dropped.columns = ['time', 'glc']
    count = 0
    for i, row in dropped.iterrows():
        is_date = try_parsing_date(row['time'])
        if not is_date:
            count += 1
            continue
        try:
            float(row['glc'])
            break
        except Exception:
            count += 1
    if count == dropped.shape[0]:
        raise Exception('Problem with input data')
    return dropped.iloc[count:]


def try_parsing_date(text):
    text = str(text)
    # ? NEEDS MORE THINKING ME THINKS ?
    formats = ("%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M:%S", "%d/%m/%Y %H:%M",
               "%d-%m-%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S",
               "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M")  # add dot format
    for fmt in formats:
        try:
            datetime.strptime(text, fmt)
            return True
        except ValueError:
            pass
    return False


def test_col(col):
    
    #try:
    if col.dtype is float:
        col_num = pd.to_numeric(col).dropna()
        # print('NUM')
        if ((col_num < 28) & (col_num > 2)).all():
            #print('glc_uk')
            return 'glc_uk'
        elif ((col_num < 505) & (col_num > 36)).all():
            return 'glc_us'
    else:
        return 'unknown'
    #except Exception:
    #    return 'unknown'

    # maybe could add an elif for a str dtype
    else:
        # this is so slow
        datetime_bool = col.apply(lambda x: try_parsing_date(x))
        if datetime_bool.all():
            return 'dt'
    

def preprocess_data(df, id_colname=None):
    # Calculate the max number of rows datetime and glucose should be the max... oh shit
    max_rows = df.count().max()
    # Keep cols that have over 70% of max rows
    # ? MAYBE GET RID OF THIS ?
    cols_to_keep = df.count()[df.count() > max_rows * 0.7].index
    # Create subset with central rows to avoid any weird headers and footers
    number_test_rows = 20
    if max_rows<number_test_rows:
        number_test_rows = int(0.3*max_rows)
    # Select the middle rows
    middle_rows = df[cols_to_keep].iloc[int((max_rows-number_test_rows)/2):int((max_rows+number_test_rows)/2)]

    # ? DEAL WITH FOOTERS IF THERE ?

    # Set up dictionary with datetime and glucose for uk and us conventions
    col_type_dict = {'dt': [], 'glc_uk': [], 'glc_us': []}
    # loop through remaining cols
    for i in cols_to_keep:
        # Call the test_col function to see if it fits in
        col_type = test_col(middle_rows[i])
        if col_type != 'unknown':
            col_type_dict[col_type].append(i)
    print(col_type_dict)
    if (len(col_type_dict['dt']) > 0) & (len(col_type_dict['glc_uk']) > 0):
        sub_frame = df[[col_type_dict['dt'][0], col_type_dict['glc_uk'][0]]]
        df_processed = find_header(sub_frame)
    elif (len(col_type_dict['dt']) > 0) & (len(col_type_dict['glc_us']) > 0):
        sub_frame = df[col_type_dict['dt'][0], col_type_dict['glc_us'][0]]
        df_processed = find_header(sub_frame)
        try:
            df_processed['time'] = df_processed['time'] / 0.0557
        except Exception:
            print('Problem with input data')
    else:
        raise Exception('Can\'t identify datetime and/or glucose columns')
    if id_colname is not None:
        df_processed = df_processed.join(df[id_colname], how='left')
        df_processed.rename({id_colname: 'ID'}, inplace=True)
    df_processed.reset_index(drop=True, inplace=True)
    return df_processed


def calculate_time_interval(time):
    diff = pd.to_datetime(time.dropna()).diff().mode()
    diff_mins = int(diff[0].total_seconds())
    return diff_mins

# let's assume we're getting 1 file in and it's already been confirmed that it's a df
def auto_process_file(df):
    # Replace high and low values for different devices 
    # ?DOUBLE CHECK THESE VALUES?
    df.replace({'High': 22.2, 'Low': 2.2, 'HI':22.2, 'LO':2.2, 'hi':22.2, 'lo':2.2}, inplace=True)
    # Preprocess
    df_preprocessed = preprocess_data(df, id_colname)
    # If there's no ID column, use filename as ID
    if id_colname is None:
        df_preprocessed['ID'] = file.name.rsplit('.', 1)[0]
    # Calculate metrics
    # ?THROW AN ERROR?
    df_preprocessed.glc = pd.to_numeric(df_preprocessed.glc)
    # Calculate time interval
    if time_int is None:
        time_int = calculate_time_interval(df_preprocessed.time)
    results = cgm.all_metrics(df_preprocessed, 'time', 'glc', 'ID', time_int, start_datetime, end_datetime, by_day=by_day)
    #st.write(results)
    results_frame = results_frame.append(results)
    #results_frame = pd.DataFrame(results_list)
    results_frame.reset_index(drop=True, inplace=True)
    return results_frame
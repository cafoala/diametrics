from datetime import datetime
import pandas as pd

def find_header(df):
    dropped = df.dropna()
    dropped.columns = ['time', 'glc']
    count = 0
    for i, row in dropped.iterrows():
        is_date = assert_datetime(row['time'])
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


def assert_datetime(text):
    '''
    Asserts whether instance is a datetime in certain format
    ** steal something
    '''
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

def assert_units(col_num):
    if ((col_num < 28) & (col_num > 2)).all():
        return 'glc_uk'
    elif ((col_num < 505) & (col_num > 36)).all():
        return 'glc_us'
    else:
        return 'unknown'

def test_col(col):
    try:
    #if col.dtype is float:
        col_num = pd.to_numeric(col).dropna()
        # print('NUM')
        return assert_units(col_num)
        
    except Exception:
        # this is so slow
        datetime_bool = col.apply(lambda x: assert_datetime(x))
        if datetime_bool.all():
            return 'dt'
        # maybe could add an elif for a str dtype
        else:
            return 'unknown'

def select_middle_rows(df, cols_to_keep, max_rows):
    # Create subset with central rows to avoid any weird headers and footers
    number_test_rows = 20
    if max_rows<number_test_rows:
        number_test_rows = int(0.3*max_rows)
    # Select the middle rows
    middle_rows = pd.DataFrame(df[cols_to_keep].iloc[int((max_rows-number_test_rows)/2):int((max_rows+number_test_rows)/2)])
    return middle_rows

def identify_key_columns(df, cols_to_keep):
    # Set up dictionary with datetime and glucose for uk and us conventions
    col_types = {'dt': [], 'glc_uk': [], 'glc_us': []}
    # loop through remaining cols
    for i in cols_to_keep:
        # Call the test_col function to see if it fits in
        col_type = test_col(df[i])
        if col_type != 'unknown':
            col_types[col_type].append(i)
    return col_types

def select_final_columns(df, col_types):
    if col_types['dt'] and col_types['glc_uk']:
        sub_frame = df[[col_types['dt'][0], col_types['glc_uk'][0]]]
        
    elif col_types['dt'] and col_types['glc_us']:
        sub_frame = df[col_types['dt'][0], col_types['glc_us'][0]]
        '''
        try:
            df_processed['glc'] = df_processed['glc'] / 0.0557
            return df_processed
        except Exception:
            return None
            print('Problem with input data')
        '''
    else:
        print('Can\'t identify datetime and/or glucose columns')
        return None
        raise Exception('Can\'t identify datetime and/or glucose columns')
    df_processed = find_header(sub_frame)
    return df_processed
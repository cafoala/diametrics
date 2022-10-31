import pandas as pd
import autoprocessing

class CheckDevices:
    def __init__(self, df):
        if assert_flash_libre(df):
            convert_flash_libre(df)
        '''
        elif assert_continuous_libre(df):
            convert_continuous_libre(df)
        elif assert_dexcom(df):
            assert_dexcom(df)
        '''
        else:
            autoprocess(df)
            # autoprocessing?
            
    def autoprocess(df):
        self.device = 'Unknown'

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

    
    def assert_flash_libre(self, df):
        #check if cols align
        header =['Meter', 'Serial Number', 'Meter Timestamp', 'Record Type', 'Historic Glucose(mmol/L)', 'Scan Glucose(mmol/L)']
        if set(header).issubset(set(df.iloc[2]):
            # Set that it's usable
            self.usable = True
            # Set device name
            self.device = 'FreeStyle Libre'
            # set time interval to 15mins
            self.interval = 15
            # Set ID if it's not empty
            if pd.notnull(df.iloc[1,0]):
                self.id = df.iloc[1,0]
            return True


    def convert_flash_libre(self, df):
        # Drop top rows
        df = df.iloc[2:]
        # Keep important columns
        df = df.loc['Meter Timestamp', 'Historic Glucose(mmol/L)', 'Scan Glucose(mmol/L)']
        # Rename cols
        df.columns = ['time', 'glc', 'scan_glc']
        self.data = df
    '''
    def assert_continuous_libre():
        #same as above

    def assert_dexcom_pre_2015():
        # same as above
        # choose internal date 

    def assert_medtronic():
        # never seen one

    def assert_nightscout():
        # not even sure if this is a thing
    '''
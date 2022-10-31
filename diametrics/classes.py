import pandas as pd

class hypoglycemicEpisodes:
    def __init__(self, df, lv1_threshold, lv2_threshold):
        '''
        Works with hypos
        '''
        # Set the time column to datetime and sort by it
        df['time'] = pd.to_datetime(df['time'])
        df.sort_values('time', inplace=True)

        # Gives a consecutive unique number to each set of consecutive readings below
        # 3.9mmol/L
        bool_array = df['glc'] < lv1_threshold
        unique_num = bool_array.ne(bool_array.shift()).cumsum()
        number_consec = unique_num.map(unique_num.value_counts()).where(bool_array)
        df_unique = pd.DataFrame({'time_rep': df['time'], 'glc_rep':
                                df['glc'], 'unique_number_low': unique_num,
                                'consec_readings_low': number_consec})

        # Drop any null glucose readings and reset index
        df_unique.dropna(subset=['glc_rep'], inplace=True)
        df_unique.reset_index(inplace=True, drop=True)

        # Group by the unique number to collapse into episodes, then use min to
        # calculate the minimum glucose for each bout and the start time
        unique_min = df_unique.groupby('unique_number_low').min()

        # Use the start time of bouts and periods between bouts to calculate duration
        # of episodes
        unique_min['diff'] = unique_min.time_rep.diff().shift(-1)

        # Only keep hypos that are 15 mins or longer (smaller than this doesn't count)
        results = unique_min[unique_min['diff'] >= timedelta(minutes=15)]

        # Fill the consec readings with binary value to show whether they are hypos or
        # the periods between hypos
        results.consec_readings_low = results.consec_readings_low.fillna(-1)
        results['hypo'] = results['consec_readings_low'] > 0

        # Merge any consecutive values left by removal of too-short episodes using
        # a new unique number
        results['unique'] = results['hypo'].ne(results['hypo'].shift()).cumsum()

        # Group by the unique number, select the min values and select relevant columns
        final_results = results.groupby('unique').min()[['time_rep', 'glc_rep', 'hypo', 'diff']]

        # Calculate difference between hypo and non-hypo periods and shift column up to
        # get the final duration of the periods
        final_results['diff2'] = final_results['time_rep'].diff().shift(-1)

        # Drop the non-hypo periods and then drop the hypo column
        final_results = final_results.loc[final_results['hypo'] ==
                                        True].drop(columns=['hypo'])

        # Rename columns
        final_results.columns = ['start_time', 'min_glc', 'initial_duration', 'duration']

        # Fill final hypo with previous duration value in diff col then drop initial
        # duration
        finaL_results = final_results['duration'].fillna(final_results['initial_duration'])
        final_results.drop(columns=['initial_duration'], inplace=True)
        final_results.reset_index(drop=True, inplace=True)
        # Drop the final column if it's less than 15 mins
        final_results = final_results.loc[final_results['duration']>=
                                        timedelta(minutes=15)]

        # Create new column identifying if the hypo is level 2 (<3mmol/L)
        final_results['lv2'] = final_results['min_glc'] < lv2_threshold
        
        # Reset index
        final_results.reset_index(drop=True, inplace=True)
        
        self.breakdown = final_results

        def number_of_episodes(self):
            # Calculate overview statistics
            number_hypos = self.breakdown.shape[0]
            self.number_hypos = number_hypos
            #return number_hypos
            
        def average_length(self):
            avg_length = self.breakdown.duration.mean().round('1s')
            return avg_length
        
        def total_time(self):
            total_time_hypo = self.breakdown.duration.sum()
            return total_time_hypo

        def min(self):
            
            # Return 0s if no hypos and nan if something weird happens
            if pd.notnull(avg_length):
                avg_length = avg_length#.total_seconds() / 60
                total_time_hypo = total_time_hypo#.total_seconds() / 60
            elif number_hypos == 0:
                avg_length = 0
                total_time_hypo = 0
            else:
                avg_length = np.nan
                total_time_hypo = np.nan
                
            # Divide total hypos into number of level 1 and level 2 hypos
            number_lv2_hypos = final_results[final_results['lv2']].shape[0]
            number_lv1_hypos = number_hypos - number_lv2_hypos
            
            # Save as dataframe and return
            frame = pd.DataFrame([[number_hypos, number_lv1_hypos, number_lv2_hypos,
                                avg_length, total_time_hypo]],
                                columns=['number_hypos','number_lv1_hypos',
                                        'number_lv2_hypos', 'avg_length_of_hypo',
                                        'total_time_in_hypos'])
            
            return frame
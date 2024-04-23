# Diametrics
Diametrics is a Python package and associated [WebApp](https://diametrics.org) designed for the analysis of Continuous Glucose Monitoring (CGM) data. 

The goal of this package is to enable researchers to quickly calculate the metrics of diabetes control outlined in the [international consensus on the use of continuous glucose monitors](https://diabetesjournals.org/care/article/40/12/1631/37000/International-Consensus-on-Use-of-Continuous) in Python.
 

Diametrics has functionality for data preprocessing, calculating standard metrics of glycemic control and data visualization, using Plotly.


## Contents 
The diametrics functions are contained within a metrics.py file. The functions are

`all_metrics` calculates all of the below metrics

`average_glucose` mean glucose data given

`time_in_range` % time spent in normal (3.9-10mmol/L), hyperglycaemia (>10) and hypoglycaemia (<3.9). Hyper- and hypo-glycaemia are also broken down to % time in level 1 and level 2

`glycemic_variability` standard deviation (SD), coefficient of variation (CV) and min and max glucose

`ea1c` estimated A1c

`hypoglycemic_episodes` the number of level 1 and level 2 hypoglycemic episodes, plus an optional breakdown of every episode with start and end times

`percent_missing` percentage of data missing between two timepoints

## How to use?
 The functions take Pandas dataframes as the arguments along with the column names for the glucose readings and time. The functions can be used on datasets with only one person's data or can be used on a combined dataframe with an ID column, whose name can be specified if present.

For some of the functions there is an option to switch the thresholds to exercise thresholds, rather than normal ones.

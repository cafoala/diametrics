import metrics
import helper
import pandas as pd

example1 = pd.read_csv('test-data\example1.csv')
example2 = pd.read_csv('test-data\example2.csv')

# test the tir helper function
def test_tir():
    test_array = [2.9, 3, 3.8, 3.9, 4, 9.9, 10, 10.1, 13.8, 13.9, 14]
    test_data = pd.Series(test_array)
    assert helper.tir_helper(test_data) == [36.36, 27.27, 18.18, 9.09, 36.36, 27.27, 9.09]

# test the 3 different outcomes of check_df function
def test_check_df1():
    assert helper.check_df(example1) == True

def test_check_df2():
    assert helper.check_df(example2) == False

def test_check_df3():
    assert helper.check_df(10) == False
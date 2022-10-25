import metrics
import helper
import pandas as pd

def test_tir():
    test_array = [2.9, 3, 3.8, 3.9, 4, 9.9, 10, 10.1, 13.8, 13.9, 14]
    test_data = pd.Series(test_array)-v
    assert helper.tir_helper(test_data) == [36.36, 27.27, 18.18, 9.09, 36.36, 27.27, 9.09]

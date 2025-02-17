# Diametrics

Diametrics is a Python package and associated WebApp designed for analyzing Continuous Glucose Monitoring (CGM) data. This package enables researchers and clinicians to streamline their workflow by providing tools for data preprocessing, metric calculation, and visualization, following international standards for diabetes control.

## Features
- **Data Preprocessing:** Convert raw CGM data from multiple device formats (Libre, Dexcom, Medtronic) into a standardized format. Fill missing data, handle outliers, and set time windows for focused analysis.
- **Glycemic Metrics:** Calculate a comprehensive set of glycemic control metrics including averages, variability, time in range (TIR), glycemic risk index (GRI), estimated A1c (eA1c), and hypoglycemic/hyperglycemic episodes.
- **Visualizations:** Generate interactive plots and graphs, such as glucose traces, pie charts for TIR distribution, and ambulatory glucose profiles, using Plotly.

---

## Installation

Install Diametrics using pip:
```bash
pip install diametrics
```

---

## Quick Start

### 1. Load Your Data
The package supports multiple file formats and devices. Use the provided functions to standardize your CGM data:
```python
from diametrics.transform import open_file, convert_libre, convert_dexcom, convert_medtronic

data = open_file("data.csv")
standardized_data = convert_libre(data)  # For Libre device
```

### 2. Preprocess Your Data
Use preprocessing functions to clean and format your data:
```python
from diametrics.preprocessing import replace_cutoffs, fill_missing_data

clean_data = replace_cutoffs(standardized_data, cap=True)
filled_data = fill_missing_data(clean_data)
```

### 3. Calculate Metrics
Leverage the metrics module to calculate all glycemic control metrics:
```python
from diametrics.metrics import all_standard_metrics

results = all_standard_metrics(filled_data, units='mmol')
```

### 4. Visualize Your Results
Generate interactive plots to explore your data:
```python
from diametrics.visualizations import glucose_trace, tir_pie

glucose_plot = glucose_trace(filled_data)
glucose_plot.show()

pie_chart = tir_pie(filled_data)
pie_chart.show()
```

---

## Functionalities

### Data Preprocessing
- **`replace_cutoffs`:** Handle outlier glucose values by capping or replacing them.
- **`fill_missing_data`:** Interpolate missing CGM readings using customizable methods.
- **`set_time_frame`:** Filter data by specific time windows.
- **`detect_units` & `change_units`:** Automatically identify and convert glucose units (mmol/L or mg/dL).

### Metric Calculations
- **Averages & Variability:** Mean glucose, standard deviation, and coefficient of variation (CV).
- **Time in Range (TIR):** Calculate the percentage of time spent in normal, hyperglycemic, and hypoglycemic ranges.
- **Estimated A1c (eA1c):** Predict HbA1c levels based on average glucose.
- **Hypoglycemic/Hyperglycemic Episodes:** Identify and summarize episodes with level 1 and level 2 thresholds.
- **Glycemic Risk Index (GRI):** Score for risk associated with glucose levels.

### Visualization
- **Glucose Trace:** A line graph representing glucose trends over time.
- **TIR Pie Chart:** A breakdown of the time spent in different glycemic ranges.
- **Ambulatory Glucose Profile (AGP):** Percentile-based summary of glucose patterns.
- **Box and Violin Plots:** Display glucose distribution across subjects.

---

## Documentation
Comprehensive documentation is currently under development. In the meantime, please refer to this README and the inline comments within the code for guidance on using the package.

---

## Contributing
We welcome contributions! Please follow these steps:
1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Create a pull request.

---

## License
This project is licensed under the MIT License. See the LICENSE file for details.

---

## Support
For support, please contact [cr591@exeter.ac.uk](mailto:cr591@exeter.ac.uk).


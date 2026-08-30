# Data Dashboard

An interactive data-analysis dashboard built with **Python**, **Pandas**, **Matplotlib**, **Plotly**, and **Dash**.

The dashboard reads data from a CSV file, cleans and processes the data, creates interactive Plotly boxplots, displays a median-value pivot table, and allows the processed results to be downloaded as CSV or Excel files.

---

## Features

- Load data from `Data.csv`
- Automatically remove:
  - Completely empty rows
  - Completely empty columns
  - Blank string values
- Filter data by `Set`
- Dynamically select:
  - X-axis variable parameters
  - Y-axis measurement values
  - Hue/grouping parameters
- Display interactive Plotly boxplots
- Display all data points on the boxplot
- Show median values in a pivot table
- Download the pivot table as:
  - CSV
  - Excel
- Interactive dashboard accessible through a web browser

---

## Dashboard Preview

The dashboard contains the following components:

1. **Set selector**  
   Select a dataset or experiment set.

2. **X-axis selector**  
   Select the parameter used for grouping the boxplot categories.

3. **Y-axis selector**  
   Select the measurement or value to display.

4. **Hue selector**  
   Group and colour the boxplots according to another parameter.

5. **Interactive boxplot**  
   Visualise the distribution of values for each selected category.

6. **Pivot Data Table**  
   View median values for the selected set.

7. **Export buttons**  
   Download the pivot data as CSV or Excel.

You can add a screenshot to the repository and update this section:

---

## Screenshot

<img src="Screenshot_2.png" width="800"/>

---

## Project Structure
```
.
├── Dashboard.py
├── Data.csv
├── README.md
└── assets/
    └── dashboard_screenshot.png
```

---

## Requirements

- Python 3.9 or newer
- A CSV file named `Data.csv`
- The required Python packages


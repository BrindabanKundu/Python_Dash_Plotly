## Dataplot with `Dash`
### The Plotly Dash Implementation
#### Visit http://127.0.0.1:8050/ in your web browser

import dash
from dash import dcc, html, dash_table, Input, Output, State
import numpy as np
import pandas as pd
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt

import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

# Set the default font family
plt.rcParams['font.family'] = 'Arial'


# --- 1. DATA LOADING & PRE-CLEANING ---
########################################################################################
# Load the csv file and Basic cleaning: drop completely empty rows and columns
df_initial = (
    pd.read_csv('Data.csv', sep=',', encoding='utf8', low_memory=False)
    .replace(r'^\s*$', pd.NA, regex=True)
    .loc[:, lambda d: d.notna().any()]
)

# Dropping those Rows in DataFrame which are completely empty i.e. NaN
df_initial.dropna(how = 'all', inplace=True)
########################################################################################
# Dropping Unnecessary Column from df_initial
df_initial.drop(columns=['Number'], inplace=True)
########################################################################################
# Identify the filtering column
filter_col = 'Set'

unique_experiments = df_initial[filter_col].unique().tolist()
########################################################################################

# --- 2. DATA PROCESSING HELPER ---
def get_cleaned_joined_data(selected_experiment):
    # 1. Filter by ExperimentNumber
    df_filtered = df_initial[df_initial[filter_col] == selected_experiment].copy()

    # We can use the 'drop' to avoid the old index being added as a column
    df_filtered.reset_index(drop=True, inplace=True)    
    
    # 2. Separate into Parameters and Values
    ####################################################################
    # Getting 'Parameters' and 'Values' from the df_filt
    df_Parameters =  df_filtered.loc[:, 'Set':'Parameter_9']
    df_Values = df_filtered.loc[:, 'Mval_01.1':'Remarks']
    
    # Convert all to strings and fill empty cells with an empty string "" 
    # (This prevents 'nan' from being written into your strings)
    df_Parameters = df_Parameters.fillna("").astype(str)
    
    # Drop the last column ('Remarks') from df_Values
    df_Values.drop(columns=['Remarks'], inplace=True)
    
    # Temporarily fill values to prevent dropping
    #df_Values = df_Values.fillna(-999)
    df_Values = df_Values.fillna(np.nan)
    
    # Convert non-numeric/string values to NaN
    df_Values = df_Values.apply(pd.to_numeric, errors='coerce')
    
    # 3. Clean dfs: Drop empty columns from df_Parameters and df_Values
    ####################################################################
    df_Parameters = df_Parameters.loc[:, df_Parameters.notna().any()]
    
    df_Values = df_Values.loc[:, df_Values.notna().any()]
    ####################################################################
    
    # 4. Clean dfs: Drop those columns where all rows contain the same value
    ####################################################################
    # Removing columns (from both) where all rows contain the same value
    mask = (df_Parameters.fillna(df_Parameters.iloc[0]) != df_Parameters.iloc[0]).any(axis=0)
    
    df_temp = df_Parameters.loc[:, mask]

    # If all columns are dropped, keep only 'Purpose'
    if df_temp.shape[1] == 0:
        df_Parameters = df_Parameters[['Purpose']]
    else:
        df_Parameters = df_temp
    ##########################################
    
    ##########################################
    mask = (df_Values.fillna(df_Values.iloc[0]) != df_Values.iloc[0]).any(axis=0)
    df_Values = df_Values.loc[:, mask]
    ####################################################################
    
    # Creating a new column ('Variable_Parameters'), joining all df_Parameters values while ignoring NaN
    df_Parameters['Variable_Parameters'] =\
    df_Parameters.apply(lambda row: ", ".join(row.dropna().astype(str)), axis=1)
    
    # Bringing 'Variable_Parameters' column as the beginning 
    df_Parameters = df_Parameters[['Variable_Parameters'] + 
                                  [col for col in df_Parameters.columns if col != 'Variable_Parameters']]
    
    ####################################################################
    # Rejoin
    df_joined = pd.concat([df_Parameters, df_Values], axis=1)
    ####################################################################
    # Drop the column ('Variable_Parameters') from df_joined
    df_for_pivot = df_joined.drop(columns=['Variable_Parameters'])
    ####################################################################

    # Use `tolist()` for getting a list of columns
    Parameterslist=df_Parameters.columns.values.tolist()
    Valueslist=df_Values.columns.values.tolist()

    # Columns to remove
    to_remove = ['Variable_Parameters']

    # Use filter to remove elements
    Parameterslist_necessary = list(filter(lambda x: x not in to_remove, Parameterslist))
    ####################################################################

    # Create Pivot Table with 'median'
    pivot = pd.pivot_table(df_for_pivot, index=Parameterslist_necessary, values=Valueslist, 
                           aggfunc=['median'], sort=False)

    # Swap the placeholder back to NaN
    #pivot = pivot.replace(-999, np.nan)
    ####################################################################
    
    # Flatten the Pivot index and columns
    pivotflat = pivot.reset_index()

    # If the columns are multi-level, we flatten them as well
    if isinstance(pivotflat.columns, pd.MultiIndex):
        pivotflat.columns = [' '.join(col).strip() for col in pivotflat.columns.values]
        
    ####################################################################
    
    # Apply pivot data rounding
    round_map = {}

    for col in pivotflat.columns:
        if pivotflat[col].dtype == "float64" and col.startswith("median"):
            if "Mval_06" in col:
                round_map[col] = 3
            elif "Mval_04" in col or "Mval_05" in col:
                round_map[col] = 0
            else:
                round_map[col] = 2

    pivot_rounded = pivotflat.round(round_map)
    
    # Convert Ion/rDC/Light/Retardation columns to integer
    int_cols = [c for c in pivotflat.columns if ("Mval_04" in c) or ("Mval_05" in c) 
                or ("Light" in c) or ("Retardation" in c)]
    
    pivot_rounded[int_cols] = pivot_rounded[int_cols].astype("Int64")
####################################################################
    
    return df_joined, pivot_rounded, list(df_Parameters.columns), list(df_Values.columns)
########################################################################################


# --- 3. DASH APP SETUP ---
app = dash.Dash(__name__)

colors = {
    'background': '#ffffff',
    'text': '#5b5b5b'
}

########################################################################################
app.layout = html.Div([
    html.H1("Data Dashboard", 
            style={'textAlign': 'center', 'fontFamily': 'Arial', 'color': colors['text'], 
                   'backgroundColor': colors['background']}),

    html.Div([
        html.Label("Select Set:"),
        dcc.Dropdown(
            id='experiment_dropdown',
            options=[{'label': i, 'value': i} for i in unique_experiments],
            # value must be a list for multi-select
            #value=[unique_experiments[0]] if unique_experiments else [],
            #multi=True,
            value=unique_experiments[-1] if unique_experiments else None, # Pick last value
            #multi=True,
        )
    ], style={'width': '30%', 'margin': 'auto', 'padding': '20px', 
              'backgroundColor': colors['background'], 
              'fontFamily': 'Arial', 'color': colors['text']}),

    html.Hr(),

    html.Div([
        html.Div([
            html.Label("X-Axis (Variable Parameters):"),
            dcc.Dropdown(id='drop_down_x')
        ], style={'width': '33%', 'display': 'inline-block', 'padding': '10px', 
                  'fontFamily': 'Arial', 'color': colors['text'], 
                  'backgroundColor': colors['background']}),

        html.Div([
            html.Label("Y-Axis (Values):"),
            dcc.Dropdown(id='drop_down_y')
        ], style={'width': '34%', 'display': 'inline-block', 'padding': '10px', 
                  'fontFamily': 'Arial', 'color': colors['text'], 
                  'backgroundColor': colors['background']}),

        html.Div([
            html.Label("Hue (Parameters):"),
            dcc.Dropdown(id='drop_down_hue')
        ], style={'width': '33%', 'display': 'inline-block', 'padding': '10px', 
                  'fontFamily': 'Arial', 'color': colors['text'], 
                  'backgroundColor': colors['background']}),
        
    ], style={'display': 'flex', 'justifyContent': 'center'}),

    dcc.Graph(id='main_boxplot'),
  
    #####################################################
    # Display Pivot table data

    html.Hr(), 
    
    html.Div([
    html.H3("Pivot Data Table", 
            style={'textAlign': 'center', 'fontFamily': 'Arial', 'color': colors['text']}), 
        
        dash_table.DataTable(
            id='display_table',
            columns=[],
            data=[],
            page_size=10,

        # ---- Font size for all table cells ----
        style_cell={'fontFamily': 'Arial', 'fontSize': '14px', 'textAlign': 'center', 
                    'color': colors['text'], 'padding': '8px', 'userSelect': 'text'},
        
         
        style_data_conditional=[
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': 'rgb(220, 220, 220)',
        }],
            
 
        # ---- Header font size ----
        style_header={'fontWeight': 'bold', 'fontSize': '16px', 
                      'backgroundColor': '#f5f5f5'},
        
        #css=[{"selector": "table", "rule": "user-select: text;"}],
        css=[{"selector": ".dash-table-container *", "rule": "user-select: text !important;"}],

        style_table={'overflowX': 'auto'},
        )
    ], style={'padding': '20px'}),
    #####################################################
    
    # Add Export Buttons + Download Components to the Layout
    html.Div([
        html.Button("Download CSV", id="btn_csv", n_clicks=0, 
                    style={'marginRight': '10px'}),

        html.Button("Download Excel", id="btn_excel", n_clicks=0),
    
        dcc.Download(id="download_csv"),
        dcc.Download(id="download_excel"),
    ], style={'textAlign': 'center', 'padding': '20px'})
    #####################################################   
    
    
])
########################################################################################

# --- 4. CALLBACKS ---

# Callback to update dropdown options based on filtered/cleaned data
@app.callback(
    [Output('drop_down_x', 'options'),
     Output('drop_down_y', 'options'),
     Output('drop_down_hue', 'options'),
     Output('drop_down_x', 'value'),
     Output('drop_down_y', 'value'),
     Output('drop_down_hue', 'value')],
    [Input('experiment_dropdown', 'value')]
)
def update_dropdowns(selected_experiment):
    if not selected_experiment:
        return [], [], [], None, None, None

    # Get the cleaned and joined data
    _, _, param_cols, value_cols = get_cleaned_joined_data(selected_experiment)

    # Logic for default values
    # Default X is 'Variable_Parameters' if it survived the cleaning
    default_x = 'Variable_Parameters' if 'Variable_Parameters' in\
    param_cols else (param_cols[0] if param_cols else None)
    
    default_y = value_cols[0] if value_cols else None
    #default_hue = param_cols[-1] if len(param_cols) > 1 else default_x
    #default_hue = None
    default_hue = 'Additional_Condition' if 'Additional_Condition' in param_cols else param_cols[0]
    

    return param_cols, value_cols, param_cols, default_x, default_y, default_hue
########################################################################################

# Callback to update the graph using the joined dataframe
@app.callback(
    Output('main_boxplot', 'figure'),
    [Input('experiment_dropdown', 'value'),
     Input('drop_down_x', 'value'),
     Input('drop_down_y', 'value'),
     Input('drop_down_hue', 'value')]
)
# hoverinfo='skip'
def update_boxplot(exp, x, y, hue):
    if not x or not y:
        fig = go.Figure()
        fig.update_layout(title="Please select parameters to plot")
        return fig

    # Get joined dataframe
    df_joined, _, _, _ = get_cleaned_joined_data(exp)

    fig = go.Figure()

    # ------------------------------------------
    # Group the data properly
    # ------------------------------------------
    if hue:
        groups = df_joined.groupby([x, hue])
    else:
        groups = df_joined.groupby([x])

    for group_keys, df_group in groups:

        if hue:
            # group_keys is a tuple (x_val, hue_val)
            x_val, hue_val = group_keys
            trace_name = f"{hue}={hue_val}"
            box_x = [x_val] * len(df_group)
        else:
            # group_keys is a single value
            x_val = group_keys
            trace_name = str(x_val)
            box_x = [x_val] * len(df_group)

        fig.add_trace(
            go.Box(
                x=box_x,
                y=df_group[y],
                name=trace_name,
                #boxpoints="outliers",
                #boxpoints='suspectedoutliers', # only suspected outliers                
                boxpoints='all', # can also be outliers, or suspectedoutliers, or False
                jitter=0.0, # add some jitter for a better separation between points
                pointpos=0, # relative position of points wrt box
                marker=dict(size=10), # marker size
                #hoverinfo="skip",   # Disable hover text
            )
        )

    # ------------------------------------------
    # Layout
    # ------------------------------------------
    fig.update_layout(
        template="plotly_white",
        title=f"Boxplot: {y} vs. {x}",
        font=dict(family='Arial', size=16),
        title_x=0.5,
        
        # Axis label font sizes
        xaxis_title={"text": x, "font": {"size": 18}},
        yaxis_title={"text": y, "font": {"size": 18}},

        # Tick label font sizes
        xaxis={"tickfont": {"size": 16}},
        yaxis={"tickfont": {"size": 16}},
        
        hovermode=False, # hover interactions ['x', 'y', 'closest', False, 'x unified', 'y unified']
        font_family="Arial",

        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],

        margin={'l': 40, 'b': 40, 't': 40, 'r': 10}
    )

    return fig
########################################################################################

@app.callback(
    Output('display_table', 'columns'),
    Output('display_table', 'data'),
    Input('experiment_dropdown', 'value')
)
def update_table(selected_experiment):
    if not selected_experiment:
        return [], []

    # Retrieve df_display from your preprocessing function
    # Adjust this line depending on how pivot is produced
    pivot_rounded = _, pivot_rounded, _, _ = get_cleaned_joined_data(selected_experiment)

    # Convert dataframe to table-friendly format
    columns = [{"name": col, "id": col} for col in pivot_rounded.columns]
    data = pivot_rounded.to_dict('records')

    return columns, data
########################################################################################

# Callback for CSV Download Download of pivot_rounded
@app.callback(
    Output("download_csv", "data"),
    Input("btn_csv", "n_clicks"),
    State("experiment_dropdown", "value"),
    prevent_initial_call=True
)
def download_csv(n_clicks, selected_experiment):

    # Unpack pivot_rounded from helper function
    _, pivot_rounded, _, _ = get_cleaned_joined_data(selected_experiment)
    
    # Build filename using selected_experiment
    filename = f"{selected_experiment}_median_value.csv"

    # Export pivot_rounded as CSV
    return dcc.send_data_frame(pivot_rounded.to_csv, filename=filename, index=False)

########################################################################################

# Callback for Excel Export of pivot_rounded
@app.callback(
    Output("download_excel", "data"),
    Input("btn_excel", "n_clicks"),
    State("experiment_dropdown", "value"),
    prevent_initial_call=True
)
def download_excel(n_clicks, selected_experiment):
 
    # Unpack pivot_rounded from helper function
    _, pivot_rounded, _, _ = get_cleaned_joined_data(selected_experiment)
    
    # Build filename using selected_experiment
    filename = f"{selected_experiment}_median_value.xlsx"    

    return dcc.send_data_frame(pivot_rounded.to_excel, filename=filename, index=False)

########################################################################################

if __name__ == '__main__':
    #app.run(debug=True, port=8050)
    app.run(host='0.0.0.0', port=8050, debug=True)
   
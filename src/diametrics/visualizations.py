import plotly.express as px
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from diametrics import preprocessing, metrics

UNIT_THRESHOLDS = {
    'mmol': {
        'low': 2.1,
        'norm_tight': 7.8,
        'hypo_lv1': 3.9,
        'hypo_lv2': 3,
        'hyper_lv1': 10,
        'hyper_lv2': 13.9,
        'high': 27.8
    },
    'mg': {
        'low': 37.7,
        'norm_tight': 140,
        'hypo_lv1': 70,
        'hypo_lv2': 54,
        'hyper_lv1': 180,
        'hyper_lv2': 250,
        'high': 500
    }
}

COLORS = ['blue', 'light-blue', 'grey', 'pink', 'red']
COLORS = ['#0000FF', '#00BFFF', '#808080', '#FF69B4', '#FF0000']  # From blue to red

def boxplot(df, violin=False):
    """
    Generate a box plot or violin plot for glucose values.

    Args:
        df (pd.DataFrame): DataFrame containing glucose data.
        violin (bool): If True, generate a violin plot. If False, generate a box plot.

    Returns:
        fig: Plotly figure object representing the box plot or violin plot.
    """
    if violin:
        fig = px.violin(df, y='glc', x='ID', box=True)

    else:
        fig = px.box(df, x='ID', y="glc")

    fig.update_layout(
        title = 'Overall Glucose Distribution',
        yaxis_title = 'Glucose',
        xaxis_title = 'ID',
        #width=figure_width,  # Set the width of the figure
        #height=figure_height  # Set the height of the figure
    )   
    return fig



def glucose_trace(df, ID=None, figure_width=800, figure_height=400):
    """
    Generate a glucose trace plot.

    Args:
        df (pd.DataFrame): DataFrame containing glucose data.
        ID (str, optional): ID of the specific patient. If not provided, the first ID in the DataFrame will be used.

    Returns:
        fig: Plotly figure object representing the glucose trace plot.
    """
    # If ID column present then cut dataframe
    if 'ID' in df.columns:
        ID = ID or df['ID'].iloc[0]
        df = df.loc[df['ID']==ID]
    # Determine the units
    units = preprocessing.detect_units(df)

    # Use this to get the thresholds from the global dictionary
    thresholds = UNIT_THRESHOLDS.get(units, {})
    low = thresholds.get('low')
    norm_tight = thresholds.get('norm_tight')
    hypo_lv1 = thresholds.get('hypo_lv1')
    hypo_lv2 = thresholds.get('hypo_lv2')
    hyper_lv1 = thresholds.get('hyper_lv1')
    hyper_lv2 = thresholds.get('hyper_lv2')
    high = thresholds.get('high')

    # Determine bounds for the scatter plot
    if units == 'mmol':
        low = df['glc'].min()-2
        high = df['glc'].max()+2
    else:
        low = df['glc'].min()-36
        high = df['glc'].max()+36


    fig = go.Figure()
    # Create and style traces
    fig.add_trace(go.Scatter(x=df.time, y=df.glc,
                            line=dict(color='black', ), 
                            opacity=0.5,
                            showlegend=False, name='Glucose trace'),
                            #row=1, col=1
                            )
    # Add shape regions
    fig.add_hrect(
        y0=low, y1=hypo_lv2,
        fillcolor=COLORS[0], opacity=0.2,
        layer="below", line_width=0,
        #row=1, col=1
    ),
    fig.add_hrect(
        y0=hypo_lv2, y1=hypo_lv1,
        fillcolor=COLORS[1], opacity=0.2,
        layer="below", line_width=0,
        #row=1, col=1
    ),
    fig.add_hrect(
        y0=hypo_lv1, y1=hyper_lv1,
        fillcolor=COLORS[2], opacity=0.2,
        layer="below", line_width=0,
        #row=1, col=1
    ),
    fig.add_hrect(
        y0=hyper_lv1, y1=hyper_lv2,
        fillcolor=COLORS[3], opacity=0.2,
        layer="below", line_width=0,#annotation_text='Level 1 hyperglycemia (10-13.9)', annotation_position="top left",
        #row=1, col=1
    ),
    fig.add_hrect(
        y0=hyper_lv2, y1=high,
        fillcolor=COLORS[4], opacity=0.2,
        layer="below", line_width=0,#annotation_text='Level 2 hyperglycemia (>13.9)', annotation_position="top left",
        #row=1, col=1
    )

    fig.update_layout(
        title = 'Overall glucose trace',
        yaxis_title = f'Glucose ({units})',
        xaxis_title = 'Date',
        width=figure_width,  # Set the width of the figure
        height=figure_height  # Set the height of the figure
        )
    return fig


    

def tir_pie(df, ID=None):
    """
    Generate a pie chart to visualize the time spent in different glucose level ranges.

    Args:
        df (pd.DataFrame): DataFrame containing glucose data.
        ID (str, optional): ID of the specific patient. If not provided, the first ID in the DataFrame will be used.

    Returns:
        fig: Plotly figure object representing the pie chart.
    """
    if 'ID' in df.columns:
        ID = ID or df['ID'].iloc[0]
        df = df.loc[df['ID']==ID]
    labels = ['Level 2 hypoglycemia (<3mmol/L)', 'Level 1 hypoglycemia (3-3.9mmol/L)', 'Normal range 1 (3.9-7.8mmol/L)', 'Normal range 2 (7.8-10mmol/L)', 'Level 1 hyperglycemia (10-13.9mmol/L)','Level 2 hyperglycemia (>13.9mmol/L)',]
    
    tir = metrics.time_in_range(df)
    values = [tir['tir_lv2_hypo'], tir['tir_lv1_hypo'], tir['tir_norm_tight'], tir['tir_normal']-tir['tir_norm_tight'], tir['tir_lv1_hyper'], tir['tir_lv2_hyper']]
    fig = go.Figure()
    fig.add_trace(go.Pie(values=values, labels=labels),) # marker_colors=COLORS, ,opacity=0.5
    fig.update_layout(
        title = 'Percentage time in range')
        
    return fig

def agp(df, ID=None, figure_width=800, figure_height=400):
    """
    Generates an ambulatory glucose profile plot based on the given DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame containing glucose readings.
        ID (str, optional): The ID of the patient. If provided, the plot will be generated for the specific patient.

    Returns:
        go.Figure: The ambulatory glucose profile plot.
    """
    if 'ID' in df.columns:
        ID = ID or df['ID'].iloc[0]
        df = df.loc[df['ID']==ID]
    
    units = preprocessing.detect_units(df)

    df.time = pd.to_datetime(df.time)
    grouped = df.set_index('time').groupby(pd.Grouper(freq='15min')).mean()['glc']
    group_frame = grouped.reset_index().dropna()
    amb_prof = group_frame.groupby(group_frame['time'].dt.time).apply(lambda group: pd.DataFrame([np.percentile(group.glc, [90, 75, 50, 25, 10])], columns=['q90', 'q3', 'q2', 'q1', 'q10'])).reset_index().drop(columns=['level_1'])

    # Set values for graph
    x = amb_prof['time'] #.astype(str)
    q2 = amb_prof['q2']
    q1 = amb_prof['q1']
    q3 = amb_prof['q3']
    q10 = amb_prof['q10']
    q90 = amb_prof['q90']

    tick_values = x[0::8]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=x, y=q1,
        fill=None,
        line_color='rgb(0,176,246)',
        name='25-75%-IQR',
    ))
    fig.add_trace(go.Scatter(
        x=x,
        y=q3,
        fill='tonexty',
        fillcolor='rgba(0,176,246,0.1)',
        line_color='rgba(255,255,255,0)',
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=x, y=q2,
        line_color='orange',
        name='50%-Median',
    ))
    fig.add_trace(go.Scatter(
        x=x,
        y=q3,
        line_color='rgb(0,176,246)',
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=x,
        y=q10,
        line_color='green',
        showlegend=True,
        line=dict(dash='dash'),
        name='10/90%',
    ))
    fig.add_trace(go.Scatter(
        x=x,
        y=q90,
        line_color='green',
        showlegend=False,
        line=dict(dash='dash'),
        name='10/90%',
    ))

    fig.update_layout(
        title='Ambulatory glucose profile',
        yaxis_title=f'Glucose ({units})',
        xaxis_title='Time (hr)',
        xaxis=dict(
            tickmode='array',
            tickvals=tick_values,
            ticktext=[i.strftime('%I %p') for i in tick_values]
        ),
        width=figure_width,  # Set the width of the figure
        height=figure_height  # Set the height of the figure
    )

    return fig


def tir_bargraph(results_df, units):
    """
    Generates a bar graph representing the time in range (TIR) for different glucose levels.

    Args:
        results_df (pd.DataFrame): The input DataFrame containing TIR results.

    Returns:
        go.Figure: The TIR bar graph.
    """
    melted = results_df[['ID', 'TIR level 2 hypoglycemia (%)',
               'TIR level 1 hypoglycemia (%)', 
               'TIR normal 1 (%)',
               'TIR normal 2 (%)',
               'TIR level 1 hyperglycemia (%)',
               'TIR level 2 hyperglycemia (%)']].melt(id_vars='ID')
    fig = px.bar(melted, x='ID', y='value', color='variable')

    fig.update_layout(
        title='Bargraph',
        yaxis_title=f'Glucose ({units})',
    )

    return fig


def create_bargraph(df, y_axis):
    if y_axis=='Time in range':
        y_value = ['TIR level 2 hypoglycemia', 
        'TIR level 1 hypoglycemia', 'TIR normal', 
        'TIR level 1 hyperglycemia', 
        'TIR level 2 hyperglycemia']
    elif y_axis == 'Total glycemic events':
        y_value=['Total number hypoglycemic events', 
                    'Total number hyperglycemic events']
    elif y_axis =='Hypoglycemic events':
        y_value=['Number LV1 hypoglycemic events', 
                    'Number LV2 hypoglycemic events']
    elif y_axis =='Hyperglycemic events':
        y_value=['Number LV1 hyperglycemic events', 
                    'Number LV2 hyperglycemic events',]
    elif y_axis == 'Prolonged glycemic events':
        y_value=['Number prolonged hypoglycemic events',
                    'Number prolonged hyperglycemic events']
    else:
        y_value=y_axis
    fig = px.bar(df, x='ID', y=y_value)
    return fig

def tir_boxplot(df, y_axis):
    if y_axis=='Time in range':
        y_value=['TIR level 2 hypoglycemia',
        'TIR level 1 hypoglycemia', 'TIR normal',
        'TIR level 1 hyperglycemia',
        'TIR level 2 hyperglycemia']
    elif y_axis == 'Total glycemic events':
        y_value=['Total hypos','Total hypers']
    elif y_axis == 'Hypoglycemic events':
        y_value=['LV1 hypos','LV2 hypos']
    elif y_axis == 'Hyperglycemic events':
        y_value = ['LV1 hypers', 'LV2 hypers']
    elif y_axis == 'Prolonged glycemic events':
        y_value=['Prolonged hypos', 
        'Prolonged hypers']

    else:
        y_value=y_axis
    fig = px.box(df, y=y_value, points="all")
    return fig

def create_scatter(df, x_axis, y_axis):
    fig=px.scatter(df, x=x_axis, y=y_axis, trendline="ols")

    results = px.get_trendline_results(fig)
    results_as_html = results.px_fit_results.iloc[0].summary().as_html()
    stats_df = pd.read_html(results_as_html, header=0, index_col=0)[0]    

    return fig, stats_df
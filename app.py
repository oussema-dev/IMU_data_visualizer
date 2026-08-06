import os
import dash
from dash import dcc, html, Input, Output
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from config import CSV_PATH ,SAMPLING_RATE, EXCLUDE_COLS, SUBJECTS_COL, CLASS_COL

csv_path = os.path.join('datasets', CSV_PATH)
print(f"Loading data from {csv_path}...")
df = pd.read_csv(csv_path)

sampling_rate = SAMPLING_RATE # Hz

exclude_cols = EXCLUDE_COLS
signal_cols = [c for c in df.columns if c not in exclude_cols and np.issubdtype(df[c].dtype, np.number)]

subjects = sorted(df[SUBJECTS_COL].unique().tolist())
classes = sorted(df[CLASS_COL].unique().tolist())

# Calculate the maximum duration in seconds across all subjects/class combinations
# This sets the upper limit for the duration slider
max_rows = df.groupby([SUBJECTS_COL, CLASS_COL]).size().max()
max_seconds = float(np.ceil(max_rows / sampling_rate))

# Initialize Dash App
app = dash.Dash(__name__)
app.layout = html.Div(style={'fontFamily': 'Arial, sans-serif', 'padding': '20px'}, children=[
    html.H2("IMU Signal Explorer"),
    
    html.Div(style={'display': 'flex', 'gap': '20px', 'marginBottom': '20px'}, children=[
        # Signal Selection
        html.Div(style={'flex': '1'}, children=[
            html.Label("Select Signal:"),
            dcc.Dropdown(
                id='signal-dropdown',
                options=[{'label': s, 'value': s} for s in signal_cols],
                value=signal_cols[0],
                clearable=False
            )
        ]),
        
        # Subject Selection (Multiple)
        html.Div(style={'flex': '1'}, children=[
            html.Label("Select Subjects:"),
            dcc.Dropdown(
                id='subject-dropdown',
                options=[{'label': str(p), 'value': p} for p in subjects],
                value=[subjects[0]], 
                multi=True
            )
        ]),
        
        # Class Selection (Multiple)
        html.Div(style={'flex': '1'}, children=[
            html.Label("Select Classes:"),
            dcc.Dropdown(
                id='class-dropdown',
                options=[{'label': m, 'value': m} for m in classes],
                value=classes, 
                multi=True
            )
        ]),
    ]),
    
    # Duration Range Slider
    html.Div(style={'marginBottom': '30px'}, children=[
        html.Label("Select Duration to Visualize (Seconds):"),
        dcc.RangeSlider(
            id='duration-slider',
            min=0,
            max=max_seconds,
            step=0.5,
            value=[0, min(10.0, max_seconds)], # Default to first 10 seconds
            marks={i: f"{i}s" for i in range(0, int(max_seconds)+1, max(1, int(max_seconds)//10))},
            tooltip={"placement": "bottom", "always_visible": True}
        )
    ]),
    
    # The Graph
    dcc.Graph(id='imu-graph', style={'height': '60vh'})
])

# Callback to update the graph based on controls
@app.callback(
    Output('imu-graph', 'figure'),
    [Input('signal-dropdown', 'value'),
     Input('subject-dropdown', 'value'),
     Input('class-dropdown', 'value'),
     Input('duration-slider', 'value')]
)
def update_graph(selected_signal, selected_subjects, selected_classes, duration_range):
    fig = go.Figure()

    # Handle empty states
    if not selected_subjects or not selected_classes or not selected_signal:
        return fig.update_layout(title="Please select at least one subject, class, and signal.")

    start_sec, end_sec = duration_range
    start_idx = int(start_sec * sampling_rate)
    end_idx = int(end_sec * sampling_rate)

    for subject in selected_subjects:
        for mode in selected_classes:
            # Filter the dataframe
            subset = df[(df[SUBJECTS_COL] == subject) & (df[CLASS_COL] == mode)]
            
            if subset.empty:
                continue
                
            # Slice based on the selected duration
            y_data = subset[selected_signal].iloc[start_idx:end_idx].values
            
            # Reconstruct time axis for this specific slice
            x_data = np.arange(len(y_data)) / sampling_rate + start_sec
            
            fig.add_trace(go.Scatter(
                x=x_data,
                y=y_data,
                mode='lines',
                name=f'S{subject} | {mode}',
                opacity=0.85
            ))

    fig.update_layout(
        title=f"{selected_signal} ({start_sec}s to {end_sec}s)",
        xaxis_title="Time (Seconds)",
        yaxis_title="Amplitude",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            title="Subject | Mode",
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        ),
        margin=dict(l=40, r=150, t=60, b=40)
    )

    return fig

if __name__ == '__main__':
    app.run()
    # http://127.0.0.1:8050/
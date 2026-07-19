import dash
from dash import dcc, html, Input, Output
import pandas as pd
import numpy as np
import plotly.graph_objects as go

csv_path = 'dataset.csv'
print(f"Loading data from {csv_path}...")
df = pd.read_csv(csv_path)

SAMPLING_RATE = 60 # Hz

exclude_cols = ['participant_id', 'walk_mode']
signal_cols = [c for c in df.columns if c not in exclude_cols and np.issubdtype(df[c].dtype, np.number)]

participants = sorted(df['participant_id'].unique().tolist())
walk_modes = sorted(df['walk_mode'].unique().tolist())

# Calculate the maximum duration in seconds across all participant/mode combinations
# This sets the upper limit for our duration slider
max_rows = df.groupby(['participant_id', 'walk_mode']).size().max()
max_seconds = float(np.ceil(max_rows / SAMPLING_RATE))

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
        
        # Participant Selection (Multiple)
        html.Div(style={'flex': '1'}, children=[
            html.Label("Select Participants:"),
            dcc.Dropdown(
                id='participant-dropdown',
                options=[{'label': str(p), 'value': p} for p in participants],
                value=[participants[0]], 
                multi=True
            )
        ]),
        
        # Walk Mode Selection (Multiple)
        html.Div(style={'flex': '1'}, children=[
            html.Label("Select Walk Modes:"),
            dcc.Dropdown(
                id='mode-dropdown',
                options=[{'label': m, 'value': m} for m in walk_modes],
                value=walk_modes, 
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
     Input('participant-dropdown', 'value'),
     Input('mode-dropdown', 'value'),
     Input('duration-slider', 'value')]
)
def update_graph(selected_signal, selected_parts, selected_modes, duration_range):
    fig = go.Figure()

    # Handle empty states
    if not selected_parts or not selected_modes or not selected_signal:
        return fig.update_layout(title="Please select at least one participant, mode, and signal.")

    start_sec, end_sec = duration_range
    start_idx = int(start_sec * SAMPLING_RATE)
    end_idx = int(end_sec * SAMPLING_RATE)

    for participant in selected_parts:
        for mode in selected_modes:
            # Filter the dataframe
            subset = df[(df['participant_id'] == participant) & (df['walk_mode'] == mode)]
            
            if subset.empty:
                continue
                
            # Slice based on the selected duration
            y_data = subset[selected_signal].iloc[start_idx:end_idx].values
            
            # Reconstruct time axis for this specific slice
            x_data = np.arange(len(y_data)) / SAMPLING_RATE + start_sec
            
            fig.add_trace(go.Scatter(
                x=x_data,
                y=y_data,
                mode='lines',
                name=f'P{participant} | {mode}',
                opacity=0.85
            ))

    fig.update_layout(
        title=f"{selected_signal} ({start_sec}s to {end_sec}s)",
        xaxis_title="Time (Seconds)",
        yaxis_title="Amplitude",
        template="plotly_white",
        hovermode="x unified",
        legend=dict(
            title="Participant | Mode",
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
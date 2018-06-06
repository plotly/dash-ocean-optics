# -*- coding: utf-8 -*-

import dash
import dash_daq as daq
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objs as go
import plotly
import datetime 
from dash.dependencies import Input, Output, Event 

import numpy # for demo purposes 
import random 

import seabreeze.spectrometers as sb # actual data collection 

# demo or functional
DEMO = False

if not DEMO:
    device = sb.list_devices()
    # spec = sb.Spectrometer(devices[0]) # (throws an error) 

# device-specific limitations

# integration times 
int_time_max = 65000000
int_time_min = 1000


# begin Dash app 
app = dash.Dash()
app.scripts.config.serve_locally = True
app.css.config.serve_locally = True


# style options
# TODO: move to external stylesheet 
colors={
    'black':'#000000',
    'white':'#ffffff',
    'red':'#ff0000'
}

graphContainerStyle={
    'background':colors['white'],
    'border-color':colors['black'],
    'border-style':'solid',
    'border-width':'thin',
    'border-radius':'10px',
    'height':'auto',
    'width':'70%',
    'min-width':'200px',
    'padding':'1%',
    'margin':'20px',
    'layout':'inline-block',
    'position':'relative',
    'float':'left',
    'font-family':'sans-serif'
}
optionBoxStyle={
    'width':'20%',
    'min-width':'100px', 
    'position':'relative',
    'float':'left',
    'border-color':colors['black'],
    'border-style':'solid',
    'border-width':'thin',
    'border-radius':'10px', 
    'height':'auto',
    'margin':'5px',
    'margin-top':'20px'
}
optionNameStyle={
    'padding-top':'10px',
    'padding-bottom':'10px',
    'text-align':'center',
    'font-family':'sans-serif',
    'font-weight':100,
    'font-size':'20pt'
}
inputStyle={
    'width':'80%',
    'position':'static',
    'margin-left':'10%',
    'margin-right':'10%',
    'margin-top':'10px',
    'margin-bottom':'10px',
    'padding':'5px',
    'font-size':'16pt'
}



# begin html 
app.layout = html.Div(children=[


# plot 
html.Div(
    id='graph-container',
    style=graphContainerStyle,
    children=[
        html.Div(
            children=[
                dcc.Graph(id='spec-readings', animate=True),
                dcc.Interval(
                    id='spec-reading-interval',
                    interval = 0.1*1000,
                    n_intervals=0
                )
            ]
        )
    ]
),


# all options 

# integration time 
html.Div(
    id='integration-time',
    style=optionBoxStyle,
    children=[
        html.Div(
            id='option-name',
            style=optionNameStyle,
            children=[
                "Integration time"
            ]
        ), 
        dcc.Input(
            style=inputStyle,
            placeholder='time (ms)', 
            type='text'
        ),
        dcc.Interval(
            id='empty-callback',
            interval=0.1*1000,
            n_intervals=0
        )
    ]
),


# calibration 
html.Div(
    id='calibration-container',
    style=optionBoxStyle,
    children=[
        html.Div(
            id='option-name',
            style=optionNameStyle,
            children=[
                "Calibration wavelength"
            ]
        ),
        html.Br(), 
        dcc.Input(
            style=inputStyle, 
            placeholder='wavelength(nm)',
            type='text'
        )
    ]
),

]
)

# update plots
@app.callback(Output('spec-readings', 'figure'),
              events=[Event('spec-reading-interval', 'interval')])
def update_spec_readings():
    
    traces = []

    traces.append(plotly.graph_objs.Scatter(
        x=[i for i in range(700)], #spec.wavelengths(),
        y=[random.random() for i in range(700)], #spec.intensities(),
        name='Spectrometer readings',
        mode='markers+lines'
    ))

    return {'data':traces}

def normal_dist(wl,scale,samples):
    return list(numpy.random.normal(wl,scale,700))

if __name__ == '__main__':
    app.run_server(debug=True)

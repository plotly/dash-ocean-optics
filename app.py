# -*- coding: utf-8 -*-AA

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
specmodel='USB2000+'
spec=None

# demo or functional
DEMO = True 

if not DEMO:
    device = sb.list_devices()
    spec = sb.Spectrometer(devices[0]) # (throws an error) 

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
    'middarkgrey':'#444444', 
    'midgrey':'#888888',
    'lightgrey':'#BBBBBB',
    'white':'#ffffff',
    'accent':'#00ff00'
}
pageStyle={
    'backgroundColor':'#000000' 
} 
graphContainerStyle={
    'backgroundColor':'#000000',
    'height':'auto',
    'width':'100%',
    'min-width':'200px',
    'margin':'0px',
    'layout':'inline-block',
    'position':'relative',
    'float':'left',
}
graphTitleStyle={
    'color':'#ffffff',
    'margin-top':'30px',
    'margin-left':'50px',
    'font-size':50,
    'font-weight':100,
    'font-variant':'small-caps', 
    'font-family':'Helvetica, sans-serif',
    'font-weight':'light'
} 
optionBoxStyle={
    'width':'auto',
    'min-width':'100px', 
    'position':'relative',
    'float':'left',
    'backgroundColor':'#000000',
    'height':'150px',
    'margin':'0px',
    'padding':'10px',
    'border-style':'dotted',
    'border-width':'1px',
    'border-color':'#ffffff'
}
optionNameStyle={
    'padding-top':'10px',
    'padding-bottom':'10px',
    'text-align':'center',
    'font-variant':'small-caps', 
    'font-family':'Helvetica, sans-serif',
    'font-weight':100,
    'font-size':'18pt',
    'color':'#ffffff'
}
inputStyle={
    'width':'80%',
    'position':'static',
    'margin-left':'5%',
    'margin-right':'5%',
    'padding':'5%',
    'font-size':'12pt',
    'background-color':'#111111',
    'color':'#ffffff'
}



# begin html 
app.layout = html.Div(style=pageStyle,children=[
    
# plot 
html.Div(
    id='graph-container',
    style=graphContainerStyle,
    children=[
        html.Div(
            children=[
                html.Div(
                    style=graphTitleStyle,
                    children=[
                        "ocean optics %s"%specmodel
                    ]
                ), 
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
            className='option-name',
            style=optionNameStyle,
            children=[
                "integration time"
            ]
        ), 
        dcc.Input(
            id='integration-time-input',
            style=inputStyle,
            placeholder='time (ms)', 
            type='text'
        ),
    ]
),


# calibration 
html.Div(
    id='calibration-wavelength',
    style=optionBoxStyle,
    children=[
        html.Div(
            className='option-name',
            style=optionNameStyle,
            children=[
                "calibration wavelength"
            ]
        ),
        html.Br(), 
        dcc.Input(
            id='calibration-wavelength-input',
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
    wavelengths=[]
    intensities=[] 
    
    if DEMO:
        wavelengths=numpy.linspace(0,700,7000)
        intensities=[sample_spectrum(wl) for wl in wavelengths] 
    else:
        wavelengths=spec.wavelengths()
        intensities=spec.intensities()
        
    traces.append(plotly.graph_objs.Scatter(
        x=wavelengths,
        y=intensities,
        name='Spectrometer readings',
        mode='lines',
        line={
            'width':1,
            'color':colors['accent']
        }
    ))

    layout=go.Layout(
        font={
            'family':'Helvetica Neue, sans-serif',
            'size':12
        },
        margin={
            't':20
        },
        titlefont={
            'family':'Helvetica, sans-serif',
            'color':colors['white'],
            'size':26
        },
        xaxis={
            'title':'Wavelength (nm)',
            'titlefont':{
                'family':'Helvetica, sans-serif',
                'color':colors['lightgrey']
            },
            'tickfont':{
                'color':colors['midgrey']
            },
            'gridcolor':colors['middarkgrey']
        },
        yaxis={
            'title':'Intensity (AU)',
            'titlefont':{
                'family':'Helvetica, sans-serif',
                'color':colors['lightgrey']
            },
            'tickfont':{
                'color':colors['midgrey']
            },
            'gridcolor':colors['middarkgrey']
        },
        paper_bgcolor=colors['black'],
        plot_bgcolor=colors['black'],
    )

    return {'data':traces,
            'layout':layout}

# generated randomly, just for demonstration purposes  
def sample_spectrum(x):
    return (50*numpy.e**(-1*((x-200)/10)**2)+
            60*numpy.e**(-1*((x-500)/5)**2)+
            random.random())

if __name__ == '__main__':
    app.run_server(debug=True)

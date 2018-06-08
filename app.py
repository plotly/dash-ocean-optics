# -*- coding: utf-8 -*-AA

import dash
import dash_daq as daq
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objs as go
import plotly
import datetime 
from dash.dependencies import Input, Output, Event, State 

import numpy # for demo purposes 
import random 

import seabreeze.spectrometers as sb # actual data collection
specmodel='USB2000+'
spec=None

# demo or functional
DEMO = True 

if not DEMO:
    device = sb.list_devices()
    specmodel = sb.list_devices()[0] # parse this to get model name 
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

styles={
'page':{
    'backgroundColor':'#000000',
    'height':'100%',
    'width':'100%',
    'position':'absolute',
    'left':'0px',
    'top':'0px',
    'padding':'20px', 
    'padding-bottom':'300px'
},
'graph-container':{
    'backgroundColor':'#000000',
    'height':'600px',
    'width':'80%',
    'min-width':'200px',
    'margin':'0px',
    'layout':'inline-block',
    'position':'relative',
    'float':'left',
},
'graph-title':{
    'color':'#ffffff',
    'margin-top':'30px',
    'margin-left':'50px',
    'font-size':50,
    'font-weight':100,
    'font-variant':'small-caps', 
    'font-family':'Helvetica, sans-serif',
    'font-weight':'light'
},
'option-box':{
    'width':'200px', 
    'position':'relative',
    'float':'left',
    'backgroundColor':'#000000',
    'height':'150px',
    'margin':'10px',
    'padding':'10px',
    'transition-duration':10000
},
'option-name':{
    'padding-top':'10px',
    'padding-bottom':'10px',
    'text-align':'center',
    'font-variant':'small-caps', 
    'font-family':'Helvetica, sans-serif',
    'font-weight':100,
    'font-size':'18pt',
    'color':'#ffffff'
},
'input':{
    'width':'80%',
    'position':'static',
    'margin-left':'5%',
    'margin-right':'5%',
    'padding':'5%',
    'font-size':'12pt',
    'background-color':'#111111',
    'border-style':'none',
    'border-bottom':'solid',
    'border-width':'1px', 
    'color':'#ffffff'
},
'status-box':{
    'width':'15%',
    'margin':'0px',
    'height': '600px',
    'position':'static',
    'float':'left',
    'align-items':'center', 
    'border-color':'white',
    'border-style':'none',
    'border-width':'1px'
},
'submit-button':{
    'font-family':'Helvetica, sans-serif', 
    'font-size':'16px',
    'font-variant':'small-caps',
    'color':'#000000', 
    'text-align':'center',
    'height':'50px',
    'width':'100%',
    'background-color':'#44ff44',
    'position':'static', 
    'border-width':'1px',
    'border-color':'#00ff00',
    'border-radius':'5px'
},
'submit-status':{
    'width':'80%',
    'position':'static',
    'margin-left':'10%',
    'margin-right':'10%',
    'padding':'0px',
    'font-family':'Helvetica, sans-serif', 
    'font-size':'14pt',
    'color':'#BBBBBB'
} 
    
}
    



# begin html 
app.layout = html.Div(id='page',style=styles['page'],children=[

# plot 
html.Div(
    id='graph-container',
    style=styles['graph-container'],
    children=[
        html.Div(
            children=[
                html.Div(
                    style=styles['graph-title'],
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


# status box 
html.Div(
    id='status-box',
    style=styles['status-box'],
    children=[
        daq.PowerButton(
            id='power-button',
            size=70,
            color='#44ff44',
            on=False
        ),
        # submit button
        html.Div(
            id='submit-button-container',
            children=[
                html.Button(
                    'submit options', 
                    id='submit-button',
                    style=styles['submit-button'],
                    n_clicks=0
                )
            ]
        ),
        
        # displays whether the parameters were successfully changed 
        html.Div(
            id='submit-status', 
            style=styles['submit-status'],
            children=[
                ""
            ]
        )
    ]
),
    
# integration time 
html.Div(
    id='integration-time',
    style=styles['option-box'], 
    children=[
        html.Div(
            className='option-name',
            style=styles['option-name'], 
            children=[
                "integration time"
            ]
        ),
        html.Br(), 
        daq.NumericInput(
            id='integration-time-input',
            max=int_time_max,
            min=int_time_min, 
            size=120
        ) 
    ]
),


# number of scans to average over 
html.Div(
    id='nscans-to-average',
    style=styles['option-box'], 
    children=[
        html.Div(
            className='option-name',
            style=styles['option-name'], 
            children=[
                "scans to average"
            ]
        ),
        html.Br(), 
        daq.NumericInput(
            id='nscans-to-average-input', 
            size=120
        )
    ]
),



]
)


# send user-selected options to spectrometer
@app.callback(Output('submit-status', 'children'),
              [Input('submit-button','n_clicks')],
              # TODO: add all options found in pyseabreeze 
              state=[
                  State('integration-time-input', 'value'),
                  State('nscans-to-average-input', 'value'),
              ])
def update_spec_params(n_clicks,
                       integration_time,
                       nscans_average):
    if spec is not None:
        # list of commands to send; dictionary form so we can iterate
        # through them and determine which one(s) failed in a user-friendly
        # way 
        commands={
            'spec.integration_time_micros(integration_time)':'Integration time',
            'spec.scans_to_average(nscans_average)':'Number of scans to average'
        }
        failed={} 

        for cmd in commands:
            try:
                # TODO: try to implement without using "exec" 
                exec(cmd)
            except Exception as e:
                # TODO: include exception text as optional for
                # user to read 
                failed[commands[cmd]]=str(e)
                pass

        if (len(failed) == 0):
            return "Success!"
        else:
            failString = "Failure - the following parameters were not successfully updated:"
            for f in failed:
                failString += '- '+f+'/n'
            return failString 
            
    else:
        if(random.random() > 0.5): 
            return "Success!" 
        else:
            return "Fail" 
    
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
    return (50*numpy.e**(-1*((x-200))**2)+
            60*numpy.e**(-1*((x-500)/5)**2)+
            random.random())

if __name__ == '__main__':
    app.run_server(debug=True)

# -*- coding: utf-8 -*-

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

############################
# Settings 
############################

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

############################
# Style
############################
colors={
    'background':'#ffffff',
    'primary':'#000000',
    'secondary':'#444444',
    'tertiary':'#888888',
    'grid-colour':'#bbbbbb',
    'accent':'#ff0000'
}

styles={
'page':{
    'backgroundColor':colors['background'],
    'height':'100%',
    'width':'100%',
    'position':'absolute',
    'left':'0px',
    'top':'0px',
    'padding':'20px', 
    'padding-bottom':'300px'
},
'graph-container':{
    'backgroundColor':colors['background'],
    'width':'80%',
    'min-width':'200px',
    'margin':'0px',
    'layout':'inline-block',
    'position':'relative',
    'float':'left',
},
'graph-title':{
    'color':colors['primary'],
    'margin-top':'30px',
    'margin-left':'50px',
    'font-size':50,
    'font-weight':100,
    'font-variant':'small-caps', 
    'font-family':'Helvetica, sans-serif',
    'font-weight':'light'
},
'option-box':{
    'width':'auto', 
    'position':'relative',
    'float':'left',
    'backgroundColor':colors['background'],
    'height':'125px',
    'margin':'10px',
    'margin-top':'0px', 
    'padding':'10px',
},
'option-name':{
    'padding-top':'0px',
    'padding-bottom':'10px',
    'text-align':'center',
    'font-variant':'small-caps', 
    'font-family':'Helvetica, sans-serif',
    'font-weight':100,
    'font-size':'18pt',
    'color':colors['primary']
},
'numeric-input':{
    'width':'100%',
    'padding':'50px',
    'padding-top':'0px', 
    'position':'static',
    'font-size':'12pt',
    'border-style':'none',
    'color':colors['primary']
},
'status-box':{
    'width':'15%',
    'margin':'0px',
    'margin-top':'25px', 
    'height': '600px',
    'position':'static',
    'float':'left',
    'align-items':'center', 
    'border-color':colors['primary'],
    'border-style':'none',
    'border-width':'1px'
},
'submit-button':{
    'font-family':'Helvetica, sans-serif', 
    'font-size':'20px',
    'font-variant':'small-caps',
    'color':colors['background'],
    'text-align':'center',
    'height':'50px',
    'width':'80%',
    'background-color':colors['accent'],
    'position':'static', 
    'border-width':'1px',
    'border-color':colors['accent'], 
    'border-radius':'5px',
    'margin':'10%'
},
'submit-status':{
    'width':'80%',
    'position':'static',
    'margin-left':'10%',
    'margin-right':'10%',
    'padding':'0px', 
    'font-family':'Courier, monospace', 
    'font-size':'9pt',
    'color':colors['tertiary']
}, 
'boolean-switch':{
    'margin-top':'25px' 
} 
}

############################
# Controls 
############################ 
    
def sample_func(x):
    if(x == 13): 
        raise Exception("unlucky!!!")
    else:
        return 

# all user-defined parameters (referred to as "controls")
controls = []

class Control:
    def __init__(self, new_ctrl_id, new_ctrl_name,
                 new_component_type, new_component_attr, new_ctrl_func):
        self.ctrl_id = new_ctrl_id                # id for callbacks 
        self.ctrl_name = new_ctrl_name            # name for label
        self.component_type = new_component_type  # dash-daq component type 
        self.component_attr = new_component_attr  # dash-daq component attributes
        if DEMO:                                  # function associated w/ control
            self.ctrl_func = sample_func
        else: 
            self.ctrl_func = new_ctrl_func
        controls.append(self)
        
    # creates a new control box with defined component, id, and name
    def create_ctrl_div(self):
        # create dash-daq components 
        if(self.component_type == "BooleanSwitch" or self.component_type == "PowerButton"):
            component=daq.BooleanSwitch(
                id=self.component_attr['id'],
                style=self.component_attr['style'],
                color=self.component_attr['color'],
                on=self.component_attr['on']
            )
        elif(self.component_type == "NumericInput"):
            component=daq.NumericInput(
                id=self.component_attr['id'],
                style=self.component_attr['style'],
                max=self.component_attr['max'],
                min=self.component_attr['min'],
                size=self.component_attr['size'],
                value=self.component_attr['value']
            )

        # generate html code 
        new_control = html.Div(
            id=self.ctrl_id,
            style=styles['option-box'],
            children=[
                html.Div(
                    className='option-name',
                    style=styles['option-name'],
                    children=[
                        self.ctrl_name
                    ]
                ),
                component
            ]
        )
        return new_control

    # gets whether we look for "value", "on", etc. 
    def val_string(self):
        if('value' in self.component_attr):
            return 'value'
        else: 
            return 'on'

    # changes value ('on' or 'value', etc.) 
    def update_value(self, new_value):
        self.component_attr[self.val_string()] = new_value

############################
# All controls
############################

int_time = Control('integration-time', "integration time (ms)",
                   "NumericInput",
                   {'id':'integration-time-input',
                    'style':styles['numeric-input'],
                    'max':int_time_max,
                    'min':int_time_min,
                    'size':100,
                    'value':int_time_min
                   },
                   #spec.integration_time_micros
                   lambda : "int_time"
)
nscans_avg = Control('nscans-to-average', "scans to average",
                     "NumericInput", 
                     {'id':'nscans-to-average-input',
                      'style':styles['numeric-input'],
                      'max':100,
                      'min':1,
                      'size':100,
                      'value':1 
                     },
                     #spec.scans_to_average,
                     lambda : "nscans_avg"
)
strobe_enable = Control('continuous-strobe-toggle', "strobe",
                        "BooleanSwitch",
                        {'id':'continuous-strobe-toggle-input',
                         'style':styles['boolean-switch'],
                         'color':colors['accent'],
                         'on':False
                        },
                        #spec.continuous_strobe_set_enable
                        lambda : "strobe_enable"
)
strobe_period = Control('continuous-strobe-period', "strobe period (ms)",
                        "NumericInput",
                        {'id':'continuous-strobe-period-input',
                         'style':styles['numeric-input'],
                         'max':100,
                         'min':1,
                         'size':100,
                         'value':1
                        },
                        #spec.continuous_strobe_set_period_micros
                        lambda : "strobe_period" 
)

############################
# Layout
############################

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
                    interval = 0.5*1000,
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
        # power button 
        html.Div(
            id='power-button-container', children=[
                daq.PowerButton(
                    id='power-button',
                    size=70,
                    color=colors['accent'],
                    on=False
                )
            ]
        ),
        # submit button
        html.Div(
            id='submit-button-container',
            children=[
                html.Button(
                    'submit', 
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


# all controls
html.Div(
    id='controls',
    children=[
        ctrl.create_ctrl_div() for ctrl in controls 
    ]
),
    
]
)

############################
# Callbacks
############################

# keep component values from resetting 
@app.callback(Output('controls', 'children'), [
    Input(ctrl.component_attr['id'], ctrl.val_string()) for ctrl in controls
])
def preserve_controls_settings(*args):
    for i in range(len(controls)):
        controls[i].update_value(args[i])
    return [ctrl.create_ctrl_div for ctrl in controls] 


# keep power button from resetting 
@app.callback(Output('power-button-container', 'children'),[
    Input('power-button', 'on')
])
def preserve_on(current):
    return [daq.PowerButton(
        id='power-button',
        size=70,
        color=colors['accent'],
        on=current
    )]


# send user-selected options to spectrometer
@app.callback(Output('submit-status', 'children'),
              [Input('submit-button', 'n_clicks')],
              # TODO: add all options found in pyseabreeze 
              state=[
                  State(ctrl.component_attr['id'], ctrl.val_string()) for ctrl in controls
])
def update_spec_params(n_clicks, *args):
    # list of commands to send; dictionary form so we can iterate
    # through them and determine which one(s) failed in a user-friendly
    # way 
    failed={} 
    # TODO: scrollable errors 
    for i in range(len(controls)): 
        try:
            controls[i].ctrl_func(args[i])
        except Exception as e:
            # TODO: include exception text as optional for
            # user to read 
            failed[controls[i].ctrl_name]=str(e)
            pass

    if (len(failed) == 0):
        return "Success!"
    else:
        fails= ["Failure - the following parameters were not successfully updated: ", html.Br()]
        for f in failed:
            fails.append('- '+f+', '+failed[f]+'; ')
            fails.append(html.Br())
        return html.Div(fails)

# update the plot 
@app.callback(Output('spec-readings', 'figure'),
              state=[State('power-button', 'on')], 
              events=[Event('spec-reading-interval', 'interval')
])
def update_spec_readings(on):
    
    traces = []
    wavelengths=[]
    intensities=[] 

    if(on): 
        if DEMO:
            wavelengths=numpy.linspace(0,700,7000)
            intensities=[sample_spectrum(wl) for wl in wavelengths] 
        else:
            wavelengths=spec.wavelengths()
            intensities=spec.intensities()
    else:
        wavelengths=numpy.linspace(0,700,7000)
        intensities=[0 for wl in wavelengths]
        
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
            'color':colors['primary'],
            'size':26
        },
        xaxis={
            'title':'Wavelength (nm)',
            'titlefont':{
                'family':'Helvetica, sans-serif',
                'color':colors['secondary']
            },
            'tickfont':{
                'color':colors['tertiary']
            },
            'gridcolor':colors['grid-colour']
        },
        yaxis={
            'title':'Intensity (AU)',
            'titlefont':{
                'family':'Helvetica, sans-serif',
                'color':colors['secondary']
            },
            'tickfont':{
                'color':colors['tertiary']
            },
            'gridcolor':colors['grid-colour']
        },
        paper_bgcolor=colors['background'],
        plot_bgcolor=colors['background'],
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

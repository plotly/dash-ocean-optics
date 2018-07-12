#-*- coding: utf-8 -*-

import os
import sys
import numpy
from threading import Lock
import time
from textwrap import dedent

import dash
import dash_html_components as html
import dash_core_components as dcc

import plotly.graph_objs as go

import dash_daq as daq
from dash.dependencies import Input, Output, Event, State

import DashOceanOpticsSpectrometer as doos
from DashOceanOpticsSpectrometer import Control

#############################
# Spectrometer properties
#############################

# lock for modifying information about spectrometer
spec_lock = Lock()
# lock for communicating with spectrometer
comm_lock = Lock()

# initialize spec
spec = doos.DashOceanOpticsSpectrometer(spec_lock, comm_lock)

# demo or actual
if(('DYNO' in os.environ) or (len(sys.argv) == 2 and sys.argv[1] == "demo")):
    spec = doos.DemoSpectrometer(spec_lock, comm_lock)
else:
    spec = doos.PhysicalSpectrometer(spec_lock, comm_lock)
    
spec.assign_spec()


############################
# Begin Dash app
############################

app = dash.Dash()
app.scripts.config.serve_locally = True
server = app.server

############################
# Style
############################

app.css.append_css({
    "external_url": "https://rawgit.com/shammamah/dash-stylesheets/master/dash-ocean-optics-stylesheet.css"
})

colors = {}

with open("colors.txt", 'r') as f:
    for line in f.readlines():
        colors[line.split(' ')[0]] = line.split(' ')[1].strip('\n')

        
############################
# All controls
############################

controls = []

# integration time, microseconds
int_time = Control('integration-time', "int. time (μs)",
                   "NumericInput",
                   {'id': 'integration-time-input',
                    'max': spec.int_time_max(),
                    'min': spec.int_time_min(),
                    'size': 150,
                    'value': spec.int_time_min()
                    }
                   )
controls.append(int_time)

# scans to average over
nscans_avg = Control('nscans-to-average', "number of scans",
                     "NumericInput",
                     {'id': 'nscans-to-average-input',
                      'max': 100,
                      'min': 1,
                      'size': 150,
                      'value': 1
                      }
                     )
controls.append(nscans_avg)

# strobe
strobe_enable = Control('continuous-strobe-toggle', "strobe",
                        "BooleanSwitch",
                        {'id': 'continuous-strobe-toggle-input',
                         'color': colors['accent'],
                         'on': False
                         }
                        )
controls.append(strobe_enable)

# strobe period
strobe_period = Control('continuous-strobe-period', "strobe pd. (μs)",
                        "NumericInput",
                        {'id': 'continuous-strobe-period-input',
                         'max': 100,
                         'min': 1,
                         'size': 150,
                         'value': 1
                         }
                        )
controls.append(strobe_period)

# light sources
light_sources = Control('light-source', "light source",
                        "Dropdown",
                        {'id': 'light-source-input',
                         'options': spec.light_sources(),
                         'placeholder': "select light source",
                         'value': ""
                         }
                        )
controls.append(light_sources)


############################
# Layout
############################

page_layout = [html.Div(id='page', children=[

    # banner
    html.Div(
        id='logo',
        style={
            'position': 'absolute',
            'left': '10px',
            'top': '10px',
            'zIndex': 100
        },
        children=[
            html.A(
            html.Img(
                src="https://s3-us-west-1.amazonaws.com/plotly-tutorials/excel/dash-daq/dash-daq-logo-by-plotly-stripe+copy.png",
                style={
                    'height': '65px',
                }
            ),
            href="http://www.dashdaq.io"
            )
        ]
    ),
    
    # plot
    html.Div(
        id='graph-container',
        children=[
            html.Div(
                children=[
                    html.Div(
                        id='graph-title',
                        children=[
                            "ocean optics"
                        ]
                    ),
                    dcc.Graph(id='spec-readings', animate=True),
                    dcc.Interval(
                        id='spec-reading-interval',
                        interval=1 * 1000,
                        n_intervals=0
                    )
                ]
            )
        ]
    ),

    # power button
    html.Div(
        id='power-button-container', children=[
            daq.PowerButton(
                id='power-button',
                size=50,
                color=colors['accent'],
                on=False
            )
        ],
    ),
    
    # status box
    html.Div(
        id='status-box',
        children=[
            # light intensity
            html.Div(
                className='status-box-title',
                children=[
                    "light intensity"
                ]
            ),
            html.Div(
                id='light-intensity-knob-container',
                children=[
                    daq.Knob(
                        id='light-intensity-knob',
                        size=110,
                        color=colors['accent'],
                        value=0
                    ),
                ],
            ),
            # autoscale
            html.Div(
                className='status-box-title',
                children=[
                    "autoscale plot"
                ]
            ),
            html.Div(
                id='autoscale-switch-container',
                children=[
                    daq.BooleanSwitch(
                        id='autoscale-switch',
                        on=True,
                        color=colors['accent']
                    )
                ]
            ),

            # submit button

            html.Div(
                id='submit-button-container',
                children=[
                    html.Button(
                        'update',
                        id='submit-button',
                        n_clicks=0,
                        n_clicks_timestamp=0
                    )
                ]
            ),
            
            # displays whether the parameters were successfully changed
            html.Div(
                id='submit-status',
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
            ctrl.create_ctrl_div(True) for ctrl in controls
        ],
    ),

    # about the app
    html.Div(
        id='infobox',
        children=[
            html.Div(
                "about this app",
                id='infobox-title',
            ),
            dcc.Markdown(dedent('''
            This app was created to act as an interface for an Ocean Optics \
            spectrometer. The options above are used to control various \
            properties of the instrument; the integration time, the number of \
            scans to average over, the strobe and strobe period, and the \
            light source.

            Clicking \"Update\" after putting in the desired settings will \
            result in them being sent to the device. A status message \
            will appear below the button indicating which commands, if any, \
            were unsuccessful; below the unsuccessful commands, a list of \
            successful commands can be found.

            (Note that the box containing the status information is \
            scrollable.)


            The dial labelled \"light intensity\" will affect the current \
            selected light source, if any. The switch labelled \"autoscale \
            plot\" will change the axis limits of the plot to fit all of the \
            data. Please note that the animations and speed of the graph will \
            improve if this feature is turned off, and that it will not be \
            possible to zoom in on any portion of the plot if it is turned \
            on.
            '''))
        ]
    ),

])]

app.layout = html.Div(id='main', children=page_layout)


############################
# Callbacks
############################

# disable/enable the update button depending on whether options have changed
@app.callback(
    Output('submit-button', 'style'),
    [Input(ctrl.component_attr['id'], ctrl.val_string())
     for ctrl in controls] +
    [Input('submit-status', 'children')],
    state=[State('submit-button', 'n_clicks_timestamp')]
)
def update_button_disable_enable(*args):
    now = time.time() * 1000
    disabled = {
        'color': colors['accent'],
        'backgroundColor': colors['background'],
        'cursor': 'not-allowed'
    }
    enabled = {
        'color': colors['background'],
        'backgroundColor': colors['accent'],
        'cursor': 'pointer'
    }
    
    # if the button was recently clicked (less than a second ago), then
    # it's safe to say that the callback was triggered by the button; so
    # we have to "disable" it
    if(int(now) - int(args[-1]) >= 1000):
        return enabled
    else:
        return disabled
    
    
# spec model
@app.callback(
    Output('graph-title', 'children'),
    [Input('power-button', 'on')]
)
def update_spec_model(_):
    return "ocean optics %s" % spec.model()


# keep component values from resetting
@app.callback(
    Output('controls', 'children'),
    [Input(ctrl.component_attr['id'], ctrl.val_string())
     for ctrl in controls] +
    [Input('power-button', 'on')]
)
def preserve_controls_settings(*args):
    for i in range(len(controls)):
        controls[i].update_value(args[i])

    return [ctrl.create_ctrl_div(not args[-1]) for ctrl in controls]


# keep power button from resetting
@app.callback(
    Output('power-button-container', 'children'),
    [Input('power-button', 'on')]
)
def preserve_on(current):
    return [daq.PowerButton(
        id='power-button',
        size=50,
        color=colors['accent'],
        on=current
    )]


# keep light intensity from resetting, update the value,
# or disable in the event of no light sources
@app.callback(
    Output('light-intensity-knob-container', 'children'),
    [Input('light-intensity-knob', 'value'),
     Input('power-button', 'on')],
    state=[
        State('light-source-input', 'value')
    ]
)
def preserve_set_light_intensity(intensity, pwr, ls):
    if ls != "" and ls is not None:
        spec.send_light_intensity(ls, intensity)
    disable = not (pwr and ls != "" and ls is not None)
    return[daq.Knob(
        id='light-intensity-knob',
        size=110,
        color=colors['accent'],
        scale={
            'interval': '1',
            'labelInterval': '1'
        },
        disabled=disable,
        value=intensity
    )]


# send user-selected options to spectrometer
@app.callback(
    Output('submit-status', 'children'),
    [Input('submit-button', 'n_clicks')],
    state=[
        State(ctrl.component_attr['id'], ctrl.val_string())
        for ctrl in controls] + [
        State('power-button', 'on')
    ]
)
def update_spec_params(n_clicks, *args):

    # don't return anything if the device is off
    if(not args[-1]):
        return [
            "Press the power button to the top-right of the app, then \
            press the \"update\" button above to apply your options to \
            the spectrometer."
        ]

    # dictionary of commands; component id and associated value
    commands = {controls[i].component_attr['id']: args[i]
                for i in range(len(controls))}
            
    failed, succeeded = spec.send_control_values(commands)
    
    summary = []
    
    if len(failed) > 0:
        summary.append("The following parameters were not \
        successfully updated: ")
        summary.append(html.Br())
        summary.append(html.Br())

        for f in failed:
            # get the name as opposed to the id of each control
            # for readability
            [ctrlName] = [c.ctrl_name for c in controls
                          if c.component_attr['id'] == f]
            summary.append(ctrlName.upper() + ': ' + failed[f])
            summary.append(html.Br())

        summary.append(html.Br())
        summary.append(html.Hr())
        summary.append(html.Br())
        summary.append(html.Br())
        
    if len(succeeded) > 0:
        summary.append("The following parameters were successfully updated: ")
        summary.append(html.Br())
        summary.append(html.Br())

        for s in succeeded:
            [ctrlName] = [c.ctrl_name for c in controls
                          if c.component_attr['id'] == s]
            summary.append(ctrlName.upper() + ': ' + succeeded[s])
            summary.append(html.Br())

    return html.Div(summary)


# update the plot
@app.callback(
    Output('spec-readings', 'figure'),
    state=[
        State('power-button', 'on'),
        State('autoscale-switch', 'on')
    ],
    events=[
        Event('spec-reading-interval', 'interval')
    ]
)
def update_plot(on, auto_range):

    traces = []
    wavelengths = []
    intensities = []

    x_axis = {
            'title': 'Wavelength (nm)',
            'titlefont': {
                'family': 'Helvetica, sans-serif',
                'color': colors['secondary']
            },
            'tickfont': {
                'color': colors['tertiary']
            },
            'dtick': 100,
            'color': colors['secondary'],
            'gridcolor': colors['grid-colour']
    }
    y_axis = {
        'title': 'Intensity (AU)',
        'titlefont': {
            'family': 'Helvetica, sans-serif',
            'color': colors['secondary']
        },
        'tickfont': {
            'color': colors['tertiary']
        },
        'color': colors['secondary'],
        'gridcolor': colors['grid-colour'],
    }
    
    if(on):
        spectrum = spec.get_spectrum()
        wavelengths = spectrum[0]
        intensities = spectrum[1]
    else:
        wavelengths = numpy.linspace(400, 900, 5000)
        intensities = [0 for wl in wavelengths]

    if(on):
        if(auto_range):
            x_axis['range'] = [
                min(wavelengths),
                max(wavelengths)
            ]
            y_axis['range'] = [
                min(intensities),
                max(intensities)
            ]
    traces.append(go.Scatter(
        x=wavelengths,
        y=intensities,
        name='Spectrometer readings',
        mode='lines',
        line={
            'width': 1,
            'color': colors['accent']
        }
    ))

    layout = go.Layout(
        height=600,
        font={
            'family': 'Helvetica Neue, sans-serif',
            'size': 12
        },
        margin={
            't': 20
        },
        titlefont={
            'family': 'Helvetica, sans-serif',
            'color': colors['primary'],
            'size': 26
        },
        xaxis=x_axis,
        yaxis=y_axis,
        paper_bgcolor=colors['background'],
        plot_bgcolor=colors['background'],
    )

    return {'data': traces,
            'layout': layout}


############################
# Run app
############################

if __name__ == '__main__':
    app.run_server(debug=True)

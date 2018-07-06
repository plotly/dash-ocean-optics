#-*- coding: utf-8 -*-

import dash
import dash_daq as daq
import dash_html_components as html
import dash_core_components as dcc

import plotly.graph_objs as go

from dash.dependencies import Input, Output, Event, State
from threading import Lock

import numpy
import os

import DashOceanOpticsSpectrometer as doos
from DashOceanOpticsSpectrometer import Control

#############################
# Spectrometer properties
#############################

import sys

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
int_time = Control('integration-time', "int. time (us)",
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
strobe_period = Control('continuous-strobe-period', "strobe pd. (us)",
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
            # title
            html.Div(
                style={
                    'font-family': 'Helvetica, sans-serif',
                    'font-size': '14pt',
                    'font-variant': 'small-caps',
                    'text-align': 'center',
                    'color': colors['primary'],
                },
                children=[
                    "light intensity"
                ]
            ),
            # light intensity
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
            # submit button
            html.Div(
                id='submit-button-container',
                children=[
                    html.Button(
                        'update',
                        id='submit-button',
                        n_clicks=0,
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
                id='infobox-title',
                children=[
                    "about this app"
                ]
            ),
            "This app was created to act as an interface for an Ocean Optics \
            spectrometer. The options above are used to control various \
            properties of the instrument; the integration time, the number of \
            scans to average over, the strobe and strobe period, and the \
            light source.",
            html.Br(),
            html.Br(),
            "Clicking \"Update\" after putting in the desired settings will \
            result in them being sent to the device. A status message \
            will appear below the button indicating which commands, if any, \
            were unsuccessful; below the unsuccessful commands, a list of \
            successful commands can be found.",
            html.Br(),
            "(Note that the box containing the status information is \
            scrollable.)",
            html.Br(),
            html.Br(),
            "The intensity of the light source can be controlled by the dial \
            above the update button.",
            html.Br()
        ]
    ),

])]

app.layout = html.Div(id='main', children=page_layout)


############################
# Callbacks
############################

# spec model
@app.callback(Output('graph-title', 'children'), [
    Input('power-button', 'on')
])
def update_spec_model(_):
    return "ocean optics %s" % spec.model()


# keep component values from resetting
@app.callback(Output('controls', 'children'), [
    Input(ctrl.component_attr['id'], ctrl.val_string()) for ctrl in controls
] + [Input('power-button', 'on')])
def preserve_controls_settings(*args):
    for i in range(len(controls)):
        controls[i].update_value(args[i])

    return [ctrl.create_ctrl_div(not args[-1]) for ctrl in controls]


# keep power button from resetting
@app.callback(Output('power-button-container', 'children'), [
    Input('power-button', 'on')
])
def preserve_on(current):
    return [daq.PowerButton(
        id='power-button',
        size=50,
        color=colors['accent'],
        on=current
    )]


# keep light intensity from resetting, update the value,
# or disable in the event of no light sources
@app.callback(Output('light-intensity-knob-container', 'children'),
              [Input('light-intensity-knob', 'value'),
               Input('power-button', 'on')
               ],
              state=[
                  State('light-source-input', 'value')
              ])
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
@app.callback(Output('submit-status', 'children'),
              [Input('submit-button', 'n_clicks')],
              state=[
                  State(ctrl.component_attr['id'], ctrl.val_string())
                  for ctrl in controls
] + [State('power-button', 'on')])
def update_spec_params(n_clicks, *args):

    # don't return anything if the device is off
    if(not args[-1]):
        return ""

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
@app.callback(Output('spec-readings', 'figure'),
              state=[State('power-button', 'on')],
              events=[Event('spec-reading-interval', 'interval')]
)
def update_plot(on):

    traces = []
    wavelengths = []
    intensities = []

    if(on):
        spectrum = spec.get_spectrum()
        wavelengths = spectrum[0]
        intensities = spectrum[1]
    else:
        wavelengths = numpy.linspace(400, 900, 5000)
        intensities = [0 for wl in wavelengths]

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
        autosize=False,
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
        xaxis={
            'title': 'Wavelength (nm)',
            'titlefont': {
                'family': 'Helvetica, sans-serif',
                'color': colors['secondary']
            },
            'tickfont': {
                'color': colors['tertiary']
            },
            'color': colors['secondary'],
            'gridcolor': colors['grid-colour']
        },
        yaxis={
            'title': 'Intensity (AU)',
            'titlefont': {
                'family': 'Helvetica, sans-serif',
                'color': colors['secondary']
            },
            'tickfont': {
                'color': colors['tertiary']
            },
            'color': colors['secondary'],
            'gridcolor': colors['grid-colour']
        },
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

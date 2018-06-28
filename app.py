#-*- coding: utf-8 -*-

import dash
import dash_daq as daq
import dash_html_components as html
import dash_core_components as dcc

import plotly.graph_objs as go

from dash.dependencies import Input, Output, Event, State
from threading import Lock

import numpy

import DashOceanOpticsSpectrometer as doos
from seabreeze.spectrometers import SeaBreezeError

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
if(len(sys.argv) == 2 and sys.argv[1] == "demo"):
    spec = doos.DemoSpectrometer(spec_lock, comm_lock)
else:
    spec = doos.PhysicalSpectrometer(spec_lock, comm_lock)
    
spec.assign_spec()

############################
# Begin Dash app
############################

app = dash.Dash()
app.scripts.config.serve_locally = True


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
# Control object
############################

controls = []


class Control:
    def __init__(self, new_ctrl_id, new_ctrl_name,
                 new_component_type, new_component_attr, new_ctrl_func):
        self.ctrl_id = new_ctrl_id                # id for callbacks
        self.ctrl_name = new_ctrl_name            # name for label
        self.component_type = new_component_type  # dash-daq component type
        self.component_attr = new_component_attr  # component attributes
        self.ctrl_func = new_ctrl_func            # control function
        controls.append(self)

    # creates a new control box with defined component, id, and name
    def create_ctrl_div(self, pwrOff):
        # create dash-daq components
        if(self.component_type == "BooleanSwitch"):
            component = daq.BooleanSwitch(
                id=self.component_attr['id'],
                color=self.component_attr['color'],
                on=self.component_attr['on'],
                disabled=pwrOff
            )
        elif(self.component_type == "NumericInput"):
            component = daq.NumericInput(
                id=self.component_attr['id'],
                max=self.component_attr['max'],
                min=self.component_attr['min'],
                size=self.component_attr['size'],
                value=self.component_attr['value'],
                disabled=pwrOff
            )
        elif(self.component_type == "PowerButton"):
            component = daq.PowerButton(
                id=self.component_attr['id'],
                color=self.component_attr['color'],
                on=self.component_attr['on'],
                disabled=pwrOff
            )
        elif(self.component_type == "Dropdown"):
            component = dcc.Dropdown(
                id=self.component_attr['id'],
                options=self.component_attr['options'],
                placeholder=self.component_attr['placeholder'],
                value=self.component_attr['value'],
                disabled=pwrOff
            )
        elif(self.component_type == "Knob"):
            component = daq.Knob(
                id=self.component_attr['id'],
                size=self.component_attr['size'],
                max=self.component_attr['max'],
                color=self.component_attr['color'],
                value=self.component_attr['value'],
                disabled=pwrOff
            )

        # generate html code
        new_control = html.Div(
            id=self.ctrl_id,
            children=[
                html.Div(
                    className='option-name',
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
        elif('on' in self.component_attr):
            return 'on'

    # changes value ('on' or 'value', etc.)
    def update_value(self, new_value):
        self.component_attr[self.val_string()] = new_value

        
############################
# All controls
############################

# integration time, microseconds
int_time = Control('integration-time', "int. time (us)",
                   "NumericInput",
                   {'id': 'integration-time-input',
                    'max': spec.int_time_max,
                    'min': spec.int_time_min,
                    'size': 100,
                    'value': spec.int_time_min
                    },
                   spec.controlFunctions['int_time']
                   )

# scans to average over
nscans_avg = Control('nscans-to-average', "number of scans",
                     "NumericInput",
                     {'id': 'nscans-to-average-input',
                      'max': 100,
                      'min': 1,
                      'size': 100,
                      'value': 1
                      },
                     spec.controlFunctions['nscans_avg']
                     )

# strobe
strobe_enable = Control('continuous-strobe-toggle', "strobe",
                        "BooleanSwitch",
                        {'id': 'continuous-strobe-toggle-input',
                         'color': colors['accent'],
                         'on': False
                         },
                        spec.controlFunctions['strobe_enable']
                        )

# strobe period
strobe_period = Control('continuous-strobe-period', "strobe pd. (us)",
                        "NumericInput",
                        {'id': 'continuous-strobe-period-input',
                         'max': 100,
                         'min': 1,
                         'size': 100,
                         'value': 1
                         },
                        spec.controlFunctions['strobe_period']
                        )

# light sources
light_sources = Control('light-source', "light source",
                        "Dropdown",
                        {'id': 'light-source-input',
                         'options': spec.lightSources,
                         'placeholder': "select light source",
                         'value': ""
                         },
                        spec.controlFunctions['light_sources']
                        )


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
    try:
        spec_lock.acquire()
        spec.assign_spec()
    except SeaBreezeError:  # occurs only if spec is already assigned
        pass
    finally:
        spec_lock.release()
    return "ocean optics %s" % spec.specmodel


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
        try:
            comm_lock.acquire()
            ls.set_intensity(intensity)
        except Exception:
            pass
        finally:
            comm_lock.release()
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

    # list of commands to send; dictionary form so we can iterate
    # through them and determine which one(s) failed and succeeded
    # in a user-friendly way
    failed = {}
    succeeded = {}

    summary = []
    
    for i in range(len(controls)):
        try:
            comm_lock.acquire()
            eval(controls[i].ctrl_func)(args[i])
            succeeded[controls[i].ctrl_name] = str(args[i])
        except Exception as e:
            failed[controls[i].ctrl_name] = str(e).strip('b')
            # get rid of b indicating this is a byte literal
        finally:
            comm_lock.release()
            
    if len(failed) > 0:
        summary.append("The following parameters were not \
        successfully updated: ")
        summary.append(html.Br())
        summary.append(html.Br())
        for f in failed:
            summary.append(f.upper() + ': ' + failed[f])
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
            summary.append(s.upper() + ': ' + succeeded[s])
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
        global int_time_min
        global int_time_demo_val
        global int_time_demo_lock
        
        spectrum = [[], []]
        if spec is None:
            try:
                spec_lock.acquire()
                spec.assign_spec()
            except Exception:
                pass
            finally:
                spec_lock.release()
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

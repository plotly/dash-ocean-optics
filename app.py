# -*- coding: utf-8 -*-

import dash
import dash_daq as daq
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objs as go
import plotly
from dash.dependencies import Input, Output, Event, State

import numpy  # for demo purposes
import random

import seabreeze.spectrometers as sb  # actual data collection
specmodel = 'USB2000+'
spec = None

lightSources = []

############################
# Settings
############################

DEMO = False


def assign_spec():
    devices = sb.list_devices()
    global spec
    global specmodel
    global lightSources
    spec = sb.Spectrometer(devices[0])
    specmodel = spec.__repr__()[
        spec.__repr__().index("Spectrometer") +
        13:spec.__repr__().index(':')]
    # light sources
    lightSources = [{'label': ls.__repr__(), 'value': ls}
                    for ls in list(spec.light_sources)]

    
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
colors = {
    'background': '#bbbbbb',
    'primary': '#ffffff',
    'secondary': '#ffffff',
    'tertiary': '#dfdfdf',
    'grid-colour': '#eeeeee',
    'accent': '#2222ff'
}

styles = {
    'page': {
        'backgroundColor': colors['background'],
        'height': 'auto',
        'width': '90%',
        'position': 'absolute',
        'left': '0px',
        'top': '0px',
        'padding': '5%',
        'padding-bottom': '100px'
    },
    'graph-container': {
        'backgroundColor': colors['background'],
        'width': '70%',
        'min-width': '200px',
        'height': '500px',
        'margin-right': '50px',
        'layout': 'inline-block',
        'position': 'absolute',
    },
    'graph-title': {
        'color': colors['primary'],
        'margin-top': '30px',
        'margin-bottom': '30px',
        'margin-left': '50px',
        'font-size': 50,
        'font-weight': 100,
        'font-variant': 'small-caps',
        'font-family': 'Helvetica, sans-serif',
    },
    'power-button-container': {
        'position': 'absolute',
        'right': '50px',
        'top': '50px'
    },
    'light-intensity-knob-container': {
        'margin-left': '20px',
    },
    'controls': {
        'position': 'relative',
        'margin-top': '50px',
        'padding-bottom': '25px',
        'overflow': 'auto',
    },
    'option-box': {
        'width': '150px',
        'position': 'static',
        'float': 'left',
        'backgroundColor': colors['background'],
        'height': '125px',
        'margin': '10px',
        'margin-top': '0px',
        'padding': '10px',
        'padding-top': '0px',
        'padding-bottom': '0px',
        'font-family': 'Helvetica, sans-serif',
    },
    'option-name': {
        'padding': 'none',
        'padding-bottom': '10px',
        'text-align': 'center',
        'font-variant': 'small-caps',
        'font-family': 'Helvetica, sans-serif',
        'font-weight': 100,
        'font-size': '16pt',
        'color': colors['primary']
    },
    'numeric-input': {
        'width': '100%',
        'padding': '15%',
        'padding-top': '0px',
        'position': 'static',
        'font-size': '12pt',
        'border-style': 'none',
        'color': colors['primary']
    },
    'status-box': {
        'width': '225px',
        'margin-top': '100px',
        'height': '425px',
        'position': 'relative',
        'left': '80%',
        'padding': '0px',
        'padding-top': '10px',
        'border-color': colors['secondary'],
        'border-style': 'solid',
        'border-width': '1px',
        'border-radius': '5px',
        'font-family': 'Helvetica, sans-serif',
    },
    'submit-button': {
        'font-family': 'Helvetica, sans-serif',
        'font-size': '20px',
        'font-variant': 'small-caps',
        'color': colors['background'],
        'text-align': 'center',
        'height': '50px',
        'width': '120px',
        'margin-left': '50px',
        'margin-bottom': '25px',
        'background-color': colors['accent'],
        'position': 'static',
        'border-width': '1px',
        'border-color': colors['accent'],
        'border-radius': '5px',
    },
    'submit-status': {
        'width': '175px',
        'border-style': 'solid',
        'border-color': colors['tertiary'],
        'border-width': '1px',
        'height': '100px',
        'padding': '10px',
        'overflow': 'scroll',
        'position': 'static',
        'margin-left': '10px',
        'font-family': 'Courier, monospace',
        'font-size': '9pt',
        'color': colors['secondary']
    },
    'boolean-switch': {
        'margin-top': '5px'
    },
    'infobox': {
        'position': 'static',
        'width': '700px',
        'padding': '20px',
        'margin': '50px',
        'margin-top': '0px',
        'border-style': 'solid',
        'border-width': '1px',
        'border-radius': '5px',
        'border-color': colors['primary'],
        'color': colors['primary'],
        'font-family': 'Helvetica, sans-serif',
    },
    'infobox-title': {
        'position': 'static',
        'width': '100%',
        'text-align': 'center',
        'font-size': '30pt',
        'padding-top': '0px',
        'font-variant': 'small-caps'
    }
}


############################
# Controls
############################

# a sample function attached to a control
# to test exceptions, this throws one whenever
# light source 1 is selected in the demo
def sample_func(x):
    if(x == 'l1'):
        raise Exception("Lamp not found.")
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
        self.component_attr = new_component_attr  # component attributes
        if DEMO:                                  # control function
            self.ctrl_func = sample_func
        else:
            self.ctrl_func = new_ctrl_func
        controls.append(self)

    # creates a new control box with defined component, id, and name
    def create_ctrl_div(self, pwrOff):
        # create dash-daq components
        if(self.component_type == "BooleanSwitch"):
            component = daq.BooleanSwitch(
                id=self.component_attr['id'],
                style=self.component_attr['style'],
                color=self.component_attr['color'],
                on=self.component_attr['on'],
                disabled=pwrOff
            )
        elif(self.component_type == "NumericInput"):
            component = daq.NumericInput(
                id=self.component_attr['id'],
                style=self.component_attr['style'],
                max=self.component_attr['max'],
                min=self.component_attr['min'],
                size=self.component_attr['size'],
                value=self.component_attr['value'],
                disabled=pwrOff
            )
        elif(self.component_type == "PowerButton"):
            component = daq.PowerButton(
                id=self.component_attr['id'],
                style=self.component_attr['style'],
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
        elif('on' in self.component_attr):
            return 'on'

    # changes value ('on' or 'value', etc.)
    def update_value(self, new_value):
        self.component_attr[self.val_string()] = new_value

    # changes other attributes
    def update_attribute(self, attr_name, new_attr_value):
        self.component_attr[attr_name] = new_attr_value
        
############################
# All controls
############################


int_time = Control('integration-time', "int. time (us)",
                   "NumericInput",
                   {'id': 'integration-time-input',
                    'style': styles['numeric-input'],
                    'max': int_time_max,
                    'min': int_time_min,
                    'size': 100,
                    'value': int_time_min
                    },
                   lambda _: "int_time" if (DEMO)
                   else spec.integration_time_micros
                   )
nscans_avg = Control('nscans-to-average', "number of scans",
                     "NumericInput",
                     {'id': 'nscans-to-average-input',
                      'style': styles['numeric-input'],
                      'max': 100,
                      'min': 1,
                      'size': 100,
                      'value': 1
                      },
                     lambda _: "nscans_avg" if (DEMO)
                     else spec.scans_to_average
                     )
strobe_enable = Control('continuous-strobe-toggle', "strobe",
                        "BooleanSwitch",
                        {'id': 'continuous-strobe-toggle-input',
                         'style': styles['boolean-switch'],
                         'color': colors['accent'],
                         'on': False
                         },
                        lambda _: "strobe_enable" if (DEMO)
                        else spec.continuous_strobe_set_enable
                        )
strobe_period = Control('continuous-strobe-period', "strobe pd. (us)",
                        "NumericInput",
                        {'id': 'continuous-strobe-period-input',
                         'style': styles['numeric-input'],
                         'max': 100,
                         'min': 1,
                         'size': 100,
                         'value': 1
                         },
                        lambda _: "strobe_period" if (DEMO)
                        else spec.continuous_strobe_set_period_micros
                        )


if (DEMO):
    lightSources = [{'label': 'Lamp 1 at 127.0.0.1:1020', 'value': 'l1'},
                    {'label': 'Lamp 2 at 127.0.0.1:2030', 'value': 'l2'}]
elif spec is not None:
    lightSources = [{'label': ls.__repr__(), 'value': ls}
                    for ls in list(spec.light_sources)]

# selection of light sources
light_sources = Control('light-source', "light source",
                        "Dropdown",
                        {'id': 'light-source-input',
                         'options': lightSources,
                         'placeholder': "select light source",
                         'value': ""
                         },
                        lambda _: "light_source" if (DEMO)
                        else lambda _: ""
                        )


############################
# Layout
############################

# begin html
app.layout = html.Div(id='page', style=styles['page'], children=[

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
                            "ocean optics %s" % specmodel
                        ]
                    ),
                    dcc.Graph(id='spec-readings', animate=True),
                    dcc.Interval(
                        id='spec-reading-interval',
                        interval=0.1 * 1000,
                        n_intervals=0
                    )
                ]
            )
        ]
    ),

    html.Div(
        id='power-button-container', children=[
            daq.PowerButton(
                id='power-button',
                size=50,
                color=colors['accent'],
                on=False
            )
        ],
        style=styles['power-button-container']
    ),
    # status box
    html.Div(
        id='status-box',
        style=styles['status-box'],
        children=[
            html.Div(
                style={
                    'font-family': 'Helvetica, sans-serif',
                    'font-size': '12pt',
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
                        size=100,
                        color=colors['accent'],
                        value=0
                    ),
                ],
                style=styles['light-intensity-knob-container']
            ),

            # submit button
            html.Div(
                id='submit-button-container',
                children=[
                    html.Button(
                        'update',
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
            ctrl.create_ctrl_div(True) for ctrl in controls
        ],
        style=styles['controls']
    ),

    html.Div(
        id='infobox',
        style=styles['infobox'],
        children=[
            html.Div(
                id='infobox-title',
                style=styles['infobox-title'],
                children=[
                    "about this app"
                ]
            ),
            "This app was created to act as an interface for an Ocean Optics \
            spectrometer. The options above are used to control various \
            properties of the instrument; the integration time, the number of \
            scans to average over, the strobe and strobe period, and the \
            light source. \
            Clicking \"Update\" after putting in the desired settings will \
            result in them being sent to the device, and a status message \
            will appear below the button indicating which commands, if any, \
            were unsuccessful. The intensity of the light source can be \
            controlled by the dial that appears above the update button."
        ]
    )
]
)

############################
# Callbacks
############################


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


# keep light intensity from resetting
@app.callback(Output('light-intensity-knob-container', 'children'), [
    Input('light-intensity-knob', 'value'),
    Input('power-button', 'on')
])
def preserve_light_intensity(current, pwr):
    # TODO: fill this in
    lambda: "light_intensity"
    disable = not pwr
    return[daq.Knob(
        id='light-intensity-knob',
        size=100,
        color=colors['accent'],
        scale={
            'interval': '1',
            'labelInterval': '1'
        },
        disabled=disable,
        value=current
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
    # through them and determine which one(s) failed in a user-friendly
    # way
    failed = {}
    # TODO: scrollable errors
    for i in range(len(controls)):
        try:
            controls[i].ctrl_func(args[i])
        except Exception as e:
            # TODO: include exception text as optional for
            # user to read
            failed[controls[i].ctrl_name] = str(e)
            pass

    if (len(failed) == 0):
        return "Success!"
    else:
        fails = [
            "Failure - the following parameters \
            were not successfully updated: ",
            html.Br(),
            html.Br()]
        for f in failed:
            fails.append(f.upper() + ': ' + failed[f])
            fails.append(html.Br())
        return html.Div(fails)

    
# update the plot
@app.callback(Output('spec-readings', 'figure'),
              state=[State('power-button', 'on')],
              events=[Event('spec-reading-interval', 'interval')
                      ])
def update_spec_readings(on):

    traces = []
    wavelengths = []
    intensities = []

    if(on):
        if DEMO:
            wavelengths = numpy.linspace(0, 700, 7000)
            intensities = [sample_spectrum(wl) for wl in wavelengths]
        else:
            if spec is None:
                assign_spec()
            spectrum = spec.spectrum(correct_dark_counts=True,
                                     correct_nonlinearity=True)
            wavelengths = spectrum[0]
            intensities = spectrum[1]
    else:
        wavelengths = numpy.linspace(0, 700, 7000)
        intensities = [0 for wl in wavelengths]

    traces.append(plotly.graph_objs.Scatter(
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
            'gridcolor': colors['grid-colour']
        },
        paper_bgcolor=colors['background'],
        plot_bgcolor=colors['background'],
    )

    return {'data': traces,
            'layout': layout}


# generated randomly, just for demonstration purposes
def sample_spectrum(x):
    return (50 * numpy.e**(-1 * ((x - 200))**2) +
            60 * numpy.e**(-1 * ((x - 500) / 5)**2) +
            random.random())


if __name__ == '__main__':
    app.run_server(debug=True)

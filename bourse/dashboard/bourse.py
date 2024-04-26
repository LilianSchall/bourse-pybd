import base64
import os
import time
from datetime import date
from difflib import get_close_matches

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import sqlalchemy
from dash import ClientsideFunction, Patch, clientside_callback, dcc, html
from dash.dependencies import MATCH, Input, Output, State

external_stylesheets = [dbc.themes.BOOTSTRAP]

DATABASE_URI = "timescaledb://ricou:monmdp@db:5432/bourse"  # inside docker
# DATABASE_URI = 'timescaledb://ricou:monmdp@localhost:5432/bourse'  # outisde docker
engine = sqlalchemy.create_engine(DATABASE_URI)

# CUSTOM FOR INFRASTRUCTURE
## START DO NOT REMOVE
PREFIX_PATH = os.getenv("PREFIX_PATH")

if PREFIX_PATH is not None:
    app = dash.Dash(
        __name__,
        title="Bourse",
        suppress_callback_exceptions=True,
        url_base_pathname=PREFIX_PATH,
        external_stylesheets=external_stylesheets,
    )
else:
    app = dash.Dash(
        __name__,
        title="Bourse",
        suppress_callback_exceptions=True,
        external_stylesheets=external_stylesheets,
    )
server = app.server
## END DO NOT REMOVE

# -- Constants
# MIN_DATE = date(2019, 1, 1)
# MAX_DATE = date(2023, 12, 29)
# INIT_DATE = date(2021, 1, 1)
MIN_DATE = date(2015, 2, 17)
MAX_DATE = date(2017, 2, 17)
INIT_DATE = date(2016, 1, 1)
BASIC_FIG_LAYOUT = dict(
    margin=dict(l=0, r=0, t=0, b=30),
    xaxis=dict(
        type="date",
        range=[MIN_DATE.strftime("%Y-%m-%d"), MAX_DATE.strftime("%Y-%m-%d")],
    ),
    yaxis=dict(type="linear"),
)

# -- Mock data
df = pd.read_csv(
    "https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv"
)

table_df = pd.DataFrame(
    {
        "Date (in days)": pd.date_range(start="2021-01-01", periods=8).strftime(
            "%Y-%m-%d"
        ),
        "Min": [300, 400, 500, 600, 700, 800, 900, 1000],
        "Max": [400, 500, 600, 700, 800, 900, 1000, 1100],
        "Start": [350, 450, 550, 650, 750, 850, 950, 1050],
        "End": [380, 480, 580, 680, 780, 880, 980, 1080],
        "Mean": [350, 450, 550, 650, 750, 850, 950, 1050],
        "Std deviation": [20, 30, 40, 50, 60, 70, 80, 90],
    }
)

mock_companies = {
    "Company A": ["SYM1", "SYM2", "SYM3"],
    "Company B": ["SYM4", "SYM5"],
    "Company C": ["SYM6", "SYM7", "SYM8"],
    "Company D": ["SYM9", "SYM10"],
    "Company E": ["SYM11", "SYM12", "SYM13"],
    "Company F": ["SYM14", "SYM15", "SYM16"],
    "Company G": ["SYM17", "SYM18", "SYM19"],
    "Company H": ["SYM20", "SYM21", "SYM22"],
}

fixed_dates = ["1D", "5D", "1M", "3M", "6M", "YTD", "1Y", "5Y", "ALL"]

navbar_options_svg = ["night-mode", "full-screen"]

graph_options_svg = [
    "bx-cross",
    "candles",
    "polyline",
    "text",
    "ruler",
    "zoom",
    "trash-can",
]


# -- App layout
app.layout = html.Div(
    [
        # -- Nav bar
        html.Nav(
            [
                html.Div(
                    [
                        html.Span("📈", style={"font-size": "1.4em"}),
                        html.H5("Stock Market Viewer", className="m-0"),
                    ],
                    className="navbar-left",
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Button(
                                    [
                                        html.Img(
                                            src="assets/header/night-mode.svg",
                                            className="svg-size-24 m-auto",
                                        ),
                                    ],
                                    id="navbar-option-night-mode",
                                    className="navbar-btn hoverable-btn",
                                ),
                                html.Button(
                                    [
                                        html.Img(
                                            src="assets/header/full-screen.svg",
                                            className="svg-size-24 m-auto",
                                        ),
                                    ],
                                    id="navbar-option-full-screen",
                                    className="navbar-btn hoverable-btn",
                                ),
                            ],
                        ),
                        html.Button("Save", id="save-btn"),
                        dcc.Download(id="download-figure"),
                    ],
                    className="navbar-right",
                ),
            ]
        ),
        html.Main(
            [
                # -- Graph options sidebar
                html.Div(
                    [
                        html.Button(
                            [
                                html.Img(
                                    src=f"assets/graph_options/{svg}.svg",
                                    className="m-auto",
                                ),
                            ],
                            id=f"graph-option-{svg}",
                            className="graph-option-btn hoverable-btn",
                        )
                        for svg in graph_options_svg
                    ],
                    className="graph-options-sidebar",
                ),
                # -- Graph
                html.Div(
                    [
                        dcc.Graph(
                            id="stock-graph",
                            figure=go.Figure(layout=BASIC_FIG_LAYOUT),
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Button(
                                                    [date],
                                                    id=f"fixed-date-{date}",
                                                    className="fixed-date-btn hoverable-btn",
                                                )
                                                for date in fixed_dates
                                            ],
                                            className="graph-fixed-dates-container",
                                        ),
                                        html.Div(className="vertical-divider"),
                                        dcc.DatePickerRange(
                                            id="date-picker-range",
                                            min_date_allowed=MIN_DATE,
                                            max_date_allowed=MAX_DATE,
                                            initial_visible_month=INIT_DATE,
                                            start_date_placeholder_text="Start Period",
                                            end_date_placeholder_text="End Period",
                                            with_portal=True,
                                        ),
                                    ],
                                    className="graph-date-container",
                                ),
                                html.Div(
                                    [
                                        html.Button(
                                            ["lin"],
                                            id="lin-btn",
                                            className="lin-log-btn hoverable-btn",
                                        ),
                                        html.Button(
                                            ["log"],
                                            id="log-btn",
                                            className="lin-log-btn hoverable-btn",
                                        ),
                                    ],
                                    className="graph-lin-log-container",
                                ),
                            ],
                            className="date-lin-log-container",
                        ),
                    ],
                    id="graph-container",
                ),
                # -- Table data
                html.Div(
                    [
                        html.Div(
                            [
                                html.Button(
                                    [
                                        html.Img(src="assets/table/chevron-up.svg"),
                                    ],
                                    id="table-chevron-up",
                                    className="float-end",
                                ),
                            ],
                            className="table-header",
                        ),
                        html.Div(
                            [
                                dbc.Table.from_dataframe(
                                    table_df,
                                    striped=True,
                                    hover=True,
                                    responsive=True,
                                    size="md",
                                    class_name="table",
                                )
                            ],
                            id="table-content",
                        ),
                    ],
                    id="table-container",
                ),
                # -- Graph company selection sidebar
                html.Div(
                    [
                        html.H4("Company Selection"),
                        html.Div(
                            [
                                html.Img(
                                    src="assets/company_selection/search-line.svg",
                                    className="svg-size-20",
                                ),
                                dcc.Input(
                                    id="input-company",
                                    type="text",
                                    placeholder="Search company",
                                    debounce=True,
                                ),
                            ],
                            className="company-search-bar",
                        ),
                        html.Div(
                            children=[],
                            id="company-selection",
                            className="ms-3",
                            style={"overflow-y": "auto", "height": "480px"},
                        ),
                    ],
                    className="company-selection-container",
                ),
            ],
            id="main-container",
        ),
    ],
    className="app-container",
)


# -- Functions
def add_or_update_trace(fig, trace_name):
    # Check if the trace type already exists
    for trace in fig["data"]:
        if trace["name"] == trace_name:
            # Toggle visibility
            trace["visible"] = not trace["visible"]
            return fig

    # Add a new trace if it doesn't exist
    if trace_name == "polyline":
        new_trace = go.Scatter(
            x=df["Date"],
            y=df["AAPL.High"],
            mode="lines",
            line=dict(color="royalblue"),
            name=trace_name,
            visible=True,
        )
        fig["data"].append(new_trace)
    elif trace_name == "candles":
        new_trace = go.Candlestick(
            x=df["Date"],
            open=df["AAPL.Open"],
            high=df["AAPL.High"],
            low=df["AAPL.Low"],
            close=df["AAPL.Close"],
            name=trace_name,
            visible=True,
        )
        fig["data"].append(new_trace)

    return fig


def create_company_details(company, symbols):
    html_details = html.Details(
        [
            html.Summary(
                children=[
                    dcc.Checklist(
                        [
                            {
                                "label": html.Span(
                                    company,
                                    className="ms-2 lead fw-normal",
                                ),
                                "value": company,
                            }
                        ],
                        id={
                            "type": "company-checkbox",
                            "index": company,
                        },
                        inputStyle={
                            "width": "15px",
                            "height": "15px",
                        },
                        className="d-inline-block",
                    )
                ],
            ),
            dcc.Checklist(
                [
                    {
                        "label": html.Span(symbol, className="ms-2"),
                        "value": symbol,
                    }
                    for symbol in symbols
                ],
                id={
                    "type": "symbol-checkbox",
                    "index": company,
                },
                style={"margin-left": "30px"},
            ),
        ],
        className="my-2",
    )

    return html_details


# -- Callbacks
@app.callback(
    Output("main-container", "className"),
    Output("table-container", "className"),
    Output("table-chevron-up", "className"),
    Input("table-chevron-up", "n_clicks"),
    State("main-container", "className"),
    State("table-container", "className"),
    Input("table-chevron-up", "className"),
    prevent_initial_call=True,
)
def expand_table(
    n_clicks, main_container_class, table_container_class, table_chevron_up_class
):
    new_mc_class = "" if not main_container_class else main_container_class
    new_tc_class = "" if not table_container_class else table_container_class
    new_cu_class = "" if not table_chevron_up_class else table_chevron_up_class
    if n_clicks % 2 == 1:
        time.sleep(0.001)  # Hide the graph before expanding the table
        return (
            new_mc_class + " expand-table",
            new_tc_class + " fix-table-gap",
            new_cu_class + " chevron-active",
        )
    return (
        new_mc_class.replace(" expand-table", ""),
        new_tc_class.replace(" fix-table-gap", ""),
        new_cu_class.replace(" chevron-active", ""),
    )


@app.callback(
    Output("graph-container", "className"),
    Input("table-chevron-up", "n_clicks"),
    State("graph-container", "className"),
    prevent_initial_call=True,
)
def hide_graph(n_clicks, graph_container_class):
    new_gc_class = "" if not graph_container_class else graph_container_class
    if n_clicks % 2 == 1:
        return new_gc_class + " hide"
    time.sleep(0.5001)  # Wait for the table collapse animation to finish
    return new_gc_class.replace(" hide", "")


@app.callback(
    Output({"type": "symbol-checkbox", "index": MATCH}, "value"),
    Input({"type": "company-checkbox", "index": MATCH}, "value"),
    State({"type": "symbol-checkbox", "index": MATCH}, "options"),
    prevent_initial_call=True,
)
def update_children_checkbox(checkbox_value, options):
    if not checkbox_value:
        return checkbox_value
    return [option["value"] for option in options]


@app.callback(
    Output("lin-btn", "className"),
    Output("log-btn", "className"),
    Input("lin-btn", "n_clicks"),
    Input("log-btn", "n_clicks"),
    prevent_initial_call=True,
)
def toggle_lin_log_btn(*args):
    lin_class = "lin-log-btn hoverable-btn"
    log_class = "lin-log-btn hoverable-btn"
    if dash.ctx.triggered_id == "lin-btn":
        lin_class += " active"
    else:
        log_class += " active"
    return lin_class, log_class


@app.callback(
    Output("stock-graph", "figure"),
    State("stock-graph", "figure"),
    Input("date-picker-range", "start_date"),
    Input("date-picker-range", "end_date"),
    Input("lin-btn", "n_clicks"),
    Input("log-btn", "n_clicks"),
    Input("graph-option-polyline", "n_clicks"),
    Input("graph-option-candles", "n_clicks"),
    Input("graph-option-trash-can", "n_clicks"),
    prevent_initial_call=True,
)
def update_graph_polyline(
    current_fig, start_date, end_date, lin_clicks, log_clicks, *args
):
    selected_fig = current_fig

    if dash.ctx.triggered_id == "lin-btn":
        selected_fig["layout"]["yaxis"]["type"] = "linear"
    elif dash.ctx.triggered_id == "log-btn":
        selected_fig["layout"]["yaxis"]["type"] = "log"

    id_prefix = "graph-option-"
    if dash.ctx.triggered_id == id_prefix + "polyline":
        selected_fig = add_or_update_trace(selected_fig, "polyline")
    elif dash.ctx.triggered_id == id_prefix + "candles":
        selected_fig = add_or_update_trace(selected_fig, "candles")
    elif dash.ctx.triggered_id == id_prefix + "trash-can":
        selected_fig = go.Figure(layout=BASIC_FIG_LAYOUT)  # Reset graph
        selected_fig = selected_fig.to_dict()
    elif "date-picker-range" not in dash.ctx.triggered_id:
        print("Warning: No graph option selected")

    # Update time range
    if start_date and end_date:
        if "date-picker-range" in dash.ctx.triggered_id:
            selected_fig = Patch()
        selected_fig["layout"]["xaxis"]["type"] = "date"
        selected_fig["layout"]["xaxis"]["range"][0] = start_date
        selected_fig["layout"]["xaxis"]["range"][1] = end_date

    return selected_fig


@app.callback(
    Output("company-selection", "children"),
    Input("input-company", "value"),
    prevent_initial_call=True,
)
def update_company_selection(company):
    matches = get_close_matches(
        company, mock_companies.keys(), n=len(mock_companies), cutoff=0.5
    )
    children = []
    if not matches:
        return children

    for company in matches:
        symbols = mock_companies[company]
        html_details = create_company_details(company, symbols)
        children.append(html_details)

    return children


@app.callback(
    Output("download-figure", "data"),
    State("stock-graph", "figure"),
    Input("save-btn", "n_clicks"),
    prevent_initial_call=True,
)
def func(fig, n_clicks):
    # Due to a bug in plotly, rangeslider on yaxis must be removed to convert fig to go.Figure
    if "rangeslider" in fig["layout"]["xaxis"]:
        del fig["layout"]["xaxis"]["rangeslider"]["yaxis"]
    fig = go.Figure(fig)
    img_bytes = fig.to_image(format="png")
    encoded_image = base64.b64encode(img_bytes).decode()
    return dict(base64=True, content=encoded_image, filename="plot.png")


clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="toggle_full_screen"),
    Output("navbar-option-night-mode", "n_clicks"),
    Input("navbar-option-full-screen", "n_clicks"),
    prevent_initial_call=True,
)


if __name__ == "__main__":
    app.run(debug=True)

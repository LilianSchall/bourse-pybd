import base64
import os
import time
from datetime import date
from difflib import get_close_matches

import dash
import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import sqlalchemy
from dash import ClientsideFunction, Patch, clientside_callback, ctx, dcc, html
from dash.dependencies import ALL, MATCH, Input, Output, State
from dateutil.relativedelta import relativedelta

external_stylesheets = [dbc.themes.BOOTSTRAP]

# DATABASE_URI = "timescaledb://ricou:monmdp@db:5432/bourse"  # inside docker
DATABASE_URI = "timescaledb://ricou:monmdp@localhost:5432/bourse"  # outisde docker
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
MIN_DATE = date(2019, 1, 1)
MAX_DATE = date(2023, 12, 29)
INIT_DATE = date(2021, 1, 1)
BASIC_FIG_LAYOUT = dict(
    margin=dict(l=0, r=0, t=0, b=30),
    xaxis=dict(
        type="date",
        range=[MIN_DATE.strftime("%Y-%m-%d"), MAX_DATE.strftime("%Y-%m-%d")],
    ),
    yaxis=dict(type="linear"),
)

GRAPH_CONFIG = dict(
    displaylogo=False,
    modeBarButtonsToRemove=[
        "sendDataToCloud",
        "zoom2d",
        "zoomIn2d",
        "zoomOut2d",
        "resetScale2d",
        "autoScale2d",
        "lasso2d",
        "select2d",
        "toImage",
    ],
    scrollZoom=True,
    # editable=True,
)

ALIAS_TO_COUNTRY = {
    "euronx": "europe",
    "lse": "united-kingdom",
    "milano": "italy",
    "dbx": "germany",
    "mercados": "spain",
    "amsterdam": "netherlands",
    "compA": "france",
    "compB": "france",
    "xetra": "germany",
    "bruxelle": "belgium",
    "peapme": "france",
}


# -- Data
df = pd.read_csv(
    "https://raw.githubusercontent.com/plotly/datasets/master/finance-charts-apple.csv"
)

table_df = pd.DataFrame(
    {
        "date": pd.date_range(start="2021-01-01", periods=8).strftime("%Y-%m-%d"),
        "symbol": ["1rAAF", "SYM2", "SYM2", "SYM2", "SYM3", "SYM3", "SYM4", "SYM5"],
        "change": [-0.1, 0.2, 0.3, -0.4, 0.5, 0.6, 0.7, 0.8],
        "open": [350, 450, 550, 650, 750, 850, 950, 1050],
        "close": [380, 480, 580, 680, 780, 880, 980, 1080],
        "high": [400, 500, 600, 700, 800, 900, 1000, 1100],
        "low": [300, 400, 500, 600, 700, 800, 900, 1000],
        "mean": [350, 450, 550, 650, 750, 850, 950, 1050],
        "std_dev": [20, 30, 40, 50, 60, 70, 80, 90],
    }
)
columnDefs = [
    dict(
        headerName="Date (in days)",
        field="date",
        cellDataType="dateString",
        pinned="left",
        cellStyle=dict(fontWeight="500", backgroundColor="rgb(250, 250, 250)"),
    ),
    dict(
        headerName="Symbol",
        field="symbol",
        pinned="left",
        filter="agTextColumnFilter",
        filterParams=dict(filterOptions=["contains"]),
        cellStyle=dict(fontWeight="500", backgroundColor="rgb(250, 250, 250)"),
        cellRenderer="stockLink",
    ),
    dict(headerName="Change %", field="change", cellRenderer="colorRenderer"),
    dict(
        headerName="Open",
        field="open",
        valueFormatter=dict(function="d3.format('(.2f')(params.value)"),
    ),
    dict(
        headerName="Close",
        field="close",
        valueFormatter=dict(function="d3.format('(.2f')(params.value)"),
    ),
    dict(
        headerName="High",
        field="high",
        valueFormatter=dict(function="d3.format('(.2f')(params.value)"),
    ),
    dict(
        headerName="Low",
        field="low",
        valueFormatter=dict(function="d3.format('(.2f')(params.value)"),
    ),
    dict(
        headerName="Mean",
        field="mean",
        valueFormatter=dict(function="d3.format('(.2f')(params.value)"),
    ),
    dict(
        headerName="Std deviation",
        field="std_dev",
        valueFormatter=dict(function="d3.format('(.2f')(params.value)"),
    ),
]

# Fetch all markets from the database
query = "SELECT id, alias FROM markets"
MARKETS = pd.read_sql_query(query, engine)

# Empty dataframe to store the companies and their symbols
COMPANIES = pd.DataFrame(columns=["id", "name", "symbol"])
SELECTED_COMPANIES, SELECTED_SYMBOLS = set(), set()

DAYSTOCKS, STOCKS = pd.DataFrame(), pd.DataFrame()

fixed_dates = ["1D", "5D", "1M", "3M", "6M", "YTD", "1Y", "5Y", "ALL"]

navbar_options_svg = ["night-mode", "full-screen"]

graph_options_svg = [
    "bx-cross",
    "candles",
    "polyline",
    "area-chart",
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
                            config=GRAPH_CONFIG,
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Button(
                                                    [date.upper()],
                                                    id={
                                                        "type": "fixed-date-btn",
                                                        "index": date,
                                                    },
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
                                            clearable=True,
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
                                dag.AgGrid(
                                    id="aggrid-table",
                                    columnDefs=columnDefs,
                                    rowData=[],
                                    columnSize="sizeToFit",
                                    dashGridOptions={
                                        "pagination": True,
                                        "paginationPageSize": 20,
                                    },
                                    style={"height": "100%", "width": "100%"},
                                )
                            ],
                            id="table-content",
                        ),
                    ],
                    id="table-container",
                ),
                # -- Graph market and company selection sidebar
                html.Div(
                    [
                        html.Div(
                            [
                                html.H4("Market Selection"),
                                dcc.Dropdown(
                                    [
                                        {
                                            "label": html.Span(
                                                [
                                                    html.Img(
                                                        src=f"assets/graph_selection/markets/{ALIAS_TO_COUNTRY[markets['alias']]}.svg",
                                                        height=30,
                                                        style={
                                                            "display": "inline-block",
                                                        },
                                                    ),
                                                    html.Span(
                                                        markets["alias"],
                                                        style={
                                                            "font-size": 15,
                                                            "padding-left": 10,
                                                        },
                                                    ),
                                                ],
                                                style={
                                                    "align-items": "center",
                                                    "justify-content": "center",
                                                },
                                            ),
                                            "value": markets["id"],
                                        }
                                        for _, markets in MARKETS.iterrows()
                                    ],
                                    id="market-selection",
                                ),
                            ],
                            id="market-selection-container",
                        ),
                        html.Div(
                            [
                                html.H4("Company Selection"),
                                html.Div(
                                    [
                                        html.Img(
                                            src="assets/graph_selection/search-line.svg",
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
                                    style={"overflow-y": "auto"},
                                ),
                            ],
                            id="company-selection-container",
                        ),
                    ],
                    id="graph-selection-container",
                ),
            ],
            id="main-container",
        ),
        # -- Dummy hidden div
        html.Div(id="dummy-div", style={"display": "none"}),
    ],
    className="app-container",
)


# -- Functions
def get_aggrid_data():
    global DAYSTOCKS

    if DAYSTOCKS.empty:
        return []

    aggrid_df = DAYSTOCKS.copy()
    aggrid_df.reset_index(inplace=True)

    # Add change column
    aggrid_df["change"] = (aggrid_df["close"] - aggrid_df["open"]) / aggrid_df["open"]

    # Add mean column
    aggrid_df["mean"] = aggrid_df["close"].rolling(3).mean()

    # Add std_dev column
    aggrid_df["std_dev"] = aggrid_df["close"].rolling(3).std()

    return aggrid_df.to_dict("records")


def fig_contains_symbol_trace(fig, symbol):
    for trace in fig["data"]:
        if symbol in trace["name"]:
            return True
    return False


def add_all_traces(fig, symbol):
    # - Add the symbol polyline trace to the figure
    fig.add_trace(
        go.Scatter(
            x=STOCKS.index,
            y=STOCKS[symbol],
            mode="lines",
            name=symbol,
            visible=False,
        )
    )

    # - Add the symbol candlestick trace to the figure
    fig.add_trace(
        go.Candlestick(
            x=DAYSTOCKS.index,
            open=DAYSTOCKS[DAYSTOCKS["symbol"] == symbol]["open"],
            close=DAYSTOCKS[DAYSTOCKS["symbol"] == symbol]["close"],
            high=DAYSTOCKS[DAYSTOCKS["symbol"] == symbol]["high"],
            low=DAYSTOCKS[DAYSTOCKS["symbol"] == symbol]["low"],
            name=symbol,
            visible=False,
        )
    )

    # - Add the symbol bollinger trace to the figure
    WINDOW = 30
    sma_df = DAYSTOCKS[DAYSTOCKS["symbol"] == symbol]["close"].rolling(WINDOW).mean()
    std_df = (
        DAYSTOCKS[DAYSTOCKS["symbol"] == symbol]["close"].rolling(WINDOW).std(ddof=0)
    )

    # Moving Average
    fig.add_trace(
        go.Scatter(
            x=DAYSTOCKS.index,
            y=sma_df,
            line_color="black",
            name=f"bollinger-{symbol}",
            visible=False,
        ),
    )

    # Upper Bound
    fig.add_trace(
        go.Scatter(
            x=DAYSTOCKS.index,
            y=sma_df + (std_df * 2),
            line_color="gray",
            line={"dash": "dash"},
            name=f"bollinger-{symbol}",
            opacity=0.5,
            visible=False,
        ),
    )

    # Lower Bound fill in between with parameter 'fill': 'tonexty'
    fig.add_trace(
        go.Scatter(
            x=DAYSTOCKS.index,
            y=sma_df - (std_df * 2),
            line_color="gray",
            line={"dash": "dash"},
            fill="tonexty",
            name=f"bollinger-{symbol}",
            opacity=0.5,
            visible=False,
        ),
    )
    return fig


def add_new_stock(fig, symbol):
    global STOCKS, DAYSTOCKS

    # Get company id from COMPANIES
    cid = COMPANIES.loc[COMPANIES["symbol"] == symbol, "id"].values[0]

    # Query all stocks with cid
    stocks_query = f"SELECT date, value FROM stocks WHERE cid = {cid}"
    stocks_query_df = pd.read_sql_query(stocks_query, engine)

    # Query all daystocks with cid
    daystocks_query = (
        f"SELECT date, open, close, high, low, volume FROM daystocks WHERE cid = {cid}"
    )
    daystocks_query_df = pd.read_sql_query(daystocks_query, engine)

    # Set date as index
    stocks_query_df.set_index("date", inplace=True)
    daystocks_query_df.set_index("date", inplace=True)

    # Format datetime
    stocks_query_df.index = pd.to_datetime(stocks_query_df.index).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    daystocks_query_df.index = pd.to_datetime(daystocks_query_df.index).strftime(
        "%Y-%m-%d"
    )

    # Change value column name to symbol name
    stocks_query_df.rename(columns={"value": symbol}, inplace=True)

    # Add symbol column to daystocks
    daystocks_query_df["symbol"] = symbol

    # Concatenate the new stocks with the existing ones
    STOCKS = pd.concat([STOCKS, stocks_query_df], axis=1).sort_index()

    # Concatenate the new daystocks with the existing ones
    DAYSTOCKS = pd.concat([DAYSTOCKS, daystocks_query_df], axis=0).sort_index()

    fig = add_all_traces(fig, symbol)
    return fig


def compute_date_range(fixed_date):
    start_date, end_date = MIN_DATE, MAX_DATE
    fixed_date = fixed_date.upper()
    if fixed_date == "1D":
        start_date = end_date - relativedelta(days=1)
    elif fixed_date == "5D":
        start_date = end_date - relativedelta(days=5)
    elif fixed_date == "1M":
        start_date = end_date - relativedelta(months=1)
    elif fixed_date == "3M":
        start_date = end_date - relativedelta(months=3)
    elif fixed_date == "6M":
        start_date = end_date - relativedelta(months=6)
    elif fixed_date == "YTD":
        start_date = date(end_date.year, 1, 1)
    elif fixed_date == "1Y":
        start_date = end_date - relativedelta(years=1)
    elif fixed_date == "5Y":
        start_date = end_date - relativedelta(years=5)
    elif fixed_date == "ALL":
        start_date = MIN_DATE

    if start_date < MIN_DATE:
        start_date = MIN_DATE

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")


def create_company_details(company, company_index, symbols):
    selected_symbols = SELECTED_SYMBOLS.intersection(symbols)
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
                            "index": company_index,
                        },
                        inputStyle={
                            "width": "15px",
                            "height": "15px",
                        },
                        className="d-inline-block",
                        value=[company] if company in SELECTED_COMPANIES else [],
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
                    "index": company_index,
                },
                style={"margin-left": "30px"},
                value=list(selected_symbols),
            ),
        ],
        className="my-2",
    )

    return html_details


# -- Callbacks
@app.callback(
    Output("input-company", "disabled"),
    Output("input-company", "value"),
    Input("market-selection", "value"),
    Input("graph-option-trash-can", "n_clicks"),
    prevent_initial_call=True,
)
def disable_input_company(market_id, trash_can_clicks):
    reset_input = market_id is None or trash_can_clicks is not None
    if reset_input:
        global SELECTED_COMPANIES, SELECTED_SYMBOLS
        SELECTED_COMPANIES, SELECTED_SYMBOLS = set(), set()
    return not market_id, ""


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
    State({"type": "company-checkbox", "index": MATCH}, "options"),
    State({"type": "symbol-checkbox", "index": MATCH}, "options"),
    prevent_initial_call=True,
)
def update_children_checkbox(company_checkbox_value, coptions, soptions):
    company = coptions[0]["value"]
    symbols = []
    if not company_checkbox_value:
        SELECTED_COMPANIES.discard(company)
        for option in soptions:
            SELECTED_SYMBOLS.discard(option["value"])
        return symbols

    SELECTED_COMPANIES.add(company)
    for option in soptions:
        symbols.append(option["value"])
        SELECTED_SYMBOLS.add(option["value"])
    return symbols


@app.callback(
    Output("dummy-div", "n_clicks"),
    Input({"type": "symbol-checkbox", "index": ALL}, "value"),
    State({"type": "symbol-checkbox", "index": ALL}, "options"),
    prevent_initial_call=True,
)
def update_selected_symbol(symbols_value, soptions):
    if ctx.triggered_id is None:
        raise dash.exceptions.PreventUpdate
    idx = ctx.triggered_id["index"]
    symbol = soptions[idx][0]["value"]
    if not symbols_value[idx]:
        SELECTED_SYMBOLS.discard(symbol)
    else:
        SELECTED_SYMBOLS.add(symbol)
    return 0


@app.callback(
    Output("lin-btn", "className"),
    Output("log-btn", "className"),
    Input("lin-btn", "n_clicks"),
    Input("log-btn", "n_clicks"),
)
def toggle_lin_log_btn(*args):
    lin_class = "lin-log-btn hoverable-btn"
    log_class = "lin-log-btn hoverable-btn"
    if ctx.triggered_id is None or ctx.triggered_id == "lin-btn":
        lin_class += " active"
    else:
        log_class += " active"
    return lin_class, log_class


@app.callback(
    Output("stock-graph", "figure"),
    State("stock-graph", "figure"),
    Input("date-picker-range", "start_date"),
    Input("date-picker-range", "end_date"),
    Input({"type": "symbol-checkbox", "index": ALL}, "value"),
    State({"type": "symbol-checkbox", "index": ALL}, "options"),
    Input("graph-option-polyline", "n_clicks"),
    Input("graph-option-candles", "n_clicks"),
    Input("graph-option-area-chart", "n_clicks"),
    Input("graph-option-trash-can", "n_clicks"),
    Input("lin-btn", "n_clicks"),
    Input("log-btn", "n_clicks"),
    Input({"type": "fixed-date-btn", "index": ALL}, "n_clicks"),
    prevent_initial_call=True,
)
def update_graph_polyline(
    fig,
    start_date,
    end_date,
    svalues,
    soptions,
    polyline_clicks,
    candlestick_clicks,
    bollinger_clicks,
    *args,
):
    # Handle plotly bug when converting fig to go.Figure
    if "rangeslider" in fig["layout"]["xaxis"]:
        del fig["layout"]["xaxis"]["rangeslider"]["yaxis"]
    fig = go.Figure(fig)

    if (
        isinstance(ctx.triggered_id, dict)
        and ctx.triggered_id["type"] == "symbol-checkbox"
    ):
        global STOCKS

        # Get the checked/unchecked symbol
        idx = ctx.triggered_id["index"]
        soptions = soptions[idx]
        svalues = svalues[idx]
        symbol = soptions[0]["value"]

        if not svalues:
            # If symbol is unchecked, remove it from the figure
            fig.update_traces(
                visible=False, selector=lambda trace: symbol in trace["name"]
            )
        else:
            if symbol not in STOCKS.columns:
                # Fetch the stock data from the database and add it to the figure
                fig = add_new_stock(fig, symbol)
            elif not fig_contains_symbol_trace(fig, symbol):
                fig = add_all_traces(fig, symbol)

            is_poly_visible = polyline_clicks is not None and polyline_clicks % 2 == 1
            is_candle_visible = (
                candlestick_clicks is not None and candlestick_clicks % 2 == 1
            )
            is_bollinger_visible = (
                bollinger_clicks is not None and bollinger_clicks % 2 == 1
            )

            if is_poly_visible:
                fig.update_traces(
                    visible=True, selector=dict(name=symbol, type="scatter")
                )
            if is_candle_visible:
                fig.update_traces(
                    visible=True, selector=dict(name=symbol, type="candlestick")
                )
            if is_bollinger_visible:
                fig.update_traces(
                    visible=True,
                    selector=lambda trace: trace["name"] == f"bollinger-{symbol}",
                )
    elif ctx.triggered_id == "lin-btn":
        fig.update_layout(yaxis_type="linear")
    elif ctx.triggered_id == "log-btn":
        fig.update_layout(yaxis_type="log")
    elif ctx.triggered_id == "graph-option-polyline":
        is_visible = polyline_clicks % 2 == 1
        fig.update_traces(
            visible=is_visible,
            selector=lambda trace: trace["type"] == "scatter"
            and "bollinger" not in trace["name"],
        )
    elif ctx.triggered_id == "graph-option-candles":
        is_visible = candlestick_clicks % 2 == 1
        fig.update_traces(visible=is_visible, selector=dict(type="candlestick"))
    elif ctx.triggered_id == "graph-option-area-chart":
        is_visible = bollinger_clicks % 2 == 1
        fig.update_traces(
            visible=is_visible, selector=lambda trace: "bollinger" in trace["name"]
        )
    elif ctx.triggered_id == "graph-option-trash-can":
        fig = go.Figure(layout=BASIC_FIG_LAYOUT)  # Reset graph
    elif "date-picker-range" == ctx.triggered_id and not start_date and not end_date:
        fig.update_layout(xaxis=dict(type="date", range=[MIN_DATE, MAX_DATE]))

    # Update time range
    if start_date and end_date:
        fig.update_layout(xaxis=dict(type="date", range=[start_date, end_date]))

    if (
        isinstance(ctx.triggered_id, dict)
        and ctx.triggered_id["type"] == "fixed-date-btn"
    ):
        fixed_date = ctx.triggered_id["index"]
        start_date, end_date = compute_date_range(fixed_date)
        fig.update_layout(xaxis=dict(type="date", range=[start_date, end_date]))

    return fig


@app.callback(
    Output("aggrid-table", "rowData"),
    Input("stock-graph", "figure"),
    prevent_initial_call=True,
)
def update_table_data(*arg):
    return get_aggrid_data()


@app.callback(
    Output("company-selection", "children"),
    Input("input-company", "value"),
    prevent_initial_call=True,
)
def update_company_selection(company):
    children = []
    if not company:
        return children

    unique_companies = COMPANIES["name"].str.lower().unique()
    matches = get_close_matches(company, unique_companies, n=5, cutoff=0.5)
    if not matches:
        return children

    for i, company in enumerate(matches):
        symbols = COMPANIES.loc[COMPANIES["name"] == company.upper(), "symbol"].values
        html_details = create_company_details(company, i, symbols)
        children.append(html_details)

    return children


@app.callback(
    Output("download-figure", "data"),
    State("stock-graph", "figure"),
    Input("save-btn", "n_clicks"),
    prevent_initial_call=True,
)
def save_graph(fig, *args):
    # Due to a bug in plotly, rangeslider on yaxis must be removed to convert fig to go.Figure
    if "rangeslider" in fig["layout"]["xaxis"]:
        del fig["layout"]["xaxis"]["rangeslider"]["yaxis"]
    fig = go.Figure(fig)
    img_bytes = fig.to_image(format="png")
    encoded_image = base64.b64encode(img_bytes).decode()
    return dict(base64=True, content=encoded_image, filename="plot.png")


@app.callback(
    Output("dummy-div", "children"),
    Input("market-selection", "value"),
    prevent_initial_call=True,
)
def update_companies(market_id):
    if not market_id:
        raise dash.exceptions.PreventUpdate

    # Query the database for the companies in the selected market
    query = f"SELECT id, name, symbol FROM companies WHERE mid = {market_id}"
    df_query = pd.read_sql_query(query, engine)

    # Concatenate the new companies with the existing ones
    global COMPANIES
    COMPANIES = pd.concat([COMPANIES, df_query], ignore_index=True)

    # Remove duplicates on symbols
    COMPANIES.drop_duplicates(subset="symbol", inplace=True)

    # Nothing to output
    raise dash.exceptions.PreventUpdate


# -- Clientside callbacks

clientside_callback(
    ClientsideFunction(namespace="clientside", function_name="toggle_full_screen"),
    Output("navbar-option-night-mode", "n_clicks"),
    Input("navbar-option-full-screen", "n_clicks"),
    prevent_initial_call=True,
)


if __name__ == "__main__":
    app.run(debug=True)

#!/usr/bin/env python
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import datetime

#read in excel data
data_df = pd.read_excel("data/aug_dec_2016.xlsx")

#lambda function to get monthly periods from date fields
to_string = lambda x: str(x)[:7]

#add monthly period columns as per directions
data_df['period'] = data_df.dateordered.apply(to_string)
data_df['rperiod'] = data_df.datereturned.apply(to_string)

#add returns column to separate true orders from true returns
data_df['returns'] = data_df.orders.where(data_df.orderstatus == 'returned',0)
data_df['orders'] = data_df.orders.where(data_df.orderstatus == 'complete',0)

#make new dataframes for returns & orders
returns = data_df[["rperiod","returns"]].copy()
orders = data_df[["period", "orders"]].copy()

#rename column
returns.rename(columns={"rperiod": "period"}, inplace=True)

#group by periods and sum
returns = returns[returns.period <> "NaT"].groupby("period")["returns"].sum().to_frame().reset_index()
orders = orders[orders.period <> "NaT"].groupby("period")["orders"].sum().to_frame().reset_index()

#merge the two new dataframes
month_df = pd.merge(returns,orders, how="outer", on="period").fillna(0)

#add return rate computed columns
month_df["return_rate"] = month_df.returns/month_df.orders
month_df["return_rate_percentage"] = month_df.returns/month_df.orders * 100
month_df["return_rate_percentage"] = month_df.return_rate_percentage.round(2)
month_df["return_rate_%_delta"] = ((month_df.return_rate_percentage - month_df.return_rate_percentage.shift(1))/month_df.return_rate_percentage.shift(1))
month_df["return_rate_%_delta"] = month_df["return_rate_%_delta"].round(2)

#output to excel
month_df.to_excel("data/results.xlsx")

#month name dict
months = {'1': 'January', '2': 'February', "3": "March", "4": "April",
    "5": "May", "6": "June", "7": "July", "8": "August", "9": "September",
    "10": "October", "11": "November", "12": "December"}

def pandas_gen_html_table(df):
    return html.Table(
        [html.Tr([html.Th(col, style = {"textAlign": "center"}) for col in df.columns])] +
        [html.Tr([html.Td(df.iloc[i][col], style = {"textAlign": "center"}) for col in df.columns]) for i in range(min(len(df), 20))],
        className = "table"
        )

#Dashboard app
app = dash.Dash()
app.layout = html.Div([
    html.Br(),
    dcc.Slider(
        id = "month-slider",
        min = data_df.dateordered.dt.month.min(),
        max = data_df.dateordered.dt.month.max(),
        marks = {str(i): months[str(i)] for i in data_df.dateordered.dt.month.unique()},
        value = data_df.dateordered.dt.month.min(),
        step = None
    ),
    html.Br(),
    html.H1(["Sales & Returns 2016"],
        style = {"textAlign": "center"}),
    dcc.Graph(
        id = "data-graph",
        animate=True),
    html.Div([
        html.H3(["Monthly Totals"],
            style = {"textAlign": "center"}),
        pandas_gen_html_table(month_df)
    ]),
],
className = "container")

@app.callback(
    dash.dependencies.Output("data-graph", "figure"),
    [dash.dependencies.Input("month-slider", "value")])
def update_df_graph(in_month):
    traces = []
    for i in data_df.orderstatus.unique():
        df_by_status = data_df[data_df.orderstatus == i]
        if i == "returned":
            filtered_df = df_by_status[df_by_status.datereturned.dt.month == in_month]
            filtered_df = filtered_df.groupby("datereturned")["returns"].sum().to_frame()
            traces.append(go.Scatter(
                x = filtered_df.index,
                y = filtered_df.returns,
                mode = "lines+markers",
                opacity = .7,
                marker = {
                    "line": {"width": .5, "color": "white"},
                    "symbol": "square"
                },
                name = i
            ))
        else:
            filtered_df = df_by_status[df_by_status.dateordered.dt.month == in_month]
            filtered_df = filtered_df.groupby("dateordered")["orders"].sum().to_frame()
            traces.append(go.Scatter(
                x = filtered_df.index,
                y = filtered_df.orders,
                mode = "lines+markers",
                opacity = .7,
                marker = {
                    "line": {"width": .5, "color": "white"},
                    "symbol": "201"
                },
                name = i
            ))

    return {
        "data" : traces,
        "layout" : go.Layout(
            title = "Returns & Orders by Month",
            xaxis={"range": [datetime.date(2016,8,1), datetime.date(2017,1,1)], "type": "date", "title": "Date"},
            yaxis = {"type": "Linear", "title": "# of Transactions"},
            legend = {"x": 1, "y": 1},
            hovermode = "closest"
        )
    }

#Include bootstrap css/js
boot_css = "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css"
dash_css = "https://codepen.io/chriddyp/pen/bWLwgP.css"
boot_js = "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js"
app.css.append_css({"external_url" : dash_css})
app.css.append_css({"external_url": boot_css})
app.scripts.append_script({"external_url": boot_js})

if __name__ == '__main__':
    app.run_server(debug=True)

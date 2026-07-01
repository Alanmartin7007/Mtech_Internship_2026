import pandas as pd
from dash import Dash, dcc, html
import plotly.express as px

df = pd.read_csv("cleaned_sales.csv")

app = Dash(__name__)

fig = px.bar(
    df.groupby("Category")["Sales"].sum().reset_index(),
    x="Category",
    y="Sales",
    title="Sales by Category"
)

app.layout = html.Div([
    html.H1("Sales Dashboard"),
    dcc.Graph(figure=fig)
])

if __name__ == "__main__":
    app.run(debug=True)
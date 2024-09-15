from dash import Dash, dcc, html, Input, Output
import plotly.express 
import plotly.graph_objects as go
import pandas
i = 0 
n = 0
rowArray = []
selectArray = []
valuesList = []
titleList = [] 
categoryValuesArray = {}


#Load census csv data
censusData = pandas.read_csv('data/CityCensusData.csv')

selectArray = [2, 3, 9, 49]

while i < len(selectArray):
    rowArray.append(censusData.iloc[selectArray[i]])
    i += 1

for index, row in enumerate(rowArray):
    key = f"categoryValues_{index+1}"
    categoryValuesArray[key] = list(map(int, row.iloc[1:].values))


x_values = rowArray[0].index[1:]

graphData = {"Neighbourhoood": x_values}

for key, y_values in categoryValuesArray.items():
    graphData[key] = y_values

graphDataFrame = pandas.DataFrame(graphData)

plotMelt_censusData = graphDataFrame.melt(id_vars="Neighbourhoood", var_name="Category", value_name="Value")

print(plotMelt_censusData)

#Assign bar graph variable
fig_bar = go.Figure()

#Plotly tracing
for category in plotMelt_censusData['Category'].unique():
    category_data = plotMelt_censusData[plotMelt_censusData ['Category'] == category]
    fig_bar.add_trace(go.Bar(
        x=category_data["Neighbourhoood"],
        y=category_data["Value"],
        name=category
    ))


#Render bar graph
fig_bar.update_layout(
    title="Multi-variable stacked bar graph using Census 2021 data, City of Toronto",
    xaxis_title="Neighbourhoood",
    yaxis_title="Value",
    barmode='stack'  
)

fig_bar.show()
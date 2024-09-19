import json
import dash
import pandas
import textwrap
import statistics
import geopandas as gpd 
import plotly.io as pio
import plotly.graph_objects as go
from dash import Dash, html, dcc, Input, Output, State
pio.kaleido.scope.mathjax = None

input_array = []
figGlobal = go.Figure()
figbarGlobal = go.Figure()
figbarstackGlobal = go.Figure()
neighbourhoodFilePath = "data/Neighbourhoods.geojson"
censusFilePath =  "data/CityCensusData.csv"

def censusMap (geoDataFilePath, dataSource, rowCompare, rowArrayBar, mapZoomSettings, fileName=None):
    '''
    A function to convert a single row of census 2021 data to a map relative to Toronto's neighbourhoods. 
    ----
    Parameters:
        geoDataFilePath - the path for the geoData (str to .geojson file path)
            "data/Neighbourhoods.geojson" for city-wide neighbourhood map
            "data/Ward23Neighbourhoods.geojson" for Ward 23  neighbourhood map
        dataSource - the path for the data (str to .json file path)
            "data/CityCensusData.csv" for city-wide Census 2021 data
            "data/Ward23CensusData.csv" for Ward 23 Census 2021 data
        rowCompare - the row in dataSource  to measure data from (int)
        title - the title of the graph (str)
        rowArrayBar - label for the variable (str)
        mapZoomSettings - specific settings for map zooming (array). Should be set up in form
            [Zoom variable (float), latitude (float), longitude (float), export height (int) [optional], export width (int) [optional]]
            ---
            Use [11, 43.710, -79.380, 2000, 1250] for City of Toronto-wide maps
            Use [12.6, 43.810, -79.245, 2000, 1250] for Ward 23 maps
        fileName - the path where you want to export the file in a PDF form. If left blank, the graph will not be exported. If this parameter is used, ensure mapZoomSettings have export heights and export widths (str)
    '''
    #Opens up geoData, reads and converts it to a JSON (feature), then converts it to a FeatureCollection readable by plotly
    geoData = gpd.read_file(geoDataFilePath)
    geoDataJSON = geoData.to_json()
    geoDataDict = json.loads(geoDataJSON)
    geoDataDict = {
        "type": "FeatureCollection",
        "features": geoDataDict['features']
    }

    rowArray = []

    #Imports Census Data
    censusData = pandas.read_csv(dataSource)

    rowCompare = int(rowCompare) - 2
    print(rowCompare)
    print("Row Compare")

    #Traverses censusData, appends the rowCompare value as an int relative to Neighbourhood array
    df_geo = pandas.DataFrame(geoData.drop(columns="geometry"))
    columnsSet = set(censusData.columns)
    graphTitle = censusData.iloc[rowCompare]["Neighbourhood Name"]
    for _, row in df_geo.iterrows():
        neighbourhood_name = row["AREA_NAME"]
        
        if neighbourhood_name in columnsSet:
            neighbourhood_data = censusData[neighbourhood_name] 
            rowArray.append(neighbourhood_data[rowCompare])
        else: 
            print(f"Not appended {neighbourhood_name}")

    #Creates a figure with its fill being the z value (in this case, rowArray), relative to all the other z values
    fig = go.Figure(go.Choroplethmapbox(
        geojson=geoDataDict,
        locations=geoData["AREA_ID"],  
        z=rowArray,  
        marker_opacity=0.5,
        marker_line_width=1,
        featureidkey="properties.AREA_ID", 
        text = geoData["AREA_NAME"],
        hoverinfo="text+z",
        hovertemplate= f"%{{text}}<br>%{{z}} {rowArrayBar}<extra></extra>",
        hoverlabel= dict(font = dict(family = "proxima-nova, sans-serif")),
        colorbar=dict(
            title=rowArrayBar,
            tickfont = dict(family = "proxima-nova, sans-serif"),
        )
    ))

    #Appends ward outlines (opens up data, gets coords, and then adds a Scatter trace with each trace connected with a line)

    cityGeoData = gpd.read_file("data/CityWards.geojson")
    cityGeoDataJSON = cityGeoData.to_json()
    cityGeoDataDict = json.loads(cityGeoDataJSON)
    cityGeoDataDict = {
        "cityGeoData": "FeatureCollection",
        "features": cityGeoDataDict["features"]
    }

    mainlonArray = []
    mainlatArray = []
    wardNameArray = []
 
    for feature in cityGeoDataDict["features"]:
        geometry = feature["geometry"]
        properties = feature["properties"]
        wardNameArray.append(properties["AREA_NAME"])
        for polygon in geometry["coordinates"]:
            for multiCoordinate in polygon:
                lonArray = []
                latArray = []
                for coordinate in multiCoordinate:
                    lonArray.append(coordinate[0])
                    latArray.append(coordinate[1])
                mainlonArray.append(lonArray)
                mainlatArray.append(latArray)
    i = 0
    for i in range(len(mainlatArray)):
        fig.add_trace(go.Scattermapbox(
            mode = "lines",
            showlegend=True,
            lon=mainlonArray[i],
            lat=mainlatArray[i],
            line=dict(width=2, color="red"),  
            text = wardNameArray[i],
            name =  wardNameArray[i],
            hoverlabel= dict(font = dict(family = "proxima-nova, sans-serif")),
        ))

    #Updates appearance
    fig.update_layout(
        mapbox_style="carto-positron", 
        mapbox_zoom=mapZoomSettings[0], 
        mapbox_center={"lat": mapZoomSettings[1], "lon": mapZoomSettings[2]}, 
        margin={"r":0,"t":60,"l":0,"b":0}, 
        title={"text": graphTitle, "x": 0.5, "xanchor": "center", "yanchor": "top", "font": {"family": "proxima-nova, sans-serif", "weight": 700, "size": 25}},
        legend=dict(
            x=1.1,               
            y=0.25,               
            xanchor="left",  
            yanchor="middle",
            font = {"family": "proxima-nova, sans-serif"}
        )
    )

    if fileName is not None and len(mapZoomSettings) == 5:
       fig.write_image(fileName, format="pdf", engine="kaleido", width= mapZoomSettings[3], height=mapZoomSettings[4])
    return fig 

def censusBar (dataSource, rowSelect, fileName = None):
    fig_bar = go.Figure()
    censusData = pandas.read_csv(dataSource)
    rowSelect -= 2
    rowArray = censusData.iloc[rowSelect].to_list()
    graphTitle = rowArray[0]
    rowArray.pop(0) 
    try:
        rowArrayFloat =  list(map(float, rowArray))
    except ValueError:
        rowArrayFloat = rowArray

    x_values = censusData.columns.to_list()
    x_values.pop(0)
    
    fig_bar.add_trace(go.Bar(
        x=x_values,
        y=rowArrayFloat,
        name="Neighbourhood<br>Data",
        marker_color="blue"
    ))

    x1_endpoint = len(fig_bar.data[0]["x"])

    if isinstance(rowArrayFloat[2], float):
        '''"Else" special case for if rowSelect = 1'''
        cityWideMedian = statistics.median(rowArrayFloat) 
            
        fig_bar.add_shape(
            type="line",
            x0=-0.5,  
            x1=x1_endpoint - 0.35,
            y0=cityWideMedian,
            y1=cityWideMedian,
            line=dict(color="red", width=3, dash="dash"), 
            name=f"City-wide Median<br>({cityWideMedian})"
        )
        fig_bar.add_trace(go.Scatter(
            x=[None],  
            y=[None],
            mode="lines",
            line=dict(color="red", width=2, dash="dash"),
            showlegend=True,
            name=f"City-wide Median<br>({cityWideMedian})"
        ))

    fig_bar.update_layout(
        title={"text": graphTitle, "x": 0.5, "xanchor": "center", "yanchor": "top", "font": {"family": "proxima-nova, sans-serif", "weight": 700, "size": 25}},
        xaxis_title= "Neighbourhood",
        yaxis_title= "Value",
        hoverlabel= dict(font = dict(family = "proxima-nova, sans-serif")),
        title_font=dict(family="proxima-nova, sans-serif"),
        xaxis_title_font=dict(family="proxima-nova, sans-serif"),
        yaxis_title_font=dict(family="proxima-nova, sans-serif"),
        font=dict(family="proxima-nova, sans-serif"),
    )
    return fig_bar


def censusBarStack (dataSource, input_array):
    i = 0 
    n = 0
    rowArray = []
    graphTitleArray = []
    categoryValuesDict = {}

    #Load census csv data

    censusData = pandas.read_csv(dataSource)

    while i < len(input_array):
        ''' In operating within a non-front-end environemnt include this statement. 
        -> input_array[i] -= 2
        This is conducted in the front-end as it'll adjust the cancel buttons'''
        rowArray.append(censusData.iloc[input_array[i]])
        graphTitleArray.append(censusData.iloc[input_array[i]]["Neighbourhood Name"])
        i += 1

    for index, row in enumerate(rowArray):
        key = f"categoryValues_{index+1}"
        categoryValuesDict[key] = list(map(float, row.iloc[1:].values))

    x_values = rowArray[0].index[1:]
    graphData = {"Neighbourhoood": x_values}

    for key, y_values in categoryValuesDict.items():
        graphData[key] = y_values

    graphDataFrame = pandas.DataFrame(graphData)

    plotMelt_censusData = graphDataFrame.melt(id_vars="Neighbourhoood", var_name="Category", value_name="Value")

    print(graphTitleArray)

    #Assign bar graph variable
    fig_bar_stack = go.Figure()

    #Plotly tracing
    for category in plotMelt_censusData['Category'].unique():
        category_data = plotMelt_censusData[plotMelt_censusData ['Category'] == category]
        fig_bar_stack.add_trace(go.Bar(
            x=category_data["Neighbourhoood"],
            y=category_data["Value"],
            name= "<br>".join(textwrap.wrap(graphTitleArray[n], width=18))
        ))
        n += 1

    #Render bar graph
    fig_bar_stack.update_layout(
        xaxis_title="Neighbourhoood",
        yaxis_title="Value",
        barmode="stack",
        hoverlabel= dict(font = dict(family = "proxima-nova, sans-serif")),
        title={"text": "Multi-variable stacked bar graph using Census 2021 data, City of Toronto", "x": 0.5, "xanchor": "center", "yanchor": "top", "font": {"family": "proxima-nova, sans-serif", "weight": 700, "size": 25}},
        xaxis_title_font=dict(family="proxima-nova, sans-serif"),
        yaxis_title_font=dict(family="proxima-nova, sans-serif"),
        font=dict(family="proxima-nova, sans-serif"),
    )
    return fig_bar_stack

fig = censusMap(neighbourhoodFilePath, censusFilePath , 35, "Values", [10, 43.710, -79.380, 2000, 1250])
fig_bar = censusBar(censusFilePath, 35)
app = Dash(__name__, suppress_callback_exceptions=True, prevent_initial_callbacks='initial_duplicate')

app.layout = html.Div(
    style={'color': '#252525'},
    children=[
        html.H1("Toronto Census Visualizer", style={"textAlign": "center"}),
        html.H3("By Derek Song, using data from Toronto Open Data", style={"textAlign": "center", "color": "white", "margin" : 0,}),
        html.Div(
            className = "flex",
            children=[
                html.H2("Enter row number from Census 2021 data", style={"marginRight": "20px"}),
                
                html.Div(
                    className = "flex-col",
                    children=[
                        dcc.Input(id="search", className="textbox fulwidth", type="text", value="35", debounce = True),
                        html.Div(id="suggestion", className="textbox-suggestion", children=[], style={"position": "relative", "display": "none"}),
                        html.Div(id="output")
                    ]
                ),
                html.Button("Export bar PDF", id="exportPDFBar", className="textbox addArray", n_clicks=0),
                html.Button("Export map PDF", id="exportPDFMap", className="textbox addArrayalt", n_clicks=0),
                dcc.Download(id="downloadPDFBar"),
                dcc.Download(id="downloadPDFMap")
            ]
        ),
        dcc.Graph(id="graph", style={"height": "1060px"}),
        dcc.Graph(id="graphBar", style={"height": "1060px"}),
        html.H1("Multi-variable stacked graphs", style={"textAlign": "center", "font-size": "3.5rem"}),
                html.Div(
            className = "flex",
            children=[
                html.H2("Enter row number from Census 2021 data", style={"marginRight": "20px"}),
                    html.Div(
                        className = "flex-col",
                        children=[
                            dcc.Input(id="multiVarInput", className="textbox fulwidth", type="text", value="35", debounce = True),
                            html.Div(id="suggestionStack", className="textbox textbox-suggestion", children=[], style={"position": "relative", "display": "none"}),]
                    ),
                html.Button("Add/Search", id="multiVarConfirm", className="textbox addArray", n_clicks=0),
                html.Button("Export stack PDF", id="exportPDFStack", className="textbox addArrayalt", n_clicks=0),
                dcc.Download(id="downloadPDFStack")
            ]
        ),
        html.Div(id="buttonContainer", className="buttonContainer"),
        dcc.Graph(id="graphBarStack", style={"height": "1060px"}),
        html.H1("About", style={"textAlign": "center", "font-size": "3.5rem"}),
        html.Div(
            className = "spacebwn",
            children=[
                html.Div (
                    className = "flex-col-text",
                    children = [
                        html.P(["While working on a transportation user experience research project, there were some questions about transportation method demand in the recent 2021 census that caught my eye. The City of Toronto does provide neighbourhood profile data, but that is limited to the 2016 census data, and only looks at a single neighbourhood. ", 
                        html.Strong("This tool aims to provide comparisons between all Toronto neighbourhoods, correlating to the 2021 census results.")]
                        ),
                        html.P("This tool uses Python, Plotly, Pandas, and GeoPandas to traverse the data. Dash is used to render the data to the front-end. Kaleido is used to assist with PDF rendering and exporting. Data is sourced from Toronto Open Data, specifically:"),
                        html.Ul([html.Li(html.A("Neighbourhood census data (.xlsx, then converted to .csv)",href="https://open.toronto.ca/dataset/neighbourhood-profiles/")),
                                 html.Li(html.A("Neighbourhood boundaries (.geojson)",href="https://open.toronto.ca/dataset/neighbourhoods/")),
                                 html.Li(html.A("Ward boundaries (.geojson)",href="https://open.toronto.ca/dataset/wards-and-elected-councillors/")),
                                 
                                 
                                 ]),
                        html.P([html.Strong("This tool is not affiliated nor endorsed by the City of Toronto or Statistics Canada."), " As such, please use at your own risk."])],
                ),
                html.Img(src="/assets/TorontoCensusGraph.svg", style={"width": "500px", "height": "auto"})
            ],
        )
    ]
)

@app.callback(
    [Output("graph", "figure"),
    Output("graphBar", "figure"),
    Output("suggestion", "children"),
    Output("suggestion", "style"),
    Output("downloadPDFBar", "data"),
    Output("downloadPDFMap", "data")],
    [Input("search", "value"), 
    Input({"type": "search-btn", "index": dash.dependencies.ALL}, "n_clicks"),
    Input("exportPDFBar", "n_clicks"),
    Input("exportPDFMap", "n_clicks")]
)

def update_output(value, _, exportPDFBar, exportPDFMap):
    global figGlobal, figbarGlobal, neighbourhoodFilePath, censusFilePath
    suggestionHTML = html.Ul([])
    suggestionStyle = {"position": "relative", "display": "none"}
    fig = figGlobal
    fig_bar = figbarGlobal
    exportFileBar = None
    exportFileMap = None
    ctx = dash.callback_context
    if ctx.triggered and "search-btn" in ctx.triggered[0]["prop_id"]:
        triggered = ctx.triggered
        indexStr = triggered[0]["prop_id"].split('.')[0]
        indexDic= json.loads(indexStr.replace("'", '"'))
        print(indexDic)
        if "index" in indexDic:
            index = int(indexDic["index"]) 

        print(index)
        fig = censusMap(neighbourhoodFilePath, censusFilePath, index, "Values", [10, 43.710, -79.380, 2000, 1250])
        figGlobal = fig
        fig_bar = censusBar(censusFilePath, index)
        figbarGlobal = fig_bar
    elif ctx.triggered and "exportPDFBar" in ctx.triggered[0]["prop_id"]:
        figbarGlobal.write_image("figBar.pdf", format="pdf", engine="kaleido", width = 3000)
        exportFileBar = dcc.send_file("figBar.pdf")
    elif ctx.triggered and "exportPDFMap" in ctx.triggered[0]["prop_id"]:
        figGlobal.write_image("figMap.pdf", format="pdf", engine="kaleido", width = 3000)
        exportFileMap = dcc.send_file("figMap.pdf")
    else:
        try:
            value =  int(value) 
            fig = censusMap(neighbourhoodFilePath, censusFilePath, value, "Value", [10, 43.710, -79.380, 2000, 1250])
            figGlobal = fig
            fig_bar = censusBar(censusFilePath, value)
            figbarGlobal = fig_bar
        except ValueError:
            censusData = pandas.read_csv(censusFilePath)
            suggestion = censusData[censusData["Neighbourhood Name"].str.contains(value, case=False, regex=False, na=False)]
            indices = suggestion.index[:5] + 2
            suggestionsFive = suggestion.head(5)
            suggestionList = suggestionsFive["Neighbourhood Name"].tolist()
            combinedList = [f"Row number: {ind} - {string}" for ind, string in zip(indices, suggestionList)]
            suggestionHTML = html.Ul([html.Li([
                html.Button (f"Row Number: {str(indices[i])} {suggestionList[i]}", className="textbox", id={"type": "search-btn", "index": int(indices[i])}, n_clicks=0)
                for i, p in enumerate(combinedList)
            ])
            ])
            
            if suggestionList is not None: 
                suggestionStyle = {"position": "relative", "display": "block"}
                
        
    return fig, fig_bar, suggestionHTML, suggestionStyle, exportFileBar, exportFileMap

@app.callback(
    Output("graphBarStack", "figure"),
    Output("suggestionStack", "children"),
    Output("suggestionStack", "style"),
    Output('buttonContainer', 'children'),
    Output("downloadPDFStack", "data"),
    Input("multiVarConfirm", "n_clicks"),
    Input({"type": "remove-btn", "index": dash.dependencies.ALL}, 'n_clicks'),
    Input({"type": "search-btn", "index": dash.dependencies.ALL}, 'n_clicks'),
    Input("exportPDFStack", "n_clicks"),
    State("multiVarInput", "value")          
)

def update_array(_, nc1, nc2,exportFileStack, input_value):
    global input_array, figbarstackGlobal, censusFilePath
    suggestionHTML = html.Ul([])
    suggestionStyle = {"position": "relative", "display": "none"}
    ctx = dash.callback_context
    fig_bar_stack = figbarstackGlobal
    censusData = pandas.read_csv(censusFilePath)
    exportFileStack = None
    if ctx.triggered and "remove-btn" in ctx.triggered[0]["prop_id"]:
        triggered = ctx.triggered
        indexStr = triggered[0]["prop_id"].split('.')[0]
        indexDic= json.loads(indexStr.replace("'", '"'))
        if "index" in indexDic:
            index = indexDic["index"]
            
            # Ensure index is valid and within bounds
            if index < len(input_array):
                input_array.pop(index)
        fig_bar_stack = censusBarStack(censusFilePath, input_array)
        figbarstackGlobal = fig_bar_stack
    
    elif ctx.triggered and "search-btn" in ctx.triggered[0]["prop_id"]:
        triggered = ctx.triggered
        indexStr = triggered[0]["prop_id"].split('.')[0]
        indexDic= json.loads(indexStr.replace("'", '"'))
        print(indexDic)
        if "index" in indexDic:
            index = indexDic["index"]
            input_array.append(index - 2)

        print("Input array")
        print(input_array)
        fig_bar_stack = censusBarStack(censusFilePath, input_array)
        figbarstackGlobal = fig_bar_stack

    elif ctx.triggered and "exportPDFStack" in ctx.triggered[0]["prop_id"]:
        figbarstackGlobal.write_image("figStack.pdf", format="pdf", engine="kaleido", width = 3000)
        exportFileStack = dcc.send_file("figStack.pdf")

    elif input_value.isnumeric():
        if ctx.triggered and int(input_value) <= 2604:
            input_array.append(int(input_value) - 2)  # Add input value to the array
            print(input_array)
            fig_bar_stack = censusBarStack(censusFilePath, input_array)
            figbarstackGlobal = fig_bar_stack
        elif ctx.triggered and int(input_value) > 2604 or ctx.triggered and int(input_value) < 2:
            raise ValueError ("Invaild input")
    
    else:
        suggestion = censusData[censusData["Neighbourhood Name"].str.contains(input_value, case=False, regex=False, na=False)]
        indices = suggestion.index[:5]
        suggestionsFive = suggestion.head(5)
        suggestionList = suggestionsFive["Neighbourhood Name"].tolist()
        combinedList = [f"Row number: {ind} - {string}" for ind, string in zip(indices, suggestionList)]
        suggestionHTML = html.Ul([html.Li([
            html.Button (f"Row Number: {str(indices[i] + 2)} {suggestionList[i]}", id={"type": "search-btn", "index": int(indices[i] + 2)}, n_clicks=0)
            for i, p in enumerate(combinedList)
        ])
        ])
        
        if suggestionList is not None: 
             suggestionStyle = {"position": "relative", "display": "block"}
        
    buttons = [html.Button(f"{val + 2} - {censusData.iloc[val + 2]["Neighbourhood Name"]}", id={"type": "remove-btn", "index": i}, className= "textbox addArray", n_clicks=0) for i, val in enumerate(input_array)]

    return fig_bar_stack, suggestionHTML, suggestionStyle, buttons, exportFileStack


if __name__ == '__main__':
    app.run_server(debug=True, port=8051)  
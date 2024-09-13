import plotly.graph_objects as go
import geopandas as gpd 
import pandas
import json
import plotly.io as pio
pio.kaleido.scope.mathjax = None
from dash import Dash, html, dcc, Input, Output

def censusMap (geoDataFilePath, dataSource, rowCompare, title, rowArrayBar, mapZoomSettings, fileName=None):
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
    print(censusData)

    #Subtracts two for header and zero indexing
    rowCompare = int(rowCompare)
    rowCompare -= 2

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
    elif fileName is not None: 
        print("Error - missing or invaild mapZoomSettings. It should have 5 numbers, with the last 2 indicating the width and height of the export accordingly")
    else: 
        print("Error - missing fileName or other critical error. The last parameter in your function should be a string ending in .pdf to your exported file")
    return fig 


fig = censusMap("data/Neighbourhoods.geojson", "data/CityCensusData.csv", 232, "Amount of Census 2021 respondents who listed driving as a method of transportation", "Respondents", [10, 43.710, -79.380, 2000, 1250])
app = Dash(__name__)

app.layout = html.Div(
    style={'color': '#252525'},
    children=[
        html.H1("Toronto Census Visualizer", style={"textAlign": "center"}),
        html.H3("By Derek Song, using data from Toronto Open Data", style={"textAlign": "center", "color": "white", "margin" : 0,}),
        html.Div(
            className = "flex",
            children=[
                html.H2("Enter row number from Census 2021 data"),
                dcc.Input(id="text-input", className="textbox", type="text", value="232")
            ]
        ),
        dcc.Graph(id ="output-div", figure=fig, style={"height": "1060px"}),
    ]
)

@app.callback(
    Output("output-div", "figure"),
    [Input("text-input", "value")]
)

def update_output(value):
    value =  int(value)
    fig = censusMap("data/Neighbourhoods.geojson", "data/CityCensusData.csv", value, "Amount of Census 2021 respondents who listed driving as a method of transportation", "Respondents", [10, 43.710, -79.380, 2000, 1250])
    return fig

if __name__ == '__main__':
    app.run_server(debug=True, port=8051)  
    print("Dash online")
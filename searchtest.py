import plotly.graph_objects as go
import geopandas as gpd 
import pandas
import json
import plotly.io as pio
pio.kaleido.scope.mathjax = None

from dash import Dash, html, dcc, Input, Output

def searchSuggest(search):
    n = 0
    suggestionList = []
    censusData = pandas.read_csv("data/CityCensusData.csv")
    suggestion = censusData[censusData["Neighbourhood Name"].str.contains(search, na=False, regex=True)]
    suggestionsFive = suggestion.head(5)

    while n < len(suggestionsFive): 
        if suggestionsFive.empty is False: 
            suggestionList.append(suggestionsFive.iloc[n]["Neighbourhood Name"])
            n += 1
        else:
            suggestionList.append(None)
            n+= 1
    
    return (search)
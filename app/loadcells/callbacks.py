
import logging
from pathlib import Path
from dash import Dash
import dash_table
import dash_html_components as html
import pandas as pd
import json
from textwrap import dedent as d
import flask
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import matplotlib as mpl
mpl.use('Agg') # headless!
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime
import time
import sys
import os
from dateutil import tz
from tzlocal import get_localzone

from .loadcelldata import loadCellDataMulti

NSD=2
def register_callbacks(dashapp):

    def figUpdate(useFrac,filePath, meanCenter):
        lcd = loadCellDataMulti(NSD,filePath)
        datal = []
        for i, df in enumerate(lcd.dfs):
            nr = df.shape[0]
            if nr == 0:
                return {}
            if nr > 2000:
                useFrac = 2000.0/nr
                dat = df.sample(frac=useFrac)
            else:
                dat = df
            dat.sort_index(inplace=True)
            useFrac = float(useFrac)
            if useFrac == 0.0:
                useFrac = 0.0001
            elif useFrac >= 0.99:
                useFrac = 1.0
            if useFrac < 1.0:
                dat = df.sample(frac=useFrac)
                dat.sort_index(inplace=True)
            else:
                dat = df
            nr = df.shape[0]
            ms = 5
            if nr > 1000:
                ms = 3
            if nr > 10000:
                ms = 2
            if meanCenter == "True":
                ytitle = 'Mean centered reported Mass (g)'
                meen = dat.iloc[:,1].mean()
                m = dat['mass'] - meen
                rmedian = m.rolling(10).median()
                series = {
                        'y': rmedian, # dat.iloc[:,1] - meen,
                        'x': dat.loc[:,'date'],
                        'mode': "markers", # 'lines+markers',
                        'marker': {'size': ms}
                    }
            else:
                ytitle = 'Reported Mass (g)'
                series = {
                    'y': dat.iloc[:,1],
                    'x': dat.loc[:,'date'],
                    'mode': 'markers',
                    'marker': {'size': ms}
                }
            datal.append(series)
        fnames = [os.path.split(x)[1] for x in lcd.infiles]
        
        fig = {}
        fig['data'] = datal
        fig['layout'] = {
                'height': 800,
                'title': '%.2f fraction of %d rows from %s' % (useFrac,nr,', '.join(fnames)),
                'xaxis': {'title':'Time',

                            'titlefont':{
                            'family':'Arial, sans-serif',
                            'size':22,
                            'color':'darkblue'
                            },
                    'showticklabels': True,
                    'tickangle':45,
                    'tickfont':{
                        'family':'Arial',
                        'size':11,
                        'color':'black'
                            }
                        },
                'yaxis': {'title':ytitle,
                          'titlefont':{
                            'family':'Arial, sans-serif',
                            'size':18,
                            'color':'darkblue'
                            },
                        },
                }
        return fig



    @dashapp.callback(
        Output('aplot', 'figure'),
        [Input('reloadbutton', 'n_clicks_timestamp')],
        [State('localstore', 'data'),State('frac','value'),State('chooser','value'),State('centerdata','value')])
    def updateFigure(reloadtime,sessdat,frac,fpath,meancenter):
        return figUpdate(sessdat['useFrac'],fpath,meancenter) 
        
    @dashapp.callback(
        Output('localstore', 'data'),
        [Input('chooser','value'),Input('frac','value')],
        [State('localstore', 'data')]
        )
    def updateFigure2(fpath,frac,sessdat):
        sessdat['filePath'] = fpath
        sessdat['useFrac'] = frac
        return sessdat

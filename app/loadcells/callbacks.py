
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
from config import BaseConfig
from .loadcelldata import loadCellDataMulti

NSD=3
def register_callbacks(dashapp):

	def figUpdate(useFrac,filePath, meanCenter, movMedian):
		"""
		dcc.Store(id='localstore', storage_type='session',
				data={'filePath': filePath, 'useFrac': 1, 'centerdata': False, 'movmedian': False}),
		"""
		flask.session['filePath'] = filePath
		flask.session['centerdata'] = meanCenter
		flask.session['fmovmedian'] = movMedian
		lcd = loadCellDataMulti(NSD,filePath)
		datal = []
		for i, df in enumerate(lcd.dfs):
			nr = df.shape[0]
			if nr == 0:
				return {}
			# if nr > 5000:
				# useFrac = 5000.0/nr
				# dat = df.sample(frac=useFrac)
			# else:
				# dat = df
			
			useFrac = float(useFrac)
			if useFrac == 0.0:
				useFrac = 0.0001
			elif useFrac >= 0.99:
				useFrac = 1.0
			flask.session['useFrac'] = useFrac
			if useFrac < 1.0:
				dat = df.sample(frac=useFrac)
				keepe = df.shape[0]
				keeps = max(0,keepe-BaseConfig.ALWAYSKEEPN)
				alwaysIn = df.iloc[keeps:keepe,:]
				dat = pd.concat([alwaysIn,dat],join="outer") # ensure last 20 minutes or so shown in full
			else:
				dat = df
			dat.sort_index(inplace=True)

			nr = df.shape[0]
			ms = 5
			if nr > 1000:
				ms = 3
			if nr > 10000:
				ms = 2
			yt = ""
			if movMedian == "True":
				yt = "Moving median "
				xwork = dat['mass'].rolling(10).median()
			else:
				xwork = dat.iloc[:,1]
			if meanCenter == "True":
				yt += 'Mean centered reported Mass (g)'
				meen = xwork.mean()
				m = xwork - meen
				series = {
						'y': m, # dat.iloc[:,1] - meen,
						'x': dat.loc[:,'date'],
						'mode': "markers", # 'lines+markers',
						'marker': {'size': ms}
					}
			else:
				yt += 'Reported Mass (g)'
				series = {
					'y': xwork,
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
				'yaxis': {'title':yt,
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
		[State('localstore', 'data'),State('frac','value'),State('chooser','value'),State('centerdata','value'),State('movmedian','value')])
	def updateFigure(reloadtime,sessdat,frac,fpath,meancenter,movmedian):
		return figUpdate(frac,fpath,meancenter,movmedian) 
		
	@dashapp.callback(
		Output('localstore', 'data'),
		[Input('chooser','value'),Input('frac','value')],
		[State('localstore', 'data')]
		)
	def updateFigure2(fpath,frac,sessdat):
		sessdat['filePath'] = fpath
		sessdat['useFrac'] = frac
		return sessdat

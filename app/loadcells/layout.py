import dash_core_components as dcc
import dash_html_components as html
from config import BaseConfig
from .loadcelldata import SftpClient
from paramiko import Transport, SFTPClient, RSAKey
import os
from datetime import timedelta as td
from datetime import datetime as dt

filePath = ''
useFrac = 0.3 # 
minStartDate=dt(2019, 10, 27)
maxEndDate=dt.now() + td(days=7)

def fileChooser(returnv = False):
    """Need both the chooser list with values showing all files selected to start with
    something like [
                {'label': 'New York City', 'value': 'NYC'},
                {'label': 'Montreal', 'value': 'MTL'},
                {'label': 'San Francisco', 'value': 'SF'}
            ]
    """
    upload_remote_path = BaseConfig.REMOTEDATAPATH
    sftpkey = RSAKey.from_private_key_file(BaseConfig.SFTPKEYFILENAME)
    sftp = SftpClient(BaseConfig.REMOTEDATAHOST,BaseConfig.SFTPPORT,BaseConfig.SFTPLOGINUSER,BaseConfig.SFTPPASSWORD,sftpkey)
    sftp.dirch(upload_remote_path)
    fl = sftp.dirlist(upload_remote_path)
    fl.sort()
    fl = [x for x in fl if (x.split('.')[-1]=='xls')]
    ddl = []
    vals = []
    for fn in fl:
        ddl.append({'label':os.path.split(fn)[-1],'value': fn})
        vals.append(fn)
    if returnv:
        return vals
    else:
        return ddl


layout = html.Div(children=[
        html.Div(
            dcc.Graph(
                id='aplot',
                figure = {},
                config = {"autoresize":True}
                ),
        ), 

        html.Div(style={'width': 300, 'textAlign':'center'},
        children = [
            dcc.Store(id='localstore', storage_type='session',
                data={'filePath': filePath, 'useFrac': 0.4, 'centerdata': False, 'movmedian': False, 'minStartDate':minStartDate,'maxEndDate':maxEndDate}),
            html.Div('Files to load when reload button pressed',
                style={"fontSize":"small", "width":299, "textAlign":"center", "color": "darkred"}),
                dcc.Dropdown(
                    id='chooser',
                    options=fileChooser(False),
                    value = fileChooser(True),
                    multi=True),
            html.Div(title='Date range to show',style={"fontSize":"small", "width":299, "textAlign":"center", "color": "darkred"},children = [ 
			dcc.DatePickerRange(
				id='useDates',
				min_date_allowed=minStartDate,
				max_date_allowed=dt.now() + td(days=7),
				start_date=dt.now() - td(days=14),
				end_date=dt.now(),
			),
			html.Div(id='output-container-date-picker-range')]),
            html.Div("Subtract mean to 'center' each series?",
                style={"fontSize":"small", "width":299, "textAlign":"center", "color": "darkred"}),
            html.Div(dcc.RadioItems(
                id='centerdata',
                value='False',
                options=[{'value': i, 'label': i} for i in ['True', 'False']],
            labelStyle={'display': 'inline-block', 'margin': '6px'})),
            html.Div("Show moving median with window=10?",
                style={"fontSize":"small", "width":299, "textAlign":"center", "color": "darkred"}),
            html.Div(dcc.RadioItems(
                id='movmedian',
                value='False',
                options=[{'value': i, 'label': i} for i in ['True', 'False']],
                labelStyle={'display': 'inline-block', 'margin': '6px'})),

            html.Div('Fraction of all data to sample randomly when reload button pressed',
                style={"fontSize":"small", "width":299, "textAlign":"center", "color": "darkred"}),
            html.Div(
                dcc.Slider(id='frac', min=0.0,max=1,step=0.001,marks={i/10.0: "{}".format(i/10.0) for i in range(1,11)},
                value=useFrac),title="Set fraction to reload",n_clicks=0),
            html.Br(),
            html.Button('Reload data sample', id='reloadbutton',n_clicks_timestamp=None,
             style={'width': 295, 'backgroundColor': "lightblue", "color": "darkred","fontSize":"small"})
        ])
  ])

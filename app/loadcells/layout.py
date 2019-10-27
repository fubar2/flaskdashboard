import dash_core_components as dcc
import dash_html_components as html
from config import BaseConfig
from .loadcelldata import SftpClient
from paramiko import Transport, SFTPClient, RSAKey

filePath = ''
useFrac = 1.0

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
    ddl = []
    vals = []
    for fn in fl:
        ddl.append({'label':fn.split('/')[-1],'value': fn})
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
                data={'filePath': filePath, 'useFrac': 1, 'centerdata': False, 'movmedian': False}),
            html.Div('Files to load when reload button pressed',
                style={"fontSize":"small", "width":299, "textAlign":"center", "color": "darkred"}),
                dcc.Dropdown(
                    id='chooser',
                    options=fileChooser(False),
                    value = fileChooser(True),
                    multi=True),
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

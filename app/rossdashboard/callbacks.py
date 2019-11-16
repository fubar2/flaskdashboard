import time
import random
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import urllib.request
import base64
import random
import logging

def register_callbacks(dashapp):
    """transplanted bbeachinflask.py minus layout and app/server
    """         


    external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
    logfname = 'dashross.log'
      
    def generate_table(urls):
        return html.Table(
            # Header
            # [html.Tr([html.Th(t) for t in titles)] +

            # Body
            [html.Tr([
                html.Td(html.Img(
                    width=400,#height=300,
                    src = urls[i])) for i in range(len(urls))]
            )])

    def geth1():
        return generate_table(["http://192.168.1.199/?cache=%d" % random.randint(0,30000),
        "http://192.168.1.200/?cache=%d" % random.randint(0,30000)])
        
    def geth3():
        return generate_table(["http://203.217.21.105:1050/jpg/2/image.jpg?cache=%d" % random.randint(0,30000),
        "http://webcams.bsch.com.au/bondi_beach/1252x940.jpg?cache=%d" % random.randint(0,30000),
        "http://192.168.1.108/snapshot.jpg?cache=%d" % random.randint(0,30000),
        "http://192.168.1.107/snapshot.jpg?cache=%d" % random.randint(0,30000)])

    @dashapp.callback([Output('logtext','value'),Output('logtext','title')],
                [Input('ltimer', 'n_intervals')])
                
    def updatelog(n_intervals):
        try:
            v = ''.join(open(logfname,'r').readlines())
        except:
            v = "new log file\n"
        d = 'Last updated at %s' % time.strftime('%H:%M:%S %d/%m/%Y')
        return v,d


    @dashapp.callback(Output('h3im','children'),
                [Input('btimer', 'n_intervals')])
    def display_hour3(n_intervals):
        t = geth3()
        dashapp.server.logger.info('## Hour3 images updated @'+ time.strftime('%H:%M:%S') + ' n_intervals = %d' % n_intervals)
        return t

    @dashapp.callback(Output("h1im",'children'),
                [Input('ptimer', 'n_intervals')])
    def display_hour(n_intervals):
        dashapp.server.logger.info('## Hour1 images updated @'+ time.strftime('%H:%M:%S') + ' n_intervals = %d' % n_intervals)
        t = geth1()
        return t
        

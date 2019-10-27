import dash_core_components as dcc
import dash_html_components as html
import random

hour3 = 1200 # secs
hour1 = 3600 # secs
logupdate = 300

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
    return generate_table(["http://203.217.21.105:1050/jpg/1/image.jpg?cache=%d" % random.randint(0,30000),
    "http://webcams.bsch.com.au/bondi_beach/1252x940.jpg?cache=%d" % random.randint(0,30000),
    "http://192.168.1.108/snapshot.jpg?cache=%d" % random.randint(0,30000),
    "http://192.168.1.107/snapshot.jpg?cache=%d" % random.randint(0,30000)])

layout = html.Div(children=[

    dcc.Interval(
            id='ltimer',
            interval=logupdate*1000 ,
            n_intervals = 0
            ),
    dcc.Interval(
            id='btimer',
            interval=hour3*1000 ,
            n_intervals = 0
            ),
    dcc.Interval(
            id='ptimer',
            interval=hour1*1000 ,
            n_intervals = 0
            ),

    html.Div(id = "h3im", children=[
        geth3()
        ]),
        
    html.Div(id = "h1im", children=[
        geth1()
        ]),
    html.Div(id = "logwin", children=[
        dcc.Textarea(id = "logtext",cols=60,rows=10,contentEditable=False,
        value="log goes here...",title='Last loaded')
        ])
    ])

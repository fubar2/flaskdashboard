Derived from:
*Dash on flask with flask_login
An example of a seamless integration of a Dash app into an existing Flask app based on the application factory pattern.
For details and how to use, please read: https://medium.com/@olegkomarov_77860/how-to-embed-a-dash-app-into-an-existing-flask-app-ea05d7a2210b*


The goal is to track plant weights during growth with a view to exploring growth rate as
an outcome for experiments with feeding frequency, strenght, lighting or whatever to maximise growth.

Complicated by all sorts of technical things such as bumping the scales or plants when visiting them; 
Pots have two pieces of watering pipe - one for drainage containers and the other for nutrients. These
may interfere if they touch anything and they do.

*What we are trying to measure*

The goal is to track a plant's weight gain over time.

Since they are in hydroponic ("hempy") pots, it is assumed 
that any change in mass must be either:
* a change in plant biomass or 
* a change in the mass of water in the pot from an automated timed watering event, manual watering or from loss due to plant transpiration or other evaporation.

In order to estimate rate of change of the biomass over time, a time series of instantaneous weights is collected from each plant, typically
every 30 seconds. 

In addition to real increases and decreases in plant biomass, there are important systematic sources of variation that must
be dealt with in analysis.

The most important is *automated watering*. The plants gain a lot of weight over a minute or so 4 times a day at present. The pot+plant will
be at the maximum possible weight at the peak after watering if the watering has produced a decent run off - medium will be saturated.
Another important one is that leaves are picked irregularly - damaged leaves are always removed and constant defoliation is useful for my growing style. 
Maybe 10g from one plant at one time. This will show as a loss of maximum but the slope between successive maxima should still give a useful estimate
of biomass gain.

Cheap loadcells are temperature sensitive and have a bad press for instability. In order to establish how bad the systemic and random variation
is, I'm keeping one with a fixed load for a while. So far, the range appears to be within about 8g in 4000 so 0.2%. That's arguably good enough for 
government work since the plants might transpire 10-30g/hour.

Automated watering is key to figuring out the weight growth trajectory since the maximum weight after each watering 
should be the a good estimate because I always water until there's lots of runnoff. 

Components

1. Raspberry pi zero w with 4 hx711 interfaces for 4 10kg load cells - all cheap chinese stuff from ebay

There is code that runs on a raspberry pi zero w to collect weight readings from multiple load cells periodically and sftp them to my fileserver where this code can read 
and plot them. The loadcells have HX711 A/D converter chips and each one uses 2 GPIO ports for clock and data. The zero can easily run 4 of them sampling at
30 second intervals - I have no interest in faster sampling but you'd need a faster CPU for faster sampling. I used cheap chinese ebay gear - about $20
altogher and was expecting poor data but am pleasantly surprised. From my experiments, it's a good idea to power down the HX711 between readings and
with my chips, use 3.7v rather than the 5v supply because heat may lead to horrible drift as has lead previous projects like the beekeeper one to
abandon load cells.

2. SFTP accessible server for file storage

Do not want to be writing regularly to the pi's SD card, so data are all exported to a file server via sftp. In my case it's all on the local lan but...YMMV
The config.py contains all the login and path details. Suggest you supply a public key file path rather than a password especially if you are going full interweb.

3. Data analysis and presentation

There's a dash in flask operation here (see head of this file). One component is a simple plotter for our data. All data series at the config.py path will be available for
plotting. A plot can be raw data but most of my series are at very different scales - bigger or smaller pots - so mean centering is a really good idea to make
more than one plot comparable. Additionally, a moving median can be plotted rather than the raw data. Makes it smoother for sure since there's a fair bit of noise in
the raw readings.

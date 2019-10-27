Code derived from:
*Dash on flask with flask_login
An example of a seamless integration of a Dash app into an existing Flask app based on the application factory pattern.
For details and how to use, please read: https://medium.com/@olegkomarov_77860/how-to-embed-a-dash-app-into-an-existing-flask-app-ea05d7a2210b*

Project goal is to track plant weights during growth with a view to exploring growth rate as
an outcome for experiments with feeding frequency, strength, lighting and so on as a driver
for improving yields.

*What we are trying to measure?*

The goal is to track a plant's weight gain over time.

Since they are in hydroponic ("hempy") pots, it is assumed 
that any change in mass must be either:

* a change in plant biomass or 

* a change in the mass of water in the pot from an automated timed watering event, manual watering or from loss due to plant transpiration or other evaporation.

In order to estimate rate of change of the biomass over time, a time series of instantaneous weights is collected from each plant, typically
every 30 seconds. 

*What measurement problems arise?*

Measurement as always, is complicated by technical, systematic and random errors. 

Random errors arise for example because:

* It's very easy to bump the scales or plants when visiting them or adjusting
LST and watering. 

* Pots have two pieces of watering pipe - one for drainage into containers and the other from the automated nutrient pump. These
may interfere with measurement if/when they bump into fixed and moving objects and they do. 

* The hardware (load cell, A/D converter) introduce their own systematic and random errors, but we try to minimise these by
leaving the HX711 powered down most of the time between samples and running on the 3.7v supply instead of 5V to minimise chip and circuit heat. 

Random variation is inevitable from the test setup - could be much better in a laboratory.

In addition to random error and real changes in plant biomass, there are important systematic sources of variation that must
be dealt with in analysis:

* Biggest is *automated watering*. The plants gain a lot of weight over a minute or so 4 times a day at present. The pot+plant will
be at the maximum possible weight at the peak after watering if the watering has produced a decent run off - medium will be saturated.

* Leaves are picked irregularly - damaged leaves are always removed and constant defoliation is useful for my growing style. 
Maybe 10g of fresh biomass might be taken from one plant at one time. This will show as a loss of maximum but the slope between successive maxima should still give a useful estimate
of biomass gain.

* Cheap loadcells are temperature sensitive and have a bad press for instability. We need weeks of data and cannot regularly re-tare the scales. In order to establish how bad the systemic and random variation
is, I'm keeping one with a fixed load for a while. So far, the range appears to be within about 8g in 4000 over a week, so 0.2% - and that was a week of wide temperature
variation. That's arguably good enough for government work since the plants might transpire 10-30g/hour.

Summary:

**Random variation is unavoidable and adds "noise". It's not so bad if it's unbiased which ours probably is so we essentially ignore it. Systematic variation is more or less fixed and consistent 
within each load cell/plant series and seem unlikely to make much difference to the estimate of growth based on the slope between successive watering time maximum weights** 

Components

1. Raspberry pi zero w with 4 hx711 interfaces for 4 10kg load cells - all cheap chinese stuff from ebay

* The loadcells have HX711 A/D converter chips and each one uses 2 GPIO ports for clock and data. The zero can easily run 4 of them sampling at
30 second intervals or so - set as SAMPINT in config.py. Much faster sampling would require a faster CPU. 

* I used cheap chinese ebay gear - about $20 altogher and was expecting poor data but am pleasantly surprised. From my experiments, it's a good idea to 
power down the HX711 between readings and with my chips, use 3.7v rather than the 5v supply because heat may lead to horrible drift as has lead previous projects like the beekeeper one to
abandon load cells. See the code...

* The load cells must be mounted on rigid plates to be useful and have predrilled holes for #4 and #5 bolts on different arms. Standoffs (I used washers 
between the load cell holes and the plates) are essential so the load cell does not ever touch a plate directly, even under load.

* Wiring the load cells to the HX711 chips correctly involves soldering some rather small things. 
Not recommended as a first project since without small-thing soldering skills, it's very easy to cook a chip or 
make messy short circuits.

* There is code that runs on a raspberry pi zero w to collect weight readings from multiple load cells periodically and sftp them to my fileserver where this code can read 
and plot them. 

2. SFTP accessible server for file storage

* In order to avoid hard failing SD cards, it's best not to be writing regularly to local storage, so data are all exported to a file server via sftp. 
In my case it's all on the local lan but...YMMV 
 
* config.py contains all the login and path details. Suggest you supply a public key file path rather than a password especially if you are going full interweb.

3. Data analysis and presentation

There's a dash in flask operation here (see head of this file). One component is a simple plotter for our data. All data series at the config.py path will be available for
plotting. A plot can be raw data but most of my series are at very different scales - bigger or smaller pots - so mean centering is a really good idea to make
more than one plot comparable. Additionally, a moving median can be plotted rather than the raw data. Makes it smoother for sure since there's a fair bit of noise in
the raw readings.

Code derived from:
*Dash on flask with flask_login
An example of a seamless integration of a Dash app into an existing Flask app based on the application factory pattern.
For details and how to use, please read: https://medium.com/@olegkomarov_77860/how-to-embed-a-dash-app-into-an-existing-flask-app-ea05d7a2210b*

*Project goal* 
Evaluate biomass growth rate as a potential dependent variable for experiments with feeding frequency, strength, lighting and so on as a driver
for improving hydroponic crop yields, using inexpensive commodity hardware and the software in this repository.

*What we are trying to measure?*

One major aim is to gather data that tracks a plant's weight gain over time so the rate of change in biomass can be estimated.

In order to estimate the rate of change, a time series of instantaneous weight measurements is collected from a load cell positioned underneath the pot. Sampling every 
30 seconds seems to give reasonable detail without being too unwieldy.

Since they are in hydroponic ("hempy") pots, all nutrients are supplied in the watering solution, so no loss of mass as would be expected as soil became depleted of soluble 
nutrients, is expected over the growing period. 

Note that the total mass at any time includes *a fixed component* - the pot plus the water free medium and *some variable 
components*:

* the growing plant biomass

* the mass of water held in the hydroponic medium 

* the mass of water in any reservoir

We are trying to measure the first one, but will need to take account of the other variable sources of change.

It seems reasonable to assume *that any real change in the total mass* can only arise from:

* real change in plant biomass and/or 

* real change in the mass of water in the pot from an automated timed watering event, manual watering or from loss due to plant transpiration or other evaporation.


*What measurement problems arise?*

Measurement as always, is complicated by technical, systematic and random errors. 

Random errors arise for example because:

* It's very easy to bump the scales or plants when viewing them let alone handling the plants when 
scouting for pests with a loupe, pruning or manually watering. No attempt was made to avoid these necessary interventions.

* Pots have two pieces of plastic irrigation pipe attached. The bottom one is for drainage into containers and the other carries fluid from the automated nutrient pump attached
to the nutrient reservoir. These pipes can ay interfere with measurement if/when they bump into fixed and moving objects. And they certainly do. 

* The hardware (load cell, A/D converter) introduce their own systematic and random errors, but we try to minimise these by
leaving the HX711 powered down most of the time between samples and running on the 3.7v supply instead of 5V to minimise chip and circuit heat. 

Random variation is inevitable from the test setup - could be much better in a laboratory.

In addition to random error and real changes in plant biomass, there are important systematic sources of variation that must
be dealt with in analysis:

* *Automated watering*. The plants gain a lot of weight over a minute or so 4 times a day at present. The pot+plant will
be at the maximum possible weight at the peak after watering if the watering has produced a decent run off - medium will be saturated. This seems a
key assumption for estimating growth in each series *as a slope between the maximum values after each watering*.

* Leaves are picked irregularly - damaged leaves are always removed and regular defoliation is practised to shape and control the plants. 
Maybe 10g of fresh biomass might be taken from one plant at one time. This was easy to see in the first test days as a loss of maximum.  Since this is
inevitable, another key assumption is that if a series shows a discontinuity downward between two successive maxima, that represents a 
scale change possibly after defoliation, so is considered to end the current group of increasing maxima used to estimate a growth slope. Between these
discontinuities of loss of biomass, *Slope between successive increasing maxima* should give a useful estimate of biomass gain over time and the 
discontinuities should not bias the estimates as long as they are accounted for in the analysis as a way to partition periods between episodes of biomass removal
for slope estimation.

* Cheap loadcells are temperature sensitive and have a bad press for instability. We need weeks of data and cannot regularly re-tare the scales. In order to establish how 
bad the systemic and random variation is, I'm keeping one with a fixed load. So far, the range appears to be within about 8g in 4000 over a week, so 0.2% - and that was a 
week of wide temperature variation. That's arguably good enough for government work since the plants might transpire 10-50g/hour.

Summary:

**Random variation is unavoidable and adds "noise". It's not so bad if it's unbiased which ours probably is so we essentially ignore it. Systematic variation is more or less fixed and consistent 
within each load cell/plant series and seem unlikely to make much difference to the estimate of growth based on the slope between successive watering time maximum weights** 

*Components*

1. The protype hardware comprises a Raspberry pi zero w attached to 4 hx711 A/D chips each wired to a 10kg load cell - cheap no-name, documentation free chinese kit from ebay.
It's a fugly mess of (labelled!) wires and plugs but it's mine and it works fine.

* The loadcells have HX711 A/D converter chips and each one uses 2 GPIO ports for clock and data. The zero can easily run 4 of them sampling at
30 second intervals or so - set as SAMPINT in config.py. Much faster sampling would require a faster CPU. 

* I used cheap chinese ebay gear - about $20 altogher and was expecting poor data but am pleasantly surprised. From my experiments, it's a good idea to 
power down the HX711 between readings and with my chips, use 3.7v rather than the 5v supply because heat may lead to horrible drift as has lead previous projects like the beekeeper one to
abandon load cells. See the code...

* The load cells must be mounted on rigid plates to be useful. I hacked some pine fencing. The aluminium load cells have threaded holes for bolts. One set #4 and one set #5. 
Standoffs (make sure each bolt goes through 2 washers that are compressed between the load cell and the plate) 
are essential so the load cell does not ever touch a plate directly, even under load.

* Wiring the load cells to the HX711 chips involves correctly soldering some rather small things and making good decisions about which wire goes where.
Labels and Google for documentation (since none comes with the cheap chinese kit) are essential for sanity. 
This is definitely not an ideal choice as a first project since without excellent vision, steady hands, a reliable tiny soldering iron
and extensive small-thing soldering skills, it's very easy to cook a chip or make messy short circuits. Should be good by about the third one I reckon so buy some spares.

* The raspberry pi runs some python code as a service after an initial interactive run when each scale is tared and calibrated with a known weight. Calibrations are
reused each time the raspberry pi starts the service until the next calibration is performed interactively. The code takes weight readings from multiple load cells 
periodically and posts them to my fileserver using SFTP, where the Flask webapp code can read and plot them interactively. 

* Dependencies for the raspberry pi code include the HX711 and Rpy.GPIO python modules. They are all taken care of by using the pip requirements files on the pi. 
Please, use a virtual environment for the server but I only use the pi zero for this project so have adjusted the system python. Something like

> pip3 install -r pirequirements.txt

should work.

2. SFTP accessible server for file storage

* In order to avoid regular aggravation from hard failed SD cards, it's best not to be writing regularly to local storage, so data are all exported to a file server via sftp. 
In my case it's all on the local lan but...YMMV 
 
* config.py contains all the login and path details. Suggest you supply a public key file path rather than a password especially if you are going full interweb.

3. Data analysis and presentation

* There's an interactive web "dash in flask" application in this repository based on a project described at the head of this file). 

* One component is a simple plotter for our data. All data series at the config.py path will be available for plotting. 

* Plot can use raw measured mass data. Most of my series have widely different dynamic ranges of mass over time. There are bigger and smaller pots, and 
plant phenotypes with bigger or smaller water use. In this case, mean centering is a really good idea to make more than one plot comparable. 
Mean centering only changes the Y scale but otherwise makes no difference to the shape of each series. It certainly does 
make multiple series with variable dynamic ranges much easier to compare because the Y axis range is smaller compared to a non-centered multiple series plot, 
where a larger Y axis range results in a lot of fine detail being lost in each individual series.

* These plots are interactive and that becomes silly slow with big data. A month will be about 3000*30=90000 data points. No point plotting them all when a random sample
of say, 5000 points from each series will give excellent fidelity with reasonable interactivity. Repeating a plot may give a rather different appearance using down-sampled raw data.
Outliers vary in each sample, and the Y axis scale automatically adapts to accomodate the most extreme high and low outliers. Outliers are sampled randomly like everything else. 
The pattern remains the same but the scale jumps around with each unscaled sampling procedure. This makes me unhappy but there are methods to help decrease it.

* A moving median can be plotted rather than the raw data to make the plots less jittery. This can also be mean centered and both these techniques are recommended for
routing use when comparing multiple plant weight patterns. This does change the shape of the series and makes it smoother for sure, removing a fair bit of noise in
the raw readings as described above. More importantly, *repeated sampling of moving median data with the same parameters produces more or less indistinguishable plots* 
with occasional small changes in the Y axis scale in contrast to the more variable sampled raw data multiple series plots. This stability makes them more appealing to me.


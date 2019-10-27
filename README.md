Derived from:
*Dash on flask with flask_login
An example of a seamless integration of a Dash app into an existing Flask app based on the application factory pattern.
For details and how to use, please read: https://medium.com/@olegkomarov_77860/how-to-embed-a-dash-app-into-an-existing-flask-app-ea05d7a2210b*

There is code that runs on a raspberry pi zero w to collect weight readings from multiple load cells periodically and sftp them to my fileserver where this code can read 
and plot them. The loadcells have HX711 A/D converter chips and each one uses 2 GPIO ports for clock and data. The zero can easily run 4 of them sampling at
30 second intervals - I have no interest in faster sampling but you'd need a faster CPU for faster sampling. I used cheap chinese ebay gear - about $20
altogher and was expecting poor data but am pleasantly surprised. From my experiments, it's a good idea to power down the HX711 between readings and
with my chips, use 3.7v rather than the 5v supply because heat may lead to horrible drift as has lead previous projects like the beekeeper one to
abandon load cells.

The goal is to track plant weights during growth with a view to exploring growth rate as
an outcome for experiments with feeding frequency, strenght, lighting or whatever to maximise growth.

Complicated by all sorts of technical things such as bumping the scales or plants when visiting them; 
Pots have two pieces of watering pipe - one for drainage containers and the other for nutrients. These
may interfere if they touch anything and they do.
Cheap loadcells are temperature sensitive - I'm keeping one with a fixed load for a while and the amplitude
appears to be about 8g in 4000 so 0.2% - good enough for government work since the plants might transpire
20g/hour.

Automated watering is key to figuring out the weight growth trajectory since the maximum weight after each watering 
should be the a good estimate because I always water until there's lots of runnoff. 

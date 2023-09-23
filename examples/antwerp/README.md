# Proppy example: LoRaWAN links in Antwerp, Belgium
This directory contains files that showcase how ``proppy`` can be used to learn
a model for
[LoRaWAN](https://www.thethingsnetwork.org/docs/lorawan/what-is-lorawan/) link
quality using data. The data is published by
[Aernouts et al.](https://www.mdpi.com/2306-5729/3/2/13).


**NOTE**:
This example uses data that may not yet be publicly available. The data should be made available soon.


This example projects shows how to:
- [x] Attach terrain data to line-segments using the ``proppy.raster`` submodule;
- [x] Visualize the terrain data and how it is generated;
- [x] Train a wireless connection quality model that uses terrain data;
- [x] Make predictions using the model;
- [x] Visualize predicted connection quality
- [ ] Use data to fit a macine learning model
- [ ] Visualize the model fit


## Extracting link-level
The first task in propagation modeling is to extract the relevant *wireless links*. A link represent one uplink-receiver pair. The noteook `make_linkdate.ipynb` shows how this is done systematically for LoRaWAN data from Antwerp.

## Querying raster data for wireless links
The more we know about a link, the better we can predict its quality. The `proppy.raster`-submodule is designed help query raster images for data on wireless links. The notebook `make_godata.ipynb` shows how this is done for our linkdata in Antwerp. 


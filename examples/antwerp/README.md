# Proppy example: LoRaWAN links in Antwerp, Belgium
This directory contains files that showcase how ``proppy`` can be used to learn
a model for
[LoRaWAN](https://www.thethingsnetwork.org/docs/lorawan/what-is-lorawan/) link
quality using data. The data is published by
[Aernouts et al.](https://www.mdpi.com/2306-5729/3/2/13).

This example projects shows how to:
- Attach terrain data to line-segments using ``proppy.raster``;
- Visualize the terrain data and how it is generated;
- Train a wireless connection quality model that uses terrain data;
- Make predictions using the model;
- Visualize predicted connection quality.
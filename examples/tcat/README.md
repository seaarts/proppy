# Example: Estimating LoRaWAN propagation from bus data

This directory uses `proppy` to estimate a LoRaWAN propagation model from data collected
from a tracker on a bus.
The data was collected by Tompkins Consolidated Area Transit (TCAT) in Ithaca, NY, 2022.


Preprocessing
=============
Raw data is stored in ``proppy/data/raw``. These are ``.json`` files. The notebook
``raw_to_links.ipynb`` preprocesses these data and consolidates them to ``links.csv``.

As the name implies ``links.csv`` contains link-level data. Each row is associated with
one successful (transmitter, receiver)-pair of a particular uplink. Features include
identifiers for the uplink, timestamp, receiver, as well as metadata describing the
quality of the wireless connection. Some bus data are also included, such as the location
of the GPS tracker, the speed of the bus, and so on.


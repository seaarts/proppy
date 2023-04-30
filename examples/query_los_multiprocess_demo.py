"""
A demo of querying LoS using multiprocessing.

To-do items:
- This can be adapted into a more complete function by looping over GWs.
- It also needs a "write to file" component.

"""
from functools import partial
from multiprocessing import Pool
from time import perf_counter

import fiona
import geopandas as gpd
import numpy as np
import rasterio as rio

import proppy.segments as prs


def loadDataAndRun(maxDist=2000, verbose=False):
    """Load data, make Rectangles, and query LoS."""

    t_start = perf_counter()  # time run

    # load inputs
    rasterfile = "../data/geneva_dsm_utm.tif"
    links = gpd.read_file("../data/links_demo.geojson")

    # get angle
    angle = prs.angle(links.geometry)

    # get rectangles
    relative_buffer = 0.001
    buffers = links["dist"].values * relative_buffer
    rects = prs.makeParallelRectangles(links.geometry.values, angle, buffers)

    # get const and slope
    zHead = links["elevation_tx"].values
    zTail = links["elevation_rx"].values
    const, slope = prs.getSlope(links.geometry, angle, zHead, zTail)

    # get length
    length = links.dist

    # form list Rectangle-objects
    n = len(rects)

    # form Rectangle-objects
    rectangles = []

    for i, _ in enumerate(rects):
        if length[i] <= maxDist:
            R = prs.Rectangle(i, rects[i], angle[i], const[i], slope[i], length[i])
            rectangles.append(R)

    # Main "loop" with multiprocessing
    myKwargs = {"nRows": 1, "distPerCol": 5, "rasterfile": rasterfile, "fillna": 136}
    with Pool() as p:
        out = p.map(partial(prs.queryMeanObstruction, **myKwargs), rectangles)

    t_stop = perf_counter()
    duration = t_stop - t_start
    obstructions = [output[1] for output in out]

    return duration, sum(obstructions) / len(obstructions)  # placeholder for now


if __name__ == "__main__":
    print("-" * 80)
    print("Running LoS queries (with multiprocessing)...")
    duration, val = loadDataAndRun()
    print(f"Mean obstruction = {val:.2f}")
    print(f"Completed in {duration:.2f} seconds.")

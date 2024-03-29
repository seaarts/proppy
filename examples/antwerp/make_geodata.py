"""
Query raster data for links in Antwerp, Belgium.

This method uses ``proppy.raster`` and ``multiprocessing``.
"""

from functools import partial
from multiprocessing import Pool
from time import perf_counter

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio as rio
import rioxarray as rxr

import proppy.raster as prs


def load_and_process(relative_buffer=0.5, ncols=100, nrows=20):
    # input data files
    links_file = "/Users/sander/Desktop/lora-tools/antwerp_links.geojson"
    path_raster = "/Volumes/Transcend/lora/data/antwerp-gis/dsm-1m-clipped.tif"

    # Load link data from file
    links = gpd.read_file(links_file)
    links = links.reset_index(drop=True)

    print(f"Loaded links (shape={links.shape}) with CRS {links.crs}.")

    # Link feautres
    lengths = links["distance"].values
    lines = links.geometry
    zheads, ztails = links["ele_tr"].values, links["ele_gw"].values

    # Compute rectangle features
    buffers = lengths * relative_buffer
    angles = prs.angle(lines)
    rects = prs.makeParallelRectangles(lines.values, angles, buffers)
    consts, slopes = prs.getSlope(lines, angles, zheads, ztails)

    # Form Rectangle-objects
    rectangles = []
    for i, _ in enumerate(rects):
        R = prs.Rectangle(i, rects[i], angles[i], consts[i], slopes[i], lengths[i])
        rectangles.append(R)

    # Main "loop" using multiprocessing
    fun_kwargs = {"nrows": nrows, "ncols": ncols, "rasterfile": path_raster}

    t_start = perf_counter()  # time run

    with Pool() as p:
        out = p.map(partial(prs.normalized_raster_values, **fun_kwargs), rectangles)

    t_stop = perf_counter()
    duration = t_stop - t_start

    return out, duration


if __name__ == "__main__":
    print("-" * 80)
    print("Querying raster (with multiprocessing)...")
    out, duration = load_and_process()
    print(f"Completed in {duration:.1f} seconds.")

    # expand list column and save
    df = pd.DataFrame.from_records(out, index="id")
    df = pd.DataFrame(df["data"].to_list(), columns=list(range(len(out[0]["data"]))))
    print(f"Saving dataframe of shape {df.shape}.")
    df.to_csv("../../data/antwerp_geodata.csv")

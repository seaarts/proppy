"""
====
data
====

.. todo::
  Raw TCAT data is not yet included on git. Find a place to host it and upload.
  Implement a ``DataSet`` class for loading the data, just like ``MNIST`` or ``omniglot``.

Tools for managing proppy datasets for ``PyTorch``. 

Based on PyTorch's
`data_tutorial <https://pytorch.org/tutorials/beginner/basics/data_tutorial.html#creating-a-custom-dataset-for-your-files>`_.
"""

import os
from typing import Any, Callable, Dict, List, Optional, Tuple

import geopandas as gpd
import numpy as np
import pandas as pd
import torch as th
from torch.utils.data import Dataset

# You can implement a subclass AntwerpLinksDataset
#   This downloads and creates the data if not available locally.
#   This allows a "train" keyword for predefined train-test splits.


class LinkDataset(Dataset):
    """
    Dataset for raster-enhanced wireless links.
    """

    def __init__(
        self, linkfile, rasterdir, datacols=None, transform=None, target_transform=None
    ):
        """Load labels from linkfile and initialize.

        Parameters
        ----------
        linkfile : str
            Path to geopandas-file with link data.
        rasterdir : str
            Path to directory with raster-derived image files.
        datacols : list
            List of column names to be included from the linkfile df.
        transform :
            Transform function for input data.
        target_transform :
            Transform function for labels.
        """

        links = gpd.read_file(linkfile)
        self.labels = links["succes"]

        if datacols:
            self.data = links[datacols]
        else:
            self.data = None

        self.raster_dir = rasterdir
        self.transform = transform
        self.target_transform = target_transform

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        label = self.labels.iloc[idx, 1]

        if self.data:
            data = self.data.iloc[idx].to_numpy()

        rastervals = np.genfromtxt(f"{self.rasterpath}/{idx}.csv", delimiter=",")
        rastervals = rastervals.flatten()

        if self.data:
            x = np.concatenate(data, rastervals)
        else:
            x = rastervals

        if self.transform:
            x = self.transform(x)
        if self.target_transform:
            label = self.target_transform(label)

        return x, label


class AntwerpLoRa(Dataset):
    """
    An `AntwerpLoRa <https://www.mdpi.com/2306-5729/3/2/13>`_ Dataset.

    .. todo::
        Upload data on IoT website. Add links to this class.
        Make sure it all works.


    Parameters
    ----------
    root : str
        Root directory of dataset where `antwerp_train`, `antwerp_test` and
        `antwerp_eval` exist.
    kind : str
        Specifies which dataset to load, from `train`, `test`, and `eval`.
    download : bool
        Specifies whether to download the data and save it.
    transform : callable
        A function/transform that  takes input data
        and returns a transformed version.
    target_transform : callable
        A function/transform that takes label data and
        returns a transformed version.

    Notes
    -----
    The data has been processed considerably, to remove observations with missing data,
    align GPS coordinates with roads, and remove observations from idling vehicles.
    """

    urls = [
        "https://github.com/brendenlake/omniglot/raw/master/python/images_background.zip",
        "https://github.com/brendenlake/omniglot/raw/master/python/images_evaluation.zip",
    ]

    datadir = "data/antwerp"

    def __init__(
        self,
        root: str,
        kind: str,
        download: bool = True,
        transform: Optional[callable] = None,
        target_transform: Optional[callable] = None,
    ):
        if download:
            self.download()

        pass

    def _check_exists(self):
        return os.path.exists(
            os.path.join(self.root, self.datadir, f"{self.kind}.geojson")
        ) and os.path.exists(
            os.path.join(self.root, self.datadir, f"{self.kind}_geodata")
        )

    def download(self):
        """From omniglot - NEEDS WORK."""
        import urllib

        if self._check_exists():
            return

        # download files
        try:
            os.makedirs(os.path.join(self.root, self.datadir))
            os.makedirs(os.path.join(self.root, f"{self.datadir}/{self.kind}_geodata"))
        except OSError as e:
            if e.errno == errno.EEXIST:
                pass
            else:
                raise

        for url in self.urls:
            print("== Downloading " + url)
            data = urllib.request.urlopen(url)
            filename = url.rpartition("/")[2]
            file_path = os.path.join(self.root, self.raw_folder, filename)

            with open(file_path, "wb") as f:
                f.write(data.read())

            file_processed = os.path.join(self.root, self.processed_folder)
            print("== Unzip from " + file_path + " to " + file_processed)
            zip_ref = zipfile.ZipFile(file_path, "r")
            zip_ref.extractall(file_processed)
            zip_ref.close()
        print("Download finished.")

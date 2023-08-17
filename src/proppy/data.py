"""
Tools for managing proppy datasets.

This module implements simple tools for managing and loading data to pythorch.


Based on
``https://pytorch.org/tutorials/beginner/basics/data_tutorial.html#creating-a-custom-dataset-for-your-files``
"""

import os

import pandas as pd
import torch as th
from torch.utils.data import Dataset


class RasterLinkDataset(Dataset):
    """
    Dataset for raster-enhanced wireless links.
    """

    def __init__(self, linkfile, raster_dir, transform=None, target_transform=None):
        """Load labels from linkfile and initialize."""
        self.labels = None
        self.raster_dir = raster_dir
        self.transform = transform
        self.target_transform = target_transform

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        """Retreive link data for given index."""

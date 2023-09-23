.. proppy documentation master file, created by
   sphinx-quickstart on Sat Sep 23 11:35:54 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to proppy's documentation!
==================================
``proppy`` is a package for data-driven radio propagation modeling.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

Submodules
==========

Included in ``proppy`` are implementations
of existing textbook propagation models in the ``models``-submodule. There are two submodules for associating
wireless links with data: ``raster`` for raster data, and ``shapes`` for shapefile data. In addition, the ``data``
submodule wraps wireless datasets as `pytorch datasets <https://pytorch.org/vision/0.15/datasets.html>`_ for
seamless use in ``pytorch``. 

.. automodule:: models
    :members:

.. automodule:: raster
    :members:

.. automodule:: shapes
    :members:

.. automodule:: data
    :members:







Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

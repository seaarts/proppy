
# proppy
Wireless propagation models for Python.

This package implements radio propagation models in Python, streamlining the use of data to
model and forecast wireless conneciton quality.

## Installation
Clone the `proppy` repo to your machine.
Then, naviage to the `proppy` directory and make sure `pip` is installed and up to date.
Then use `pip` to install the package.
```shell
pip install -e . 
```
The `-e` allows you to edit the contents and have your instalation automatically updated.

If you make changes or improvements, plase make a [pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests)
so we can improve this repo.

## Examples and use
Please see the ``/examples/`` folder for examples on how to use the package.

### [Using proppy.raster for LoRaWAN links in Antwerp, Belgium](https://github.com/seaarts/proppy/tree/main/examples/antwerp)
The [Antwerp example ](https://github.com/seaarts/proppy/tree/main/examples/antwerp) shows how to convert raw LoRaWAN `json` data
into usable link-level data, and how the `proppy.raster`-submodule is used to equip each link with geo-data.

### Projecting Line of Sight in Geneva, NY](https://github.com/seaarts/proppy/tree/main/examples/tcat)
**Under construction**.


## Documentation
The documentation is not yet online - but you can find it at `/docs/build/html/index.html`. This file can be
viewed in your browser.


### Writing documentation
The documentation is generated using [sphinx](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html).

When you write code, be sure to include a ``docstring``.
This is a specially formatted string wrapped in three double quotes.
```python
def myAddition(a, b):
    """
    Add `a` to `b`.

    Parameters
    ----------
    a : float
        The first number we wish to add.
    b : float
        The second number we wish to add.

    Returns
    -------
    c : float
        The sum of `a + b`.
```
You can read more about docstrings in the
[numpydoc style guide](https://numpydoc.readthedocs.io/en/latest/format.html).
See also the [sphinx documentation](https://www.sphinx-doc.org/en/master/index.html).

If you have written more code, it is recommended that you update the documentation.

### Updating the documentation
Any chanes made to `.py` or `.rst`-files are not immediately reflected in the documentation. To update the docs, navigate to `/docs/` and call `make html`. It can be good to `clean` first.
```shell
cd docs
make clean
make html
```
You should see output about the created documents, as well as any warnings or errors. The updated docs should
then be ready to view. It is recommended to update the docs frequently, as this will inform you of any errors
that you might have in your docstrings.

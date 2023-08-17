"""
======
raster
======

Associationg transmission line-segments with data from raster files.


This module is for querying data for 3-dimensional line segments
from raster images, e.g. digital elevation or surface models. A simple
example querying whether two points in space have line of sight. This is
equivalent to querying wether the line segment connecting the two points
intersects the terrain. The ``raster``-package is designed to run such queries.
It also enables the querying of richer data for line-segments. The module uses
``multiprocessing`` to process multiple queries in parallel.
"""

import contextily as cx
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import rasterio as rio
import shapely
from shapely.affinity import rotate
from shapely.geometry import LineString, Point, Polygon, box, mapping


class Rectangle:
    """A  rectangle for geometry queries.

    The ``Rectangle``-object encodes a rectangle for making queries on a raster.
    Its main use is to be populated by a grid of points whose values at on a
    raster are queried. The ``Rectangle``-object also tracks parameters associated
    with the underlying line-segment it represents.

    Attributes
    ----------
    id : int
        An index for the rectangle.
    poly : shapely.geometryPolygon
        An axis-parallel shapely rectangle over which to query geodata.
    angle : float
        Angle for rotating rectangles to original position.
    const : float
        Value of rectangle's tail z-axis position.
    slope : float
        Values of rectangle z-axis slope.
    length : float
        Length on x-axis of aligned rectangle.
    points : geopandas.GeoDataSeries
        Geoseries of points (or None if rectangle not yet populated).
    point_vals: array-like
        Array of values associated with points (or None)

    Notes
    -----
    This data structure is used to query rasters for LoS and other geometries.
    The use of axis-parallel rectangles with angles, constants and slopes is
    motivated by limitations of using raster data of varying resolutions:
        1. Rasters values can be queried at collections of points.
        2. Axis-aligned rectangles are easily overlayed with a grid of points.
        3. The elevation of rectangles floating in 3D is easily encoded with
        a constant and a slope.

    """

    def __init__(self, id, polygon, angle, constant, slope, length):
        """Initialize Rectangle collection."""
        self.id = id
        self.poly = polygon
        self.angle = angle
        self.const = constant
        self.slope = slope
        self.length = length

    def __repr__(self):
        return f"Rectanlge({self.__dict__})"

    def normalize_raster_values(self, points, vals):
        """Vertical distance between plane parallel to LoS-line and terrain.

        Parameters
        ----------
        points : geopandas.GeoDataFrame (?)
            Points at which values were queried.
        vals : np.array
            Raster values at points
        """

        x_values = np.array([point.x for point in points])

        heights = self.const + self.slope * x_values

        return heights - vals

    def _check_point_values(self):
        if self.points is None or self.point_vals is None:
            raise ValueError("Rectangle must have points and point_values to plot.")

    @property
    def rotated_poly(self):
        """Return polygon rotated by angle."""
        return rotate(self.poly, self.angle, "center", use_radians=True)

    def plot_vals(self, cmap="terrain_r", axis_off=True, **kwargs):
        """Plot the rectangle values.

        Built on geopandas.GeoDataFrame.plot().
        """

        self._check_point_values

        gdf = gpd.GeoDataFrame({"geometry": self.points, "val": self.point_vals})

        fig, ax = plt.subplots()

        gdf.plot(marker="s", ec="None", cmap=cmap, column="val", ax=ax, **kwargs)

        if axis_off:
            plt.axis("off")

        plt.show()

    def plot_map(self, points_crs, dpi=120, cmap="terrain_r", **kwargs):
        """Plot the queried points on map."""

        self._check_point_values

        pts = gpd.GeoDataFrame(geometry=self.points)

        pts.geometry = pts.geometry.rotate(
            self.angle, origin=self.poly.centroid, use_radians=True
        )

        pts = pts.set_crs(points_crs)
        pts = pts.to_crs("EPSG:3857")  # web mercator

        gdf = gpd.GeoDataFrame({"geometry": pts.geometry, "val": self.point_vals})

        # Make a bounding ball for a square map
        rect_poly = self.poly
        rect_poly = gpd.GeoDataFrame(geometry=[rect_poly.centroid])
        rect_poly = rect_poly.set_crs(points_crs)
        rect_poly = rect_poly.geometry.buffer((self.length / 2) * 1.05)
        rect_poly = rect_poly.to_crs("EPSG:3857")

        # Make plot
        fig, ax = plt.subplots(dpi=dpi)
        rect_poly.plot(alpha=0, ax=ax)
        gdf.plot(
            marker=".",
            ec="None",
            cmap=cmap,
            column="val",
            ax=ax,
            **kwargs,
        )
        cx.add_basemap(ax=ax, source=cx.providers.CartoDB.Positron)
        plt.axis("off")
        plt.show()


def make_rectangles(lines, zheads, ztails, relative_buffer=0.1):
    """Generate list of rectangles from line-segments and a buffer.

    Parameters
    ----------
    lines : geopandas.GeoSeries
      Array of line-segments.
    zheads : array-like
      Array of z-coordinates of line-segment heads.
    ztails : array-like
      Array of z-coordinates of line-segment tails.
    relative_buffer : float
      Distance from centerline of to edge of rectangle as function of line-length.

    Returns
    -------
    rectangles : list
      List of proppy.Rectangle-objects.
    """

    lengths = lines.geometry.length

    buffers = lengths * relative_buffer

    angles = angle(lines)

    polygons = makeParallelRectangles(lines.values, angles, buffers)

    consts, slopes = getSlope(lines, angles, zheads, ztails)

    # Form Rectangle-objects
    rectangles = []
    for i, poly in enumerate(polygons):
        R = Rectangle(i, poly, angles[i], consts[i], slopes[i], lengths[i])
        rectangles.append(R)

    return rectangles


def makeLineString(A, B):
    """Make a shapely LineString from two points.

    Parameters
    ----------
    A : shapely.geometry.point.Point
    B : shapely.geometry.point.Point

    Returns
    -------
    linestring : shapely.geometry.linestring.LineString
    """
    return LineString([(A.x, A.y), (B.x, B.y)])


def makeGrid(shape, step):
    """
    Make a uniform array of (x,y)-coordinates over the envelope of ``shape``.

    Works best on axis-parallel rectangles, otherwise there may be points that
    are in the envelope but not in the shape itself. In this case one can
    collecct the points inside the ``shape``  by converting the reurned
    ``pointCoords` to  shapely ``Points`` and use `Points.within(shape)` in
    ``geopandas``.

    Parameters
    ----------
    shape : shapely.Polygon
        A 2D shape whose envelope will be populated by points.

    step : float
        Axis-parallel distance between points in grid

    Returns
    _______
    pointCoords : ndarray
        (grid) of coordinates over envelope of ``shape``.
    """

    minx, miny, maxx, maxy = shape.geometry.envelope.bounds.values[0]

    Xs = np.arange(minx, maxx, step=step)
    Ys = np.arange(miny, maxy, step=step)

    pointCoords = np.array(np.meshgrid(Xs, Ys)).T.reshape(-1, 2)

    return pointCoords


def _angle(xHead, yHead, xTail, yTail):
    """
    The angle of a 2D line going from Head to Tail.

    The inputs are cartesian coordinates.
    """
    if np.any(xHead == xTail):
        # may want to fix this later - should be permitted.
        raise ValueError("Not implemented: segments with equal X-coords.")

    return np.arctan((yTail - yHead) / (xTail - xHead))


def angle(lines):
    """
    Compute the angle of (projection of) line-segment in 2D plain.

    Given a line segment ``[(x1, y1, z1), (x2, y2, z2)]``, compute the angle of
    the projection ``[(x1, y2), (x2, y2)]`` in 2D space.
    Heights (z) are ignored.

    Parameters
    ----------
    lines : `geopandas.geoseries.GeoSeries`
        Should be only `lineString`-objects with exactly 2 points each.

    Returns
    -------
    angles : ndarray
        LineString angles in the (x,y)-plane.

    """
    xHead = np.array([line.boundary.geoms[0].x for line in lines.geometry])
    yHead = np.array([line.boundary.geoms[0].y for line in lines.geometry])
    xTail = np.array([line.boundary.geoms[1].x for line in lines.geometry])
    yTail = np.array([line.boundary.geoms[1].y for line in lines.geometry])

    # compute angle (in y=0 plain)
    angles = _angle(xHead, yHead, xTail, yTail)

    angles[xHead > xTail] += np.pi  # align rotation

    return angles


def makeParallelRectangles(lines, angles, buffer):
    """
    Generate axis-parallel rectangles from line segments.

    Notes
    ------
    The rectangles are generated by first rotating
    each line to be orthogonal to the x-axis. For an axis-aligned line, an
    axis-parallel rectangle is created by buffering the line and taking the
    envelope of the resulting sausage-like shape.

    Parameters
    ----------
    lines : geopandas.array.GeometryArray
        Array of 2D lines (``lineString``) of length ``nLines``.
    angles : np.array
        Array of line angles in radinas.
    buffers : array-like
        Scalar or array of buffer scalars.

    Returns
    -------
    rects : A list of `nLines` orthogonal rectangles.
    """

    # if scalar buffer make array
    if not hasattr(buffer, "__len__"):
        buffer = np.repeat(buffer, len(lines))

    nLines = len(lines)

    lines_parallel = [
        rotate(lines[i], -angles[i], use_radians=True) for i in range(nLines)
    ]

    sausages = [lines_parallel[i].buffer(buffer[i]) for i in range(nLines)]

    rects = [box(*sausages[i].bounds) for i in range(nLines)]

    return rects


def getSlope(lines, angles, zHeads, zTails):
    """
    Compute slopes and constants for a lineSegments.

    The slope and constant refer to the line-segments height, and change
    in height along the segment. This property depends on Z-axis values.

    Parameters
    ----------
    lines : geopandas.geoseries.GeoSeries
        Series of LineStrings of exactly two points (head, tail) each.
    angles : np.array
       Angles by which rotating makes `lines` axis-parallel.
    zHead : array_like
        Array of z-coordinates at the heads of the line segments.
    zTail : array_like
        Array of z-coordinates at the tails of the line segments.

    Returns
    -------
    const : ndarray
        Array of intercepts for lines in (x,z)-plane.
    slope : ndarray
        Array of slopes for in (x,z)-plane.

    """

    nLines = len(lines)

    # get orthogonal lines
    orthLines = [rotate(lines[i], -angles[i], use_radians=True) for i in range(nLines)]

    # get slope
    rise = zTails - zHeads
    run = lines.length
    if any(run == 0):
        raise ValueError("Input `lines` must have positive length.")
    slope = rise / run

    # get const s.t. zHeads = const + slope * xHeads
    xHeads = [line.coords[0][0] for line in orthLines]
    const = zHeads - slope * xHeads

    return const, slope


def populateRectangle(rectangle, nCols, nRows, decimals=6):
    """
    Populate an x-axis parallel rectangle with a grid of points.

    Parameters
    ----------
    rectangle : Rectangle object
        A rectanlge, or other polygon.
    nCols : number of columns, int
        The number points on x-axis of point grid.
    nRows : number of rows, int
        The number of points o y-axis of point grid.
    decimals : number of decimals in point coordinates
        Smaller decimals get rounded, defaults to 6.
    """

    minx, miny, maxx, maxy = rectangle.poly.bounds

    # make grid of points
    points = []
    for x in np.linspace(minx, maxx, nCols):
        for y in np.linspace(miny, maxy, nRows):
            points.append(Point((round(x, decimals), round(y, decimals))))

    return points


def queryRaster(points, rectangle, angle, raster):
    """
    Query ``raster`` at given ``points`` belonging to ``rectanlge`` with ``angle``.
    The ``points`` and ``raster`` should be in the same crs.

    Parameters
    ----------
    points : list
        List of coordinates of (grid of) points over rectangle.
    rectangle : shapely.geometry
        A single rectangle defining the extent of points
    angle : float
        Angle by which rotating rectanlge (anticlockwise) makes it axis parallel.
    raster : rasterio raster
        A raster to sample at points.

    Returns
    -------
    values : ``np.array`` of ``raster``-values at ``points``.

    """

    pts = gpd.GeoDataFrame(geometry=points)

    # rotate to correct format
    pts.geometry = pts.geometry.rotate(
        angle, origin=rectangle.centroid, use_radians=True
    )

    coord_list = [(x, y) for x, y in zip(pts["geometry"].x, pts["geometry"].y)]

    pts["values"] = [x[0] for x in raster.sample(coord_list)]

    return pts["values"].values


def rasterValues(rectangle, nrows, ncols, rasterfile):
    """Form (nrows x ncols) grid over rectangle and query raster."""

    raster = rio.open(rasterfile)

    points = populateRectangle(rectangle, ncols, nrows)

    vals = queryRaster(points, rectangle.poly, rectangle.angle, raster)

    return points, vals


def normalizedRasterValues(rectangle, nrows, ncols, rasterfile):
    """Form (nrwos x ncols) grid over rectangle and query distance to Los-plance."""

    points, vals = rasterValues(rectangle, nrows, ncols, rasterfile)

    return {
        "id": rectangle.id,
        "points": points,
        "vals": rectangle.normalize_raster_values(points, vals),
    }


def save_raster_values(rectangle, nrows, ncols, rasterfile, savedir, fmt="%.2e"):
    """Query distance to LoS place and save file as array."""

    out = normalizedRasterValues(rectangle, nrows, ncols, rasterfile)

    arr = out["vals"].reshape((ncols, nrows)).T

    np.savetxt(f"{savedir}/{out['id']}.csv", arr, delimiter=",", fmt=fmt)


def queryMeanObstruction(rectangle, nRows, distPerCol, rasterfile, fillna=99999):
    """
    Compute mean obstruction of Rectangles-object for given raster.

    Parameters
    ----------
    rectangle : Rectanlges-object
        Object encoding a collection of rectangles for LoS queries.
    nRows : int
        Number of rows of grid points to query the raster with.
    distPerCol : int
        Numbor of distance units for each column of grid points.
    rasterfile: str
        Filename of raster.
    fillna : float
        Value to replace missing elevation numbers with.

    Notes
    -----
    This method compares a rectangle with a rasterized 3D surface model.
    It approximates the fraction of the rectangle's area tha lies below the
    surface model. The rectanlge is tilted in the 3rd dimension to allow
    inclines. Setting `nRows` to `1` reduces the rectangles to
    line-segments. In this case the tool is essentially a LoS-query.
    """

    nCols = int(rectangle.length // distPerCol) + 1

    # read raster from file if not already read
    raster = rio.open(rasterfile)

    # populate rectangle with points
    pts = populateRectangle(rectangle.poly, nCols, nRows)
    pts = gpd.GeoDataFrame(geometry=pts)

    # sample raster values at points
    pts["rasterVal"] = queryRaster(
        pts.geometry, rectangle.poly, rectangle.angle, raster
    )

    # impute missing data - occurs e.g. when out of bounds
    pts.loc[pts["rasterVal"] > 3.0e38, "rasterVal"] = fillna

    # get rectangle values at points
    linkConst = rectangle.const
    linkSlope = rectangle.slope
    pts["x"] = np.array([p.x for p in pts.geometry])
    pts["pointVal"] = linkConst + linkSlope * pts["x"]

    # get distance from ground
    pts["diff"] = pts["pointVal"] - pts["rasterVal"]
    pts["under"] = pts["diff"] < 0

    return rectangle.id, pts["under"].mean()

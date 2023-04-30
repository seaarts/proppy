"""
========
Segments
========

Associationg geographic variables with line-segments from raster files.


This package is used to associate 3-dimensional line segments with variables
from raster images, such as digital elevation or surface models. A simple
example querying whether two points in space have line of sight. This is
equivalent to querying wether the line segment connecting the two points
intersects the terrain. The `Segments`-package is designed to run such queries.
It also enables the querying of richer data for line-segments.
"""

import geopandas as gpd
import numpy as np
import rasterio as rio
import shapely
from shapely.affinity import rotate
from shapely.geometry import LineString, Point, Polygon, box, mapping


class Rectangle:
    """A  rectangle for geometry queries.

    The `Rectangle`-object encodes a rectangle for making queries on a raster.
    Its main use is to be populated by a grid of points whose values at on a
    raster are queried.

    Attributes
    ----------
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
    Make a uniform array of (x,y)-coordinates over the envelope of `shape`.

    Works best on axis-parallel rectangles.

    Parameters
    ----------
    shape : shapely.Polygon
        A 2D shape whose envelope will be populated by points.
        To get only points inside `shape` one can convert
        `pointCoords` to `Points` and use `Points.within(shape)`.
    step : float
        Axis-parallel distance between points in grid

    Returns
    _______
    pointCoords : ndarray
        (grid) of coordinates over envelope of `shape`.
    """

    minx, miny, maxx, maxy = shape.geometry.envelope.bounds.values[0]

    Xs = np.arange(minx, maxx, step=step)
    Ys = np.arange(miny, maxy, step=step)

    pointCoords = np.array(np.meshgrid(Xs, Ys)).T.reshape(-1, 2)

    return pointCoords


def cornerCoords(geometry):
    """
    Extract the corner coordinates of a `shapely.geometry`.

    This function covers two cases:  `MultiPolygon` and `Polygon`.

    Parameters
    ----------
    geometry : shapely.geometry
        A polygon or multiPolygon.

    Returns
    -------
    corners : list
        A list of [x, y] coordinate lists corresponding to
        every point in the input `geometry`.
    """

    corners = []

    # loop over geometries `geom` if `MultiPolygon`
    if isinstance(geometry, shapely.geometry.multipolygon.MultiPolygon):
        for geom in geometry.boundary.geoms:
            coords = np.vstack(geom.coords).tolist()
            for c in coords:
                corners.append(c)
    else:
        # loop over coords only if `Polygon`
        coords = np.vstack(geometry.boundary.coords).tolist()
        for c in coords:
            corners.append(c)

    return corners


def _angle(xHead, yHead, xTail, yTail):
    """
    The angle of a 2D line going from Head to Tail.

    The inputs are cartesian coordinates.
    """
    if np.any(xHead == xTail):
        # may want to fix this later - should be permitted.
        raise ValueError("A line cannot have equal x-coordinates")

    return np.arctan((yTail - yHead) / (xTail - xHead))


def angle(lines):
    """
    Compute angle of 2D projcetion of line-segment in 3D.

    Given a line segment `[(x1, y1, z1), (x2, y2, z2)]`, compute the angle of
    the line passing through `(x1, y2), (x2, y2)` in 2D space.

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

    # compute angle (in ground plain)
    angles = _angle(xHead, yHead, xTail, yTail)
    angles[xHead > xTail] += np.pi  # align rotation

    return angles


def makeParallelRectangles(lines, angles, buffer):
    """
    Generate axis-parallel rectangles from general line segments.

    Notes
    ------
    This is exclusively 2D. The rectangles are generated by first rotating
    each line to be orthogonal to the x-axis. For an axis-aligned line, an
    axis-parallel rectangle is created by buffering the line and taking the
    envelope of the resulting sausage-shape.

    Parameters
    ----------
    lines : `geopandas.array.GeometryArray` of 2D lines (`lineString`s).
        Assume the length of the array is nLines
    angles : np.array of line angles in radias.
    buffers : array-like of buffers

    Returns
    -------
    rects : A list of `nLines` orthogonal rectangles.
    """

    # if scalar buffer make array
    if not hasattr(buffer, "__len__"):
        buffer = np.repeat(buffer, len(lines))

    nLines = len(lines)

    # rotate lines to be horizontal
    rects = [rotate(lines[i], -angles[i], use_radians=True) for i in range(nLines)]

    # create buffer around lines - produces "sausages"
    rects = [rects[i].buffer(buffer[i]) for i in range(nLines)]

    # make "sausages" into rectangles via bounds
    rects = [box(*rects[i].bounds) for i in range(nLines)]

    return rects


def getSlope(lines, angles, zHeads, zTails):
    """
    Compute slopes and constants for a lineSegments.

    This is used to evaluate Line of Sight (LoS) planes along
    wireless links. By comparing the LoS plane with terrain
    features along a link one can understand the severity of
    physical obstructions to the wireless signal.

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
    _______
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
    rectangle : shapely.geometry.polygon.Polygon
        A rectanlge, or other polygon.
    nCols : number of columns, int
        The number points on x-axis of point grid.
    nRows : number of rows, int
        The number of points o y-axis of point grid.
    decimals : number of decimals in point coordinates
        Smaller decimals get rounded, defaults to 6.
    """

    minx, miny, maxx, maxy = rectangle.bounds

    # make grid of points
    points = []
    for x in np.linspace(minx, maxx, nCols):
        for y in np.linspace(miny, maxy, nRows):
            points.append(Point((round(x, decimals), round(y, decimals))))

    return points


def queryRaster(points, rectangle, angle, raster):
    """
    Query `raster` at given `points` belonging to `rectanlge` with `angle`.
    The `points` and `raster` should be in the same crs.

    Parameters
    ----------
    points : list
        List of coordinates of (grid of) points over rectangle.
    rectangle : shapely.geomeyry
        A single rectangle defining the extent of points
    angle : float
        Angle by which rotating rectanlge (anticlockwise) makes it axis parallel.
    raster : rasterio raster
        A raster to sample at points.

    Returns
    -------
    values : `np.array` of `raster`-values at `points`.

    """

    pts = gpd.GeoDataFrame(geometry=points)

    # rotate to correct format
    pts.geometry = pts.geometry.rotate(
        angle, origin=rectangle.centroid, use_radians=True
    )

    coord_list = [(x, y) for x, y in zip(pts["geometry"].x, pts["geometry"].y)]

    pts["values"] = [x[0] for x in raster.sample(coord_list)]

    return pts["values"].values

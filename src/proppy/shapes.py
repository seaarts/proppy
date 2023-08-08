"""
proppy.shapes

This module is used to associate variables with line-segments using shapefules.
"""


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

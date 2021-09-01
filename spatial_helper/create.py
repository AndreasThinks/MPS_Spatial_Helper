import geopandas
from h3 import h3
from shapely.geometry import Polygon
import pandas as pd


def h3_from_boundary(boundary, resolution, buffer=0):
    """given a spatial polygon, returns a h3 hex grid at the given resolution for the same area with an
    optional buffer in degrees """

    boundary["city"] = "all"
    buffered = boundary.copy()
    buffered = buffered.to_crs("EPSG:4326")
    lon_buffer = buffered.dissolve(by="city")
    lon_buffer["geometry"] = lon_buffer["geometry"].buffer(buffer)

    hexs = h3.polyfill(buffered.iloc[0]["geometry"].__geo_interface__, resolution, geo_json_conformant=True)

    polygonise = lambda hex_id: Polygon(
        h3.h3_to_geo_boundary(
            hex_id, geo_json=True)
    )

    all_polys = geopandas.GeoSeries(list(map(polygonise, hexs)),
                                    index=hexs
                                    )
    london_hex = geopandas.GeoDataFrame(data=all_polys, columns=["geometry"]).reset_index().rename(
        columns={"index": "h3_ref"})
    return london_hex


def h3_from_coordinates(resolution, size, x=0, y=0, crs_type="osgb"):
    """takes a H3 resolution and grid size, and generates an appropriate H3 hex grid as a geodataframe. Will default
    to an OSGB CRS at coordinate 0,0, but can be given any option or convert to lat_lon by setting crs_type to
    'lat_lon' """

    df = pd.DataFrame(index=[0], data={"city": "all", "y": y, "x": x})
    london = geopandas.GeoDataFrame(
        df, geometry=geopandas.points_from_xy(df.y, df.x))
    if crs_type == "osgb":
        london = london.set_crs("EPSG:27700")
    elif crs_type == "lat_lon":
        london = london.set_crs("EPSG:4326")
    else:
        raise ValueError("Inccorect CRS code - please chose osgb or lat_lon")

    london_buffered = london.copy()
    london_buffered["geometry"] = london["geometry"].buffer(size)


    buffered = london_buffered.copy()
    if crs_type == "osgb":
        buffered = buffered.to_crs("EPSG:4326")
    lon_buffer = buffered.dissolve(by="city")

    hexs = h3.polyfill(lon_buffer.iloc[0]["geometry"].__geo_interface__, resolution, geo_json_conformant=True)

    polygonise = lambda hex_id: Polygon(
        h3.h3_to_geo_boundary(
            hex_id, geo_json=True)
    )
    all_polys = geopandas.GeoSeries(list(map(polygonise, hexs)),
                                    index=hexs
                                    )
    london_hex = geopandas.GeoDataFrame(data=all_polys, columns=["geometry"]).reset_index().rename(
        columns={"index": "h3_ref"})

    london_hex = london_hex.set_crs("EPSG:4326")
    if crs_type == "osgb":
        london_hex = london_hex.to_crs("EPSG:27700")

    return london_hex

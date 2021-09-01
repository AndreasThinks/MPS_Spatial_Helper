import geopandas
from h3 import h3
from shapely.geometry import Polygon


def make_h3_grid(boundary, resolution, buffer=0):
    """given a spatial object boundary, returns a h3 hex grid at the given resolution for the same area with an
    optional buffer in degrees """

    lon_buffer_zone = boundary.copy()
    lon_buffer_zone["city"] = "all"
    lon_buffer_zone["geometry"] = boundary["geometry"].buffer(buffer)
    lon_buffer_zone = lon_buffer_zone.to_crs("EPSG:4326")
    lon_buffer = lon_buffer_zone.dissolve(by="city")
    hexs = h3.polyfill(lon_buffer.geometry[0].__geo_interface__, resolution, geo_json_conformant=True)

    polygonise = lambda hex_id: Polygon(
        h3.h3_to_geo_boundary(
            hex_id, geo_json=True)
    )

    all_polys = geopandas.GeoSeries(list(map(polygonise, hexs)),
                                    index=hexs,
                                    crs="EPSG:4326"
                                    )
    london_hex = geopandas.GeoDataFrame(data=all_polys, columns=["geometry"]).reset_index().rename(
        columns={"index": "h3_ref"})
    return london_hex

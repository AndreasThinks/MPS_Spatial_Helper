import folium
import geopandas


def generate_map(geoframe, category, key, top_count=50, tileset='CartoDB positron'):
    """takes a geoframe coded to lat-long, a category to score by, and optionally a number of hexes to display,
    and produces an interactive map """

    # Create interactive map with default basemap
    map_osm = folium.Map(location=[51.5074, 0.1278], tiles=tileset)

    heat = folium.Choropleth(
        geo_data=geoframe[[key, "geometry", category]].sort_values(by=category, ascending=False).iloc[0:top_count],
        name='Custom Map',
        data=geoframe,
        columns=[key, category],
        fill_color="BuPu",
        key_on="feature.properties." + str(key)
    )
    map_osm.add_child(heat)

    style_function = lambda x: {'fillColor': '#ffffff',
                                'color': '#000000',
                                'fillOpacity': 0.1,
                                'weight': 0.1}
    highlight_function = lambda x: {'fillColor': '#000000',
                                    'color': '#000000',
                                    'fillOpacity': 0.50,
                                    'weight': 0.1}
    nil = folium.features.GeoJson(
        geoframe[[key, "geometry", category]].sort_values(by=category, ascending=False).iloc[0:top_count],
        style_function=style_function,
        control=False,
        highlight_function=highlight_function,
        tooltip=folium.features.GeoJsonTooltip(
            fields=[key, category],
            aliases=['CAD Grid Ref: ', 'Score'],
            style="background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"
        )
    )
    map_osm.add_child(nil)
    map_osm.keep_in_front(nil)
    folium.LayerControl().add_to(map_osm)

    return map_osm


def generate_cust_map(geoframe, category, key, top_count=50, values_to_show=[], tileset='CartoDB positron'):
    """takes a geoframe coded to lat-long, a category to score by, an optional list of dispays and other values to
    highlight on tooltip, and produces an interactive map """

    # Create interactive map with default basemap
    map_osm = folium.Map(location=[51.5074, 0.1278], tiles=tileset)

    heat = folium.Choropleth(
        geo_data=geoframe[[key, "geometry", category]].sort_values(by=category, ascending=False).iloc[0:top_count],
        name='Custom Map',
        data=geoframe,
        columns=[key, category],
        fill_color="BuPu",
        key_on="feature.properties." + str(key)
    )
    map_osm.add_child(heat)

    style_function = lambda x: {'fillColor': '#ffffff',
                                'color': '#000000',
                                'fillOpacity': 0.1,
                                'weight': 0.1}
    highlight_function = lambda x: {'fillColor': '#000000',
                                    'color': '#000000',
                                    'fillOpacity': 0.50,
                                    'weight': 0.1}
    nil = folium.features.GeoJson(
        geoframe[[key, "geometry", category] + values_to_show].sort_values(by=category, ascending=False).iloc[
        0:top_count],
        style_function=style_function,
        control=False,
        highlight_function=highlight_function,
        tooltip=folium.features.GeoJsonTooltip(
            fields=[key, category] + values_to_show,
            aliases=['Ref', 'Score'] + values_to_show,
            style="background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"
        )
    )
    map_osm.add_child(nil)
    map_osm.keep_in_front(nil)
    folium.LayerControl().add_to(map_osm)

    return map_osm


def make_bcu_map(wards, hexes, geodata, bcu_name, tileset='CartoDB positron'):
    """given a set of wards, hex data, and a geodata output, and a bcu name, returns a map of the BCU and a csv of
    the table with ward data """

    bcu_map = geodata[(geodata["Previous entries"] < 2) & (geodata["BCU_Name"] == bcu_name)].reset_index().rename(
        columns={"index": "Rank"})
    geomap = bcu_map.merge(hexes, how="left", left_on="h3_ref", right_on="h3_ref").drop_duplicates()
    geomap["Rank"] = geomap["Rank"] + 1
    geomap = geopandas.GeoDataFrame(
        geomap[["Rank", "h3_ref", "BCU_Name", "t_centre_name", "Final_score", "geometry"]].dropna(axis=0).copy())
    map_osm = folium.Map(location=[51.5074, 0.1278], tiles=tileset)
    heat = folium.Choropleth(
        geo_data=geomap,
        name=bcu_name,
        data=geomap,
        columns=["h3_ref", "Final_score"],
        fill_color="BuPu",
        key_on="feature.properties.h3_ref")

    map_osm.add_child(heat)

    style_function = lambda x: {'fillColor': '#ffffff',
                                'color': '#000000',
                                'fillOpacity': 0.1,
                                'weight': 0.1}
    highlight_function = lambda x: {'fillColor': '#000000',
                                    'color': '#000000',
                                    'fillOpacity': 0.50,
                                    'weight': 0.1}
    nil = folium.features.GeoJson(
        geomap[["h3_ref", "geometry", "t_centre_name", "Final_score"]],
        style_function=style_function,
        control=False,
        highlight_function=highlight_function,
        tooltip=folium.features.GeoJsonTooltip(
            fields=["h3_ref", "t_centre_name", "Final_score"],
            aliases=['Grid Ref', "Town Centre", 'Score'],
            style="background-color: white; color: #333333; font-family: arial; font-size: 12px; padding: 10px;"
        )
    )
    map_osm.add_child(nil)
    map_osm.keep_in_front(nil)
    folium.LayerControl().add_to(map_osm)
    map_osm.save("../data/map_output/" + bcu_name + "_map.html")
    hex_with_ward = geopandas.sjoin(geomap, wards, how="left", op='intersects')
    hex_with_ward.to_csv("../data/map_output/" + bcu_name + "_map.csv")

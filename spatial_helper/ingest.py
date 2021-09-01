import os
import geopandas
import pandas as pd


def calc_cchi(lon_hex, crime_file, cchi_lookup, minor_class):
    """calculcates CCCHI from an individual CRIS file"""

    if lon_hex.crs != crime_file.crs:
        crime_file = crime_file.set_crs(lon_hex.crs, allow_override=True)
    crime_per_grid = geopandas.sjoin(crime_file, lon_hex, how="left", op='within').drop_duplicates()
    crime_hex_cnt = crime_per_grid[["h3_ref", "CRNumber"]].groupby("h3_ref").count().reset_index()
    lon_count = lon_hex.merge(crime_hex_cnt, how="left", on="h3_ref").fillna(0)
    lon_count["CCHI_score"] = lon_count["CRNumber"] * float(
        cchi_lookup.loc[cchi_lookup["cris_minor"] == minor_class, "CrimeHarm"])
    print(lon_count["CCHI_score"].sum())
    return lon_count[["h3_ref", "CCHI_score"]].fillna(0)


def os_poi_to_hex(os_items, hexes):
    """takes a hex grid and an OS file and retuyrns a count per grid"""

    if os_items.crs != hexes.crs:
        os_items = os_items.to_crs(hexes.crs)
    block_with_hex = geopandas.sjoin(os_items, hexes, how="left", op='within')
    return block_with_hex[["h3_ref", "UNIQUE_REFERENCE_NUMBER"]].groupby(["h3_ref"]).count().reset_index()


def osm_feat_to_hex(osm_items, grid, osm_type, category="type"):
    """takes a list of OSM items, a grid, a type of item and optionally a key to filter by, and returns the grid by
    h3 """

    if osm_items.crs != grid.crs:
        osm_items = osm_items.to_crs(grid.crs)
    subset = osm_items[osm_items[category] == osm_type].copy()
    block_with_hex = geopandas.sjoin(subset, grid, how="left", op='within')
    return block_with_hex[["h3_ref", "osm_id"]].groupby(["h3_ref"]).count().reset_index()


def bcu_to_grid(bcu_borders, grid):
    """takes BCU borders and a grid, and assigns them fairly"""

    grid_with_borough = geopandas.sjoin(grid, bcu_borders, op='intersects')
    grid_bcu_cnt = grid_with_borough[["CAD_Ref", "BCU_Code"]].groupby(["CAD_Ref"]).count().sort_values(
        by=["BCU_Code"]).reset_index()
    more_than_bcu = grid_bcu_cnt[grid_bcu_cnt["BCU_Code"] > 1]["CAD_Ref"].unique()
    all_cads = grid_bcu_cnt["CAD_Ref"].unique()
    corrects_cad_cnt = [x for x in all_cads if x not in more_than_bcu]
    correct = grid_with_borough[grid_with_borough["CAD_Ref"].isin(corrects_cad_cnt)].copy()
    wrong = grid_with_borough[grid_with_borough["CAD_Ref"].isin(more_than_bcu)].copy()
    fixed = wrong.sample(frac=1, random_state=42).drop_duplicates(subset="CAD_Ref").copy()
    all_cads_with_bcu = pd.concat([correct, fixed], axis=0)
    all_cads_with_bcu = all_cads_with_bcu.sort_index()
    return all_cads_with_bcu


def overlap_to_grid(new_borders, identifier, grid, g_identifier):
    """takes a set of borders, an identifier per object like an LSOA or CAD ID,  and a grid, and an identifier for
    that, and assigns the border items to teh grid """

    grid_with_borough = geopandas.sjoin(grid, new_borders, op='intersects')
    grid_bcu_cnt = grid_with_borough[[g_identifier, identifier]].groupby([g_identifier]).count().sort_values(
        by=[identifier]).reset_index()
    more_than_bcu = grid_bcu_cnt[grid_bcu_cnt[identifier] > 1][g_identifier].unique()
    all_cads = grid_bcu_cnt[g_identifier].unique()
    corrects_cad_cnt = [x for x in all_cads if x not in more_than_bcu]
    correct = grid_with_borough[grid_with_borough[g_identifier].isin(corrects_cad_cnt)].copy()
    wrong = grid_with_borough[grid_with_borough[g_identifier].isin(more_than_bcu)].copy()
    fixed = wrong.sample(frac=1, random_state=42).drop_duplicates(subset=g_identifier).copy()
    all_cads_with_bcu = pd.concat([correct, fixed], axis=0)
    all_cads_with_bcu = all_cads_with_bcu.sort_index()
    return all_cads_with_bcu


def crime_cad_grid(crime_df, grid, grid_ref, major_class):
    """takes a crime df and a grid, grid reference column, and returns a count, median and mean per grid"""

    if crime_df.crs != grid.crs:
        crime_df = crime_df.set_crs(grid.crs, allow_override=True)
    if "index_right" in crime_df.columns.to_list():
        crime_df = crime_df.drop(["index_right"], axis=1).copy()
    grid.rename(columns={grid_ref: "CAD_Ref"}, inplace=True)
    crime_per_grid = geopandas.sjoin(crime_df, grid, how="left", op='within').drop_duplicates()
    crime_per_grid["hour"] = crime_per_grid["SUPV_CR_Recorded_Date"].str.slice(8, 10).astype("int")
    crime_grid_median = crime_per_grid[["CAD_Ref", "CRNumber", "hour"]].groupby("CAD_Ref").agg(
        {'CRNumber': ['count'], 'hour': ['mean', 'median']}).reset_index().rename(
        columns={"index_right": "CAD_count"}).copy()
    crime_grid_median.columns = ["CAD_Ref", "count", "mean_hr", "median_hr"]
    crime_count_geo = grid.merge(crime_grid_median, how="left", left_on="CAD_Ref", right_on="CAD_Ref")
    crime_count_geo[["CAD_Ref", "count", "mean_hr", "median_hr"]] = crime_count_geo[
        ["CAD_Ref", "count", "mean_hr", "median_hr"]].fillna(0)
    crime_count_geo = crime_count_geo.rename(
        columns={"count": major_class + "_count", "mean_hr": major_class + "_mean_hr",
                 "median_hr": major_class + "_median_hr"})
    crime_count_geo.rename(columns={"CAD_Ref": grid_ref}, inplace=True)
    return crime_count_geo


def cad_to_grid(grid, grid_ref, cads):
    """takes a geofile of grids, an index column name, and a grid and returns a count, median and mean per grid"""

    if cads.crs != grid.crs:
        cads = cads.set_crs(grid.crs, allow_override=True)
    if "index_right" in cads.columns.to_list():
        cads = cads.drop(["index_right"], axis=1).copy()
    if "index_left" in cads.columns.to_list():
        cads = cads.drop(["index_left"], axis=1).copy()
    grid.rename(columns={grid_ref: "CAD_Ref"}, inplace=True)
    cad_per_grid = geopandas.sjoin(cads, grid, how="left", op='within').drop_duplicates()
    cad_per_grid["hour"] = cad_per_grid["IncidentTime"].str.slice(0, 2).astype("int")
    cad_grid_median = cad_per_grid[["CAD_Ref", "IncidentNumber", "hour"]].groupby("CAD_Ref").agg(
        {'IncidentNumber': ['count'], 'hour': ['mean', 'median']}).reset_index().rename(
        columns={"index_right": "CAD_count"}).copy()
    cad_grid_median.columns = ["CAD_Ref", "count", "mean_hr", "median_hr"]
    cad_count_geo = grid.merge(cad_grid_median, how="left", left_on="CAD_Ref", right_on="CAD_Ref")
    cad_count_geo[["CAD_Ref", "count", "mean_hr", "median_hr"]] = cad_count_geo[
        ["CAD_Ref", "count", "mean_hr", "median_hr"]].fillna(0)
    cad_count_geo.rename(columns={"CAD_Ref": grid_ref}, inplace=True)
    return cad_count_geo


def cad_to_grid_time(grid, grid_ref, cads, time="day"):
    """takes a geofile of grids, an index column name, and a grid and returns a count, as well as a time of day (
    0600-1900) or night. """

    if cads.crs != grid.crs:
        cads = cads.set_crs(grid.crs, allow_override=True)
    if "index_right" in cads.columns.to_list():
        cads = cads.drop(["index_right"], axis=1).copy()
    if "index_left" in cads.columns.to_list():
        cads = cads.drop(["index_left"], axis=1).copy()
    grid.rename(columns={grid_ref: "CAD_Ref"}, inplace=True)
    cads["hour"] = cads["IncidentTime"].str.slice(0, 2).astype("int")
    print(cads.shape[0])
    if time == "day":
        cads = cads[(cads["hour"] <= 19) & (cads["hour"] >= 6)].copy()
    if time == "night":
        cads = cads[(cads["hour"] > 19) & (cads["hour"] < 6)].copy()
    print(cads.shape[0])
    cad_per_grid = geopandas.sjoin(cads, grid, how="left", op='within').drop_duplicates()
    cad_count = cad_per_grid[["CAD_Ref", "IncidentNumber"]].groupby("CAD_Ref").count().rename(
        columns={"IncidentNumber": time + "_count"}).copy()
    cad_count_geo = grid.merge(cad_count, how="left", left_on="CAD_Ref", right_on="CAD_Ref")
    cad_count_geo[time + "_count"] = cad_count_geo[time + "_count"].fillna(0)
    return cad_count_geo


def cad_to_grid_cats(grid, grid_ref, cads):
    """takes a  geofile , index column,  and returns a count, median and mean per grid"""

    if cads.crs != grid.crs:
        cads = cads.set_crs(grid.crs, allow_override=True)
    if "index_right" in cads.columns.to_list():
        cads = cads.drop(["index_right"], axis=1).copy()
    if "index_left" in cads.columns.to_list():
        cads = cads.drop(["index_left"], axis=1).copy()
    grid.rename(columns={grid_ref: "CAD_Ref"}, inplace=True)
    code_list = {"Police Generated Res": "_violence", "ASB Nuisance": "_asb_nuisance", "Violence Against The": "_VAP"}
    for key in code_list:
        cads = cads[cads["OpeningCode_Description"] == key].copy()
        cad_per_grid = geopandas.sjoin(cads, grid, how="left", op='within').drop_duplicates()
        cad_per_grid["hour"] = cad_per_grid["IncidentTime"].str.slice(0, 2).astype("int")
        cad_grid_median = cad_per_grid[["CAD_Ref", "IncidentNumber", "hour"]].groupby("CAD_Ref").agg(
            {'IncidentNumber': ['count'], 'hour': ['mean', 'median']}).reset_index().rename(
            columns={"index_right": "CAD_count"}).copy()
        cad_grid_median.columns = ["CAD_Ref", "count", "mean_hr", "median_hr"]
        cad_count_geo = grid.merge(cad_grid_median, how="left", left_on="CAD_Ref", right_on="CAD_Ref")
        cad_count_geo[["CAD_Ref", "count", "mean_hr", "median_hr"]] = cad_count_geo[
            ["CAD_Ref", "count", "mean_hr", "median_hr"]].fillna(0).rename(
            columns={"count": "count" + code_list[key], "mean_hr": "mean_hr" + code_list[key],
                     "median_hr": "median_hr" + code_list[key]})
        cad_count_geo.rename(columns={"CAD_Ref": grid_ref}, inplace=True)
        return cad_count_geo


def agg_cad_directory(directory, grid, grid_ref, exclude_shout=True):
    """takes all cads in a directory, aggregates and returns a list of grids, and checks wheter you want to exclude
    op shout """

    if exclude_shout:
        print("Op Shout Excluded, True")
    all_borough = []
    for filename in os.listdir(directory):
        if filename.endswith(".tab"):
            print("Processing file " + filename)
            filename = geopandas.read_file(directory + "\\" + filename, crs="EPSG:27700")
            if exclude_shout:
                filename = filename[~((filename["X"] == 523769) & (filename["Y"] == 180824) & (
                        filename["OpeningCode_Description"] == "Concern For Safety"))].copy()
            all_borough.append(filename)
        else:
            continue
    all_borough_cads = pd.concat(all_borough, axis=0, ignore_index=True)
    all_cads = cad_to_grid(grid, grid_ref, all_borough_cads)
    return all_cads


def agg_cad_directory_time(directory, grid, grid_ref, exclude_shout=True):
    """takes all cads in a directory, aggregates and returns a list of grids v3, an optionally a function,
    as well as exclude op shout """

    all_borough = []
    if exclude_shout:
        print("Op Shout Excluded, True")
    for filename in os.listdir(directory):
        if filename.endswith(".tab"):
            print("Processing file " + filename)
            filename = geopandas.read_file(directory + "\\" + filename, crs="EPSG:27700")
            if exclude_shout:
                filename = filename[~((filename["X"] == 523769) & (filename["Y"] == 180824) & (
                        filename["OpeningCode_Description"] == "Concern For Safety"))].copy()
            all_borough.append(filename)
        else:
            continue
    all_borough_cads = pd.concat(all_borough, axis=0, ignore_index=True)
    all_cads = cad_to_grid_time(grid, grid_ref, all_borough_cads)
    return all_cads


def agg_cad_code_directory(directory, theme, suffix, grid, grid_ref):
    """takes all cads in a directory, an opening code and a column name suffix, aggregates and returns a list of
    grids v3 """

    all_borough = []
    for filename in os.listdir(directory):
        if filename.endswith(".tab"):
            filename = geopandas.read_file(directory + "\\" + filename, crs="EPSG:27700")
            filename = filename[filename["OpeningCode_Description"] == theme].copy()
            all_borough.append(filename)
        else:
            continue
    all_borough_cads = pd.concat(all_borough, axis=0, ignore_index=True)
    all_cads = cad_to_grid(grid, grid_ref, all_borough_cads).rename(
        columns={"count": "count" + "_" + suffix, "mean_hr": "mean_hr" + "_" + suffix,
                 "median_hr": "median_hr" + "_" + suffix})
    return all_cads


def agg_cris_directory(directory, grid, grid_ref):
    crime_names = []
    for filename in os.listdir(directory):
        if filename.endswith(".tab"):
            major_name = filename.split("_")[0].replace(" ", "")
            if major_name not in crime_names:
                crime_names.append(major_name)
    all_crimes = []
    for name in crime_names:
        print(name)
        all_borough = []
        for filename in os.listdir(directory):
            if filename.endswith(".tab"):
                major_name = filename.split("_")[0].replace(" ", "")
                if major_name == name:
                    all_borough.append(geopandas.read_file(directory + "\\" + filename, crs="EPSG:27700"))
        all_borough_cads = pd.concat(all_borough, axis=0, ignore_index=True)
        all_crimes.append(crime_cad_grid(all_borough_cads, grid, grid_ref, name).iloc[:, -3:])
    all_things = pd.concat(all_crimes, axis=1)
    return all_things

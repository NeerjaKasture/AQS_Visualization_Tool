from simplekml import Kml

def dataframe_to_kml(df, lon_col="longitude", lat_col="latitude", name_col=None):
    """
    Convert a dataframe with lon/lat columns into a KML string.
    """
    kml = Kml()

    for i, row in df.iterrows():
        name = str(row[name_col]) if name_col else f"Sensor {i+1}"
        kml.newpoint(
            name=name,
            coords=[(row[lon_col], row[lat_col])]
        )

    return kml.kml()

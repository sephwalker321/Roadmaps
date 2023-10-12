import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.colors import Normalize as Norm
from matplotlib.colors import LinearSegmentedColormap

import numpy as np
import pandas as pd

from pyproj import CRS
import utm

from roadmaps.load import Generate_Config
from roadmaps import functions

def get_distance(
        df_day, 
        config = Generate_Config(),
    ):
    """ 
    Calculate the distance traveled for linestring geometries and append to dataframe. 
    DISUSED in favour of google maps distances.
    
    Parameters
    ----------
        df_day: Geopandas dataframe
            Road journeys for given date
        config: class
            class of configuration settings instance

    Returns
    -------
        df_day: Geopandas dataframe
            Road journeys for given date

    """
    lats = []
    longs = []
    for Linestring in df_day["geometry"].values:
        x,y = Linestring.xy
        lats += y
        longs += x

    lat_mean = np.nanmean(np.array(lats))
    longs_mean = np.nanmean(np.array(longs))

    utm_crs = CRS.from_dict(dict(
            proj = 'utm',
            zone = utm.latlon_to_zone_number(lat_mean, longs_mean),
            south = lat_mean < 0
        )
    )
    return df_day.geometry.to_crs(utm_crs).length / functions.convert_distance(config.distance_unit)

def restrict_plot(
        place,
        config = Generate_Config(),
    ):
    """ 
    Determine the x-limits, y-limits and resolution of open source maps.
    
    Parameters
    ----------
        place: str 
            placename. ["canada", "uk", "usa", "world"]
        config: class
            class of configuration settings instance

    Returns
    -------
        xlim: np.array
            x-axis plot limits (Long)
        ylim: np.array
            y-axis plot limits (Lat)
        resolution: float
            map resolution for open source base map download

    """
    if place in config.plot_bounding_box.keys():
        resolution = config.plot_bounding_box[place]["resolution"] 

        if config.plot_bounding_box[place]["width"] != -1:
            long_mid = config.plot_bounding_box[place]["long_mid"] 
            lat_mid = config.plot_bounding_box[place]["lat_mid"] 
            width = config.plot_bounding_box[place]["width"] 
            xlim = [long_mid - width/2,long_mid + width/2]
            ylim = [lat_mid - width/2,lat_mid + width/2]
            return np.array(xlim), np.array(ylim), resolution
        elif config.plot_bounding_box[place]["long_range"] != -1:
            long_range = config.plot_bounding_box[place]["long_range"] 
            lat_range = config.plot_bounding_box[place]["lat_range"] 
            return np.array(long_range), np.array(lat_range), resolution
    return np.array([None, None]), np.array([None, None]), config.plot_bounding_box["unknown"]["resolution"]
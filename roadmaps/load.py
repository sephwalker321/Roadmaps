from pathlib import Path
import os
import glob

import numpy as np
import pandas as pd
import geopandas as gpd

from datetime import datetime

import fiona
# enable KML support which is disabled by default
fiona.drvsupport.supported_drivers['kml'] = 'rw' 
fiona.drvsupport.supported_drivers['KML'] = 'rw' 

from roadmaps.functions import convert_distance, convert_time, load_yaml

class Generate_Config:
    def __init__(
        self, 
        place = "UK",
    ):
        """ 
        Class of configuration settings used across the module.
        
        Parameters
        ----------
        place: str 
            placename. ["canada", "uk", "usa", "world"]

        """
        place = place.lower()
        if place == "world":
            place = "countries"
        self.place = place.lower()
        
        self.set_fixed()
        self.load_config()
        
        self.plot_bounding_box = load_yaml(f"{self.working_dir}/roadmaps/bounding_boxes.yaml")
        self.shapefiles = load_yaml(f"{self.working_dir}/roadmaps/shapefiles.yaml")

    def set_fixed(self):
        """ 
        Set the default fixed configuration parameters.
        
        Parameters
        ----------

        Returns
        -------

        """
        self.working_dir = Path(os.getcwd()).parent

        self.sep = "history-"
        self.ext = "kml"
        self.klm_date_format =  "%Y-%m-%dT%H:%M:%S.%f%z"
        self.date_format     = "%Y-%m-%d"

        self.crs_IN   = "EPSG:4326"
        self.crs_OUT  = "EPSG:3857"
        return

    def load_config(self):
        """ 
        Set the customisable configuration parameters.
        
        Parameters
        ----------

        Returns
        -------

        """
        yaml_in = load_yaml(f"{self.working_dir}/roadmaps/config.yaml")
        self.road_data_dir   = yaml_in["roads_folder"]
        self.places_data_dir = yaml_in["places_folder"]
        self.plot_dir        = yaml_in["plots_folder"]

        self.default_date_min = datetime.fromisoformat(yaml_in["date_min"])
        self.default_date_max = datetime.fromisoformat(yaml_in["date_max"])
        self.date_min         = self.default_date_min
        self.date_max         = self.default_date_max

        self.distance_unit = yaml_in["distance_unit"]
        self.time_unit     = yaml_in["time_unit"]

        #Plotting formating
        self.road_line_colour = yaml_in["road_line_colour"] 
        self.n_colours        = yaml_in["n_colours"] 
        self.cmap             = yaml_in["cmap"] 
        self.dpi              = yaml_in["dpi"]
        return

    def change_dir(
            self,
            road_dir_new=None,
            places_dir_new=None,
        ):
        """ 
        Change the road and place directorys from the default.
        TODO Check directory exists?
        
        Parameters
        ----------
            road_dir_new: str
                folder path containing .klm driving journeys
            places_dir_new: str
                folder path containing .yaml places been
        
        Returns
        -------

        """
        if road_dir_new is not None:
            self.road_data_dir = road_dir_new
        if places_dir_new is not None:
            self.places_data_dir = places_dir_new
        return

    def set_dates(self, date_min=None, date_max=None):
        """ 
        Change the minimum and maximum dates in configuration settings.
        
        Parameters
        ----------
            date_min str
                Format YYYY-MM-DD e.g. 2020-01-01
            date_max: str
                Format YYYY-MM-DD e.g. 2020-01-01

        Returns
        -------

        """
        if date_min is not None:
            self.date_min = datetime.fromisoformat(date_min)
        else:
            self.date_min = self.default_date_min

        if date_max is not None:
            self.date_max = datetime.fromisoformat(date_max)
        else:
            self.date_max = self.default_date_max
        return

    def printout(self):
        """ 
        Print out summary of configuration set up
        TODO Write function
        
        Parameters
        ----------

        Returns
        -------

        """
        return
    
def glob_dates(
        config = Generate_Config(),
    ):
    """ 
    Collect dates of .klm files in road maps directory
    
    Parameters
    ----------
        config: class
            class of configuration settings instance

    Returns
    -------
        dates: np.array
            datetime dates of existing .klm road map files

    """
    dates = [history.split(config.sep)[-1].split(".")[0] for history in glob.glob(f'{config.working_dir}/{config.road_data_dir}/{config.sep}*.{config.ext}')]
    dates = [datetime.strptime(date, config.date_format) for date in dates]
    dates.sort()
    return np.array(dates)

def read_date_KLM(
        date,
        config = Generate_Config(),
    ):
    """ 
    Read in .klm from road map directory for given date and format into suitable geopandas dataframe.
    
    Parameters
    ----------
        date: str
            Format YYYY-MM-DD e.g. 2020-01-01
        config: class
            class of configuration settings instance

    Returns
    -------
        df: Geopandas dataframe
            Road journeys for given date

    """
    df_day = gpd.read_file(f'{config.working_dir}/{config.road_data_dir}/{config.sep}{date.strftime(config.date_format)}.{config.ext}', driver='KML')
   
    ids = []
    dates = []
    geopaths = []
    durations = []
    time_starts = []
    g_distances = []
    
    count = 0
    for row in range(df_day.shape[0]):
        #Only keep 'Driving' data formatted as LineStrings datatype.
        if df_day.iloc[row,:]["geometry"].__class__.__name__ != "LineString" or "Driving" not in df_day.iloc[row]["Description"]:
            pass
        else:
            description = df_day.iloc[row,:]['Description']
            description=description.replace("Driving from ", ',').replace(" to ", ',').replace(". Distance ", ',').replace("m", ',')
            description=description.split(",")

            T_start = datetime.strptime(description[1], config.klm_date_format)
            T_end = datetime.strptime(description[2], config.klm_date_format)
            duration = (T_end-T_start).seconds/convert_time(config.time_unit)
            distance = float(description[3])/convert_distance(config.distance_unit)

            ids.append(f"{date.strftime(config.date_format)}_{count}")
            dates.append(date)
            geopaths.append(df_day.iloc[row,:]["geometry"])
            time_starts.append(T_start.time())
            durations.append(duration)
            g_distances.append(distance) 
            count += 1

    if count == 0:
        return
    else:
        df = gpd.GeoDataFrame(data={
            "ID" : ids,
            "date" : dates,
            "time" : time_starts,
            'geometry' : geopaths,
            "distance" : g_distances,
            "duration" : durations,
        }, crs=config.crs_IN)
        df["speed"] = df["distance"] / df["duration"]
        return df
    
def load_in_roads(
        config = Generate_Config(),
    ):
    """ 
    Read in all .klm from road map directory for given date range and format into suitable geopandas dataframe.
    
    Parameters
    ----------
        config: class
            class of configuration settings instance

    Returns
    -------
        roads: Geopandas dataframe
            Road journeys for given date range

    """
    #glob all dates
    dates = glob_dates(config)

    #Truncate Dates
    dates = dates[dates >= config.date_min]
    dates = dates[dates <= config.date_max]
    
    count = 0
    for date in dates:
        df_day = read_date_KLM(date, config)        
        if df_day is None:
            continue
        else:
            count += 1
        
        #Get directly from the Google KLM instead...
        #df_day["distance"] = get_distance(df_day, config)

        if count == 1:
            roads = df_day
        else:
            roads = pd.concat([roads, df_day], ignore_index = True)
    return roads

def load_in_shapefile(
        config = Generate_Config(),
    ):
    """ 
    Load in shapefiles for the available regions.
    
    Parameters
    ----------
        config: class
            class of configuration settings instance

    Returns
    -------
        shapefile: Geopandas dataframe
            Regions shapefiles

    
    """
    folder_path = config.shapefiles[config.place]["folder_path"]
    shapefile_path = config.shapefiles[config.place]["shapefile_path"]
    col_name = config.shapefiles[config.place]["col_name"]

    map_path = f"{config.working_dir}/map_boundaries/{folder_path}/{shapefile_path}.shp"
    
    shapefile = gpd.read_file(map_path)
    shapefile=shapefile.sort_values(by=[col_name])
    return shapefile

def load_in_places(
        config = Generate_Config(),
    ):
    """ 
    Load in the places been yaml.
    
    Parameters
    ----------
        config: class
            class of configuration settings instance

    Returns
    -------
        data: dict
            Places been dictionary of booleans
    
    """
    places_path = f"{config.working_dir}/{config.places_data_dir}/{config.place}.yaml"
    data = load_yaml(places_path)
    return data
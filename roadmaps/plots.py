from roadmaps.plots_format import fig_initialize, set_size
fig_initialize()

import os

from roadmaps.load import Generate_Config
from roadmaps import format_data, functions

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.colors import Normalize as Norm
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.dates as mdates
tick_days = mdates.DayLocator() # every Day
tick_weeks = mdates.WeekdayLocator(byweekday=mdates.MO, interval=1)  # every Monday
tick_months = mdates.MonthLocator() # every month
tick_years = mdates.YearLocator() # every year

import geoplot.crs as gcrs

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import math
import contextily as ctx
from pyproj import Proj

class Plots:
    def __init__(
        self, 
        config = Generate_Config(),

        road_line_color = None,
        n_colours = None,
        cmap = None,
        show_title = True,
        
        dpi = None,
        image_ex = "pdf",
        
    ):
        self.config = config
        self.image_ex = image_ex
        self.show_title = show_title
        
        #Make plot directory
        plot_dir = f"{self.config.working_dir}/{self.config.plot_dir}"
        if os.path.exists(plot_dir) == False:
            os.mkdir(plot_dir)

        if road_line_color is not None:
            self.config.road_line_colour = road_line_color
        if n_colours is not None:
            self.config.n_colours = n_colours
        if cmap is not None:
            self.config.cmap = cmap

        if dpi is not None:
            self.config.dpi = dpi
            
        self.initalise_alpha_colourmap()

    def initalise_alpha_colourmap(self):
        """ 
        Initalise custom faded colourmap.
        
        Parameters
        ----------
        Returns
        -------
        """
        if "custom_alphamap" not in plt.colormaps():
            color_array = plt.get_cmap(self.config.cmap)(range(self.config.n_colours))
            color_array[:,-1] = np.logspace(0,-0.3,self.config.n_colours)[::-1]
            map_object = LinearSegmentedColormap.from_list(name='custom_alphamap',colors=color_array)
            plt.register_cmap(cmap=map_object)
        return
    
    def check_date_minmax(
            self,
            roads,
            date_min,
            date_max,
    ):
        """ 
        Trim roadmaps data over given data range for plotting
        
        Parameters
        ----------
            roads: Geopandas dataframe
                Road journeys for given date range
            date_min: str
                Minimum date of road maps. Format YYYY-MM-DD e.g. 2020-01-01
            date_max: str
                Maximum date of road maps. Format YYYY-MM-DD e.g. 2020-01-01

        Returns
        -------
            roads: Geopandas dataframe
                Road journeys for given new date range
            date_min: datetime
                Minimum date of road maps. 
            date_max: datetime
                Maximum date of road maps.

        """
        if date_min is not None:
            date_min = datetime.fromisoformat(date_min)
            roads = roads[roads["date"] >= date_min]
            date_min = roads["date"].min()
        else:
            date_min = max(self.config.date_min, roads["date"].min())
        if date_max is not None:
            date_max = datetime.fromisoformat(date_max)
            roads = roads[roads["date"] <= date_max]
            date_max = roads["date"].max()
        else:
            date_max = min(self.config.date_max, roads["date"].max())
        return roads, date_min, date_max

    def plot_road_map(
            self, 
            roads,
            date_min=None,
            date_max=None,
        ):
        """ 
        Plot the roadmaps over given data range.
        
        Parameters
        ----------
            roads: Geopandas dataframe
                Road journeys for given date range
            date_min: str
                Minimum date of road maps. Format YYYY-MM-DD e.g. 2020-01-01
            date_max: str
                Maximum date of road maps. Format YYYY-MM-DD e.g. 2020-01-01

        Returns
        -------
        """
        roads, date_min, date_max = self.check_date_minmax(roads, date_min, date_max)
        NDrives = roads.shape[0]
    
        f, ax = plt.subplots(1,1)
        f.set_size_inches(11.69, 8.27)
        
        ax.axis('off')
        xlim, ylim, resolution = format_data.restrict_plot(self.config.place)

        #Convert Lat long to x,y
        x1,y1 =Proj(self.config.crs_OUT)(xlim[0],ylim[0])
        x2,y2 =Proj(self.config.crs_OUT)(xlim[1],ylim[1])
        ax.set_ylim([y1,y2])
        ax.set_xlim([x1,x2])
        
        #Plot
        print(f"Number of drives: {NDrives} between {functions.format_date_string(date_min)} - {functions.format_date_string(date_max)}")

        roads["geometry"] = roads["geometry"].to_crs(self.config.crs_OUT)
        roads["geometry"].plot(ax=ax, color=self.config.road_line_colour, linewidth =.3, alpha=0.6)
        map_source = ctx.providers.OpenStreetMap.Mapnik
        ctx.add_basemap(ax=ax, crs=self.config.crs_OUT, zoom=resolution,source=map_source)
        
        if self.show_title:
            plt.title(f"{functions.format_date_string(date_min)} - {functions.format_date_string(date_max)}")
        plt.savefig(f"{self.config.working_dir}/{self.config.plot_dir}/road_map_{self.config.place}.{self.image_ex}", dpi=self.config.dpi, format=self.image_ex)
        plt.show()
        return 

    
    def plot_distance(
            self, 
            roads,
            date_min=None,
            date_max=None,
        ):
        """ 
        Plot odometer for distance driven over time
        
        Parameters
        ----------
            roads: Geopandas dataframe
                Road journeys for given date range
            date_min: str
                Minimum date of road maps. Format YYYY-MM-DD e.g. 2020-01-01
            date_max: str
                Maximum date of road maps. Format YYYY-MM-DD e.g. 2020-01-01

        Returns
        -------
        """
        d_unit, t_unit, s_unit = functions.get_units(self.config.distance_unit, self.config.time_unit)

        roads, date_min, date_max = self.check_date_minmax(roads, date_min, date_max)
        NDrives = roads.shape[0]
        UniqueDates = pd.date_range(date_min-timedelta(days=1),date_max,freq='d')

        odometer_file = f'{self.config.working_dir}/{self.config.road_data_dir}/odometer.yaml'
        odometer_bool = False
        if os.path.exists(odometer_file):
            odometer = functions.load_yaml(odometer_file)
            if odometer["odometer"] is not None: #Check odometer file not empty
                odometer_bool = True  
                odometer_distance_unit = odometer["distance_unit"]
                odometer_distances = np.array(list(odometer["odometer"].values()), dtype=float)
                odometer_distances *= functions.convert_distance(odometer_distance_unit)/functions.convert_distance(self.config.distance_unit)
                odometer_dates = np.array([ datetime.fromisoformat(date) for date in odometer["odometer"].keys()])

                if np.sum((odometer_dates>date_min) * (odometer_dates<date_max)) == 0:
                    odometer_bool = False
        
                indexes = []
                for di in range(len(odometer_distances)):
                    if odometer_dates[di] >= date_min and odometer_dates[di] <= date_max:
                        indexes.append(di)
                
                cum_dist_baseline = odometer_distances[indexes[0]]
                odometer_distances=odometer_distances[indexes]
                odometer_dates=odometer_dates[indexes]
                if len(indexes) == 0:
                    odometer_bool = False
                    
                    
        print(f"Number of drives: {NDrives} between {functions.format_date_string(date_min)} - {functions.format_date_string(date_max)}")
        N_days = (date_max-date_min).days
        
        dT = np.zeros(len(UniqueDates))
        date_i = 1
        odo_dates=[] 
        for date in UniqueDates[1:]:
            dT[date_i] += roads[roads["date"] == date]["distance"].sum()
            date_i += 1
            if odometer_bool:
                for od_date in odometer_dates:
                    if (od_date-date).days == 0:
                        odo_dates.append(date_i) 
        
        if len(odo_dates) == 0:
            odometer_bool = False  
                    
        CumDist = np.cumsum(dT)
        
        f, (ax1,ax2) = plt.subplots(2,1, sharex=True, gridspec_kw={'height_ratios': [3, 1]}) 
        plt.subplots_adjust(hspace=0.05)
        f.set_size_inches(set_size(subplots=(1, 1), fraction=1))

        ax1.plot(UniqueDates, CumDist, color=self.config.road_line_colour)
        ax2.plot(UniqueDates, dT, color=self.config.road_line_colour)

        if odometer_bool:
            diffs = []
            for di in range(len(odo_dates)):
                diffs.append(CumDist[odo_dates[di]]-odometer_distances[di])
            cum_dist_baseline=-np.nanmean(np.array(diffs))
        
            ax1.scatter(odometer_dates,odometer_distances-cum_dist_baseline, marker="x", color="r")
            ax1.scatter([],[], marker="x", color="r",label="MOT Record")
            
            

            #Set up twin axis for odometer
            ax1_s = ax1.twinx()
            Y_s = lambda Y: Y + cum_dist_baseline
            ymin, ymax = ax1.get_ylim()
            ax1_s.set_ylim((Y_s(ymin),Y_s(ymax)))
            ax1_s.plot([],[])
            ax1_s.set_ylabel(f"Odometer ({d_unit})")

        ax1.set_ylabel(f"Cumulative ({d_unit})")
        ax2.set_ylabel(f"Daily ({d_unit})")

        ax1.set_xlim([date_min-timedelta(days=1),date_max])
        ax1.set_ylim([0,None])
        ax2.set_ylim([0,None])

        if N_days < 4*7:
            ax2.xaxis.set_major_locator(tick_weeks)
            ax2.xaxis.set_minor_locator(tick_days)
        elif N_days < 4*7*3:
            ax2.xaxis.set_major_locator(tick_months)
            ax2.xaxis.set_minor_locator(tick_weeks)
        elif N_days < 4*7*12:
            ax2.xaxis.set_major_locator(tick_years)
            ax2.xaxis.set_minor_locator(tick_months)
        
        plt.savefig(f"{self.config.working_dir}/{self.config.plot_dir}/road_odometer_{self.config.place}.{self.image_ex}", dpi=self.config.dpi, format=self.image_ex)
        plt.show()
        return

    def plot_summary_histograms(
            self, 
            roads,
            date_min=None,
            date_max=None,
        ):
        """ 
        Plot summary histograms of distance, duration and average speed across all individual journeys.
        
        Parameters
        ----------
            roads: Geopandas dataframe
                Road journeys for given date range
            date_min: str
                Minimum date of road maps. Format YYYY-MM-DD e.g. 2020-01-01
            date_max: str
                Maximum date of road maps. Format YYYY-MM-DD e.g. 2020-01-01

        Returns
        -------
        """
        roads, date_min, date_max = self.check_date_minmax(roads, date_min, date_max)
        NDrives = roads.shape[0]

        d_unit, t_unit, s_unit = functions.get_units(self.config.distance_unit, self.config.time_unit)
        
        print(f"Number of drives: {NDrives} between {functions.format_date_string(date_min)} - {functions.format_date_string(date_max)}")
        print(f"Maximum distance: {roads['distance'].max():.2f}{d_unit}")
        print(f"Maximum duration: {roads['duration'].max():.2f}{t_unit}")
        print(f"Maximum average speed: {roads['speed'].max():.2f}{s_unit}")

        alpha = 0.6

        ax1_min = -1
        ax1_max = math.ceil(np.log10(roads["distance"].max()))

        ax1_nbins = 50
        ax1_bins = np.logspace(ax1_min, ax1_max, ax1_nbins)
        ax1_widths = ax1_bins[:-1]-ax1_bins[1:]
        ax1_bin_centers = (ax1_bins[1:] + ax1_bins[:-1])*0.5
        ax1_hist, _ = np.histogram(roads["distance"], bins=ax1_bins, density=True)

        ax2_min = -1
        ax2_max = math.ceil(np.log10(roads["duration"].max()))

        ax2_nbins = 50
        ax2_bins = np.logspace(ax2_min, ax2_max, ax2_nbins)
        ax2_widths = ax2_bins[:-1]-ax2_bins[1:]
        ax2_bin_centers = (ax2_bins[1:] + ax2_bins[:-1])*0.5
        ax2_hist, _ = np.histogram(roads["duration"], bins=ax2_bins, density=True)

        ax3_min = 0
        ax3_max = np.round(roads["speed"].max(),-1)
        
        ax3_step = 2.5
        ax3_bins = np.arange(ax3_min, ax3_max, ax3_step)
        ax3_widths = ax3_bins[1] - ax3_bins[0]
        ax3_bin_centers = (ax3_bins[1:] + ax3_bins[:-1])*0.5
        ax3_hist, _ = np.histogram(roads["speed"], bins=ax3_bins, density=True)

        f, (ax1, ax2, ax3) = plt.subplots(1,3) 
        f.set_size_inches(set_size(subplots=(1,3), fraction=1))

        ax1.bar(ax1_bin_centers, ax1_hist, width=ax1_widths,color=self.config.road_line_colour, alpha=alpha)
        ax2.bar(ax2_bin_centers, ax2_hist, width=ax2_widths,color=self.config.road_line_colour, alpha=alpha)
        ax3.bar(ax3_bin_centers, ax3_hist, width=ax3_widths,color=self.config.road_line_colour, alpha=alpha)


        ax1.set_xlabel(f"distance ({d_unit})")
        ax2.set_xlabel(f"duration ({t_unit})")
        ax3.set_xlabel(f"speed ({s_unit})")

        ax1.set_yticklabels([])
        ax2.set_yticklabels([])
        ax3.set_yticklabels([])

        ax1.set_xlim([10**ax1_min, 10**ax1_max])
        ax2.set_xlim([10**ax2_min, 10**ax2_max])
        ax3.set_xlim([ax3_min, ax3_max])

        ax1.set_xscale("log")
        ax2.set_xscale("log")

        if self.show_title:
            plt.suptitle(f"{functions.format_date_string(date_min)} - {functions.format_date_string(date_max)}", y=1.05)
        f.set_size_inches(set_size(subplots=(1,3), fraction=1))
        plt.savefig(f"{self.config.working_dir}/{self.config.plot_dir}/road_summary_all_{self.config.place}.{self.image_ex}", dpi=self.config.dpi, format=self.image_ex)
        plt.show()
        return

    def plot_summary_weekday_histograms(
            self, 
            roads,
            date_min=None,
            date_max=None,
        ):
        """ 
        Plot summary by weekday histograms over date range across all individual journeys.
        
        Parameters
        ----------
            roads: Geopandas dataframe
                Road journeys for given date range
            date_min: str
                Minimum date of road maps. Format YYYY-MM-DD e.g. 2020-01-01
            date_max: str
                Maximum date of road maps. Format YYYY-MM-DD e.g. 2020-01-01

        Returns
        -------
        """
        roads, date_min, date_max = self.check_date_minmax(roads, date_min, date_max)

        d_unit, t_unit, s_unit = functions.get_units(self.config.distance_unit, self.config.time_unit)
        
        days_list = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        which = ["distance", "duration", "speed"]
        alpha = 0.4
        width = 0.8

        f, axes = plt.subplots(3,1, sharex=True) 
        f.set_size_inches(set_size(subplots=(1,.75), fraction=1))
        plt.subplots_adjust(hspace=0.05)

        axes[0].fill_between([0,0], y1=0, y2=0, color="green", alpha=alpha,label=r"$1\sigma$")
        axes[0].fill_between([0,0], y1=0, y2=0, color="yellow", alpha=alpha,label=r"$2\sigma$")
        axes[0].plot([0,0], [0,0], color="black", ls="-", label="mean")
        axes[0].plot([0,0], [0,0], color="red", ls="-", label="median")

        for ai in range(3):
            for di in range(7):
                roads_day = roads[roads["date"].dt.day_name()==days_list[di]]
                di_mean = np.nanmean(roads_day[which[ai]].values)
                di_median = np.nanmedian(roads_day[which[ai]].values)
                di_std = np.nanstd(roads_day[which[ai]].values, ddof=1)
                di_min = np.nanmin(roads_day[which[ai]].values)
                di_max = np.nanmax(roads_day[which[ai]].values)

                axes[ai].plot([di-width/2, di+width/2], [di_mean,di_mean], color="black", ls="-")
                axes[ai].plot([di-width/2, di+width/2], [di_median,di_median], color="red", ls="-")
                axes[ai].errorbar([di],[di_mean],np.array([di_mean-di_min,di_max-di_mean]).reshape(2,1), color="black")

                # 1 sigma
                axes[ai].fill_between([di-width/2, di+width/2], y1=max(0,di_mean-di_std), y2=max(0,di_mean+di_std), color="green", alpha=alpha)
                #
                axes[ai].fill_between([di-width/2, di+width/2], y1=max(0,di_mean-2*di_std), y2=max(0,di_mean-1*di_std), color="yellow", alpha=alpha)
                axes[ai].fill_between([di-width/2, di+width/2], y1=max(0,di_mean+1*di_std), y2=max(0,di_mean+2*di_std), color="yellow", alpha=alpha)

        axes[0].set_ylabel(f"distance ({d_unit})")
        axes[1].set_ylabel(f"duration ({t_unit})")
        axes[2].set_ylabel(f"speed ({s_unit})")
        axes[2].set_xticklabels([""]+days_list, rotation = 90)

        axes[0].set_xlim([-0.5, 6+0.5])
        axes[0].set_ylim([0, None])
        axes[1].set_ylim([0, None])
        axes[2].set_ylim([0, None])

        axes[0].legend(loc="upper left")

        if self.show_title:
            axes[0].set_title(f"{functions.format_date_string(date_min)} - {functions.format_date_string(date_max)}")
        f.set_size_inches(set_size(subplots=(1,.75), fraction=1))
        plt.savefig(f"{self.config.working_dir}/{self.config.plot_dir}/road_summary_daily_{self.config.place}.{self.image_ex}", dpi=self.config.dpi, format=self.image_ex)
        plt.show()
        return 
        
    def plot_regions_basemap(
        self,
        shapefile,
        been,
    ):
        """ 
        Plot regions been to.
        
        Parameters
        ----------
            shapefile: Geopandas dataframe
                Regions shapefiles

            data: dict
                Places been dictionary of booleans

        Returns
        -------
        """
        col_name = self.config.shapefiles[self.config.place]["col_name"]

        colors = []
        for region in been["region"].keys():
            if been["region"][region] == True:
                colors.append(self.config.shapefiles["have_colour"])
            else:
                colors.append(self.config.shapefiles["not_colour"])
                
        cities_long = []
        cities_lat = []
        if been["cities"] is not None:
            for city in been["cities"]:
                lat = been["cities"][city][0]
                long = been["cities"][city][1]
                long,lat =Proj(self.config.crs_OUT)(long, lat)
                cities_lat.append(lat)
                cities_long.append(long)
        
        f, ax = plt.subplots(1,1) 
        f.set_size_inches(set_size(subplots=(1,1), fraction=1))
        #f.set_size_inches(11.69, 8.27)
        
        shapefile=shapefile.to_crs(self.config.crs_OUT)
        shapefile.plot(ax=ax, edgecolor='darkgrey', facecolor=colors, linewidth=.3)
        ax.scatter(cities_long,cities_lat, color="r", marker="x")
        
        ax.axis('off')
        xlim, ylim, _ = format_data.restrict_plot(self.config.place)
        x1,y1 =Proj(self.config.crs_OUT)(xlim[0],ylim[0])
        x2,y2 =Proj(self.config.crs_OUT)(xlim[1],ylim[1])
        ax.set_ylim([y1,y2])
        ax.set_xlim([x1,x2])
        plt.savefig(f"{self.config.working_dir}/{self.config.plot_dir}/places_map_{self.config.place}.{self.image_ex}", dpi=self.config.dpi, format=self.image_ex)
        plt.show()
        return
import yaml

def load_yaml(filename):
    """ 
    Load yaml into python dict
    
    Parameters
    ----------
        filename: str
            absolute path of .yaml file 

    Returns
    -------
        YAML: dict
            Required file

    """
    with open(filename, "r") as stream:
        try:
            YAML = yaml.safe_load(stream)
            return YAML
        except yaml.YAMLError as exc:
            print(exc)
    return
    

def convert_distance(
        distance_unit,
    ):
    """ 
    Convert meters into unit of choice.
    
    Parameters
    ----------
        distance_unit: str
            desired unit

    Returns
    -------
        unit_factor: float
            rescaling factor e.g. x[meters] / unit_factor = y[distance_unit]

    """
    if distance_unit in ["mi","mile","miles"]:
        unit_factor = 1609.34
    elif distance_unit in ["km","kilometer","kilometers"]:
        unit_factor = 1000.0
    elif distance_unit in ["m", "meter", "meters"]:
        unit_factor = 1.0
    return unit_factor

def convert_time(
        time_unit,
    ):
    """ 
    Convert seconds into unit of choice.
    
    Parameters
    ----------
        time_unit: str
            desired unit

    Returns
    -------
        unit_factor: float
            rescaling factor e.g. x[s] / unit_factor = y[time_unit]

    """
    if time_unit in ["s", "sec", "secs", "second", "seconds"]:
        unit_factor = 1
    elif time_unit in ["min", "mins", "minute", "minutes"]:
        unit_factor = 60.0
    elif time_unit in ["hr", "hour", "hours"]:
        unit_factor = 3600.0
    return unit_factor

def get_units(
        distance_unit,
        time_unit,
):
    """ 
    Get plotting labels for the units of distance, duration and speed.
    
    Parameters
    ----------
        distance_unit: str
            unit of distances
        time_unit: str
            unit of durations

    Returns
    -------
        distance_unit: str
            plotting distance label
        duration_unit: str
            plotting duration label
        speed_unit: str
            plotting speed label

    """
    if distance_unit in ["mi","mile","miles"]:
        distance_unit = "mi"
        distance_unit_s = "m"
    elif distance_unit in ["km","kilometer","kilometers"]:
        distance_unit = "km"
        distance_unit_s = "km"
    elif distance_unit in ["m", "meter", "meters"]:
        distance_unit = "m"
        distance_unit_s = "m"

    if time_unit in ["s", "sec", "secs", "second", "seconds"]:
        time_unit = "s"
        time_unit_s = "s"
    elif time_unit in ["min", "mins", "minute", "minutes"]:
        time_unit = "min"
        time_unit_s = "m"
    elif time_unit in ["hr", "hour", "hours"]:
        time_unit = "hr"
        time_unit_s = "h"

    speed_unit = f"{distance_unit_s}p{time_unit_s}"
    return distance_unit, time_unit, speed_unit

def format_date_string(
        date
    ):
    """ 
    Get plotting representation for the date
    
    Parameters
    ----------
        date: str
            A date

    Returns
    -------
        date: str
            plotting date

    """
    day_num = date.strftime('%d')
    month_num = date.strftime('%m')
    month_str = date.strftime('%B')
    year = date.strftime('%Y')
    
    if day_num[0] == 0:
        day_num = day_num[1:]
    
    if day_num[-1] == "1":
        super_str = "st"
    elif day_num[-1] == "2":
        super_str = "nd"
    elif day_num[-1] == "3":
        super_str = "rd"
    else:
        super_str = "th"
        
    return f"{day_num}{super_str} {month_str} {year}"
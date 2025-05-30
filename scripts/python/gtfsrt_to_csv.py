import pandas as pd
import os
from colorama import Fore, Back, Style
import argparse
from datetime import datetime, timedelta
from gtfs_realtime_utils import get_gtfs_entities_from_directory

def entities_to_dataframe(entities, round=5):
    '''
    Converts a list of entities into a dataframe
    
    Params
    ------
    entities: list
        a list of gtfsrt entities

    round: int
        number of dp to round coordinates

    Returns
    -------
    df: pandas.DataFrame
        The resulting dataframe
    '''
    records = []

    print(f"There are {Fore.YELLOW}{len(entities)}{Style.RESET_ALL} entities (bus location reports).")

    for e in entities:
        v = e.vehicle
        records.append({
            "trip_id": v.trip.trip_id,
            "start_time": v.trip.start_time,
            "start_date": v.trip.start_date,
            "schedule_relationship": v.trip.schedule_relationship,
            "route_id": v.trip.route_id,
            "latitude": v.position.latitude,
            "longitude": v.position.longitude,
            "bearing": int(v.position.bearing),
            "stop_sequence": v.current_stop_sequence,
            "status": v.current_status,
            "timestamp": v.timestamp,
            "vehicle_id": v.vehicle.id,
        })

    df = pd.DataFrame(records)

    # Optionally round coordinates
    if round:
        df['longitude'] = df['longitude'].round(round)
        df['latitude'] = df['latitude'].round(round)

    return df

def remove_duplicate_reports(df, subset=['timestamp', 'vehicle_id', 'trip_id', 'longitude', 'latitude'], sortby=['timestamp', 'vehicle_id', 'trip_id']):
    '''
    Removes duplicate data and sorts the resulting dataframe. Prints the fraction of data that was duplicated.

    Params
    ------
    df: pandas.DataFrame

    subset: list
        list of column names to use when checking for duplicates
    
    sortby: list
        columns to sort the final frame by

    Returns
    -------
    df: pandas.DataFrame
        Deduplicated dataframe
    '''
    with_duplicates = len(df) # Count the length of the raw dataframe

    df.drop_duplicates(subset=subset, keep='first', inplace=True) # The first/last here shouldn't matter as one of the duplicate fields is timestamp. So these are data points that are for the same point in time too.
    
    without_duplicates = len(df) # Count the length of the de-duplicated dataframe
    
    fraction_duplicated = round((1 - without_duplicates/with_duplicates)*100, 4)
    
    print(f"Fraction of data that was duplicated in 'longitude', 'latitude', 'timestamp', 'vehicle_id', 'trip_id':{Fore.YELLOW}{fraction_duplicated}%{Style.RESET_ALL}")

    df.sort_values(by=sortby, ascending=True, inplace=True)
    return df

def set_args():
    '''Set the arguments given in the command line'''
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--date", help="Date string format 'YYYY/mm/dd'")
    parser.add_argument("-f", "--force", action='store_true')
    args = parser.parse_args()
    return args

def main():
    BODSARCHIVE = os.environ['BODSARCHIVE']
    
    args = set_args()

    if not args.date: # if no date argument, create datestring for previous day
        now = datetime.now() - timedelta(days=1) # current date and time minus one day
        datestring = now.strftime("%Y/%m/%d/") # format the date
    else:
        datestring = args.date # get the command line variable if supplied

    OUTDIR = os.path.join(BODSARCHIVE, 'csv', datestring[0:4])
    os.makedirs(OUTDIR, exist_ok=True) # ensure directory exists
    OUTPATH = os.path.join(OUTDIR, "csv-" + datestring.replace("/", "") + '.csv.zip')

    # If not forced, but OUTPATH is already a file.
    if not args.force and os.path.isfile(OUTPATH):
            print('Already a file.')

    else: 
        entities = get_gtfs_entities_from_directory(os.path.join(BODSARCHIVE, 'gtfsrt', datestring))
        print(f"{Fore.GREEN}Entities loaded from binaries{Style.RESET_ALL}")
        df = entities_to_dataframe(entities, round=5)
        print(f"{Fore.GREEN}Entities loaded into DataFrame{Style.RESET_ALL}")
        clean_df = remove_duplicate_reports(df)
        print(f"{Fore.GREEN}Duplicates removed{Style.RESET_ALL}")
        clean_df.to_csv(OUTPATH, index=False)
        print(f"File successfully saved to {Fore.MAGENTA}{OUTPATH}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()

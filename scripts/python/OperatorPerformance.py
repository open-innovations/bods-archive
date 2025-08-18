import pandas as pd
import shutil
from pathlib import Path
from operator import attrgetter
from datetime import datetime, timedelta
from gtfs_realtime_utils import get_gtfs_entities_from_directory
from gtfs_utils import GTFSTimetable
import sys

class OperatorPerformance():
    def __init__(self):
        self.ROOT = Path(__file__).cwd().resolve()
        self.TEMPDIR = self.ROOT / "temp"
        pass

    def set_dates(self, given_date:str):
        self.given_date = datetime.strptime(given_date, "%Y%m%d")
        self.given_date_as_string = self.given_date.strftime("%Y%m%d")
        self.given_date_as_int = int(self.given_date_as_string)
        self.day_of_week = self.given_date.strftime("%A").lower()
        print("Date:", self.given_date, "Day:", self.day_of_week)
    
    def get_entities_as_df(self):
        if not (Path(self.TEMPDIR / "gtfsrt")).exists():
            print("You don't appear to have the gtfsrt data for the date requested! You may need to extract them using BulkDownloader first.")
            sys.exit(0)
        entities = get_gtfs_entities_from_directory(str(Path(self.TEMPDIR / "gtfsrt")))
        print("Got entities as a list")
        #TODO add lat, long, timestamp here. then drop duplicates before we do any counting
        getter = attrgetter('vehicle.trip.trip_id')
        trip_ids = list(map(getter, entities))
        print("Got all records")

        df = pd.DataFrame(data={'trip_id': trip_ids})
        # print(df.head().to_csv())
        print("Added to df")

        self.df = df
        return df

    def get_unique_trip_ids_as_list(self, df:pd.DataFrame):
        num_unique_ids_realtime = df.trip_id.nunique()
        print("Number of unique trip_ids: ", num_unique_ids_realtime)
        unique_ids_realtime = df.trip_id.unique()
        print("Got unique trip_ids as a list")
        return unique_ids_realtime
    
    def load_timetables(self, region:str, date:str):
        if not (self.TEMPDIR / f"timetables/itm_{region}_gtfs_{date}.zip").exists():
            print("You don't appear to have the timetables for the date requested! You may need to extract them using BulkDownloader first.")
            sys.exit(0)

        timetable = GTFSTimetable(str(self.TEMPDIR / f"timetables/itm_{region}_gtfs_{date}.zip"))

        agency = timetable.dfs['agency']
        routes = timetable.dfs['routes']
        trips = timetable.dfs['trips']
        calendar = timetable.dfs['calendar']

        self.full_timetable = (agency
                               .merge(routes, on='agency_id', how='inner')
                               .merge(trips, on='route_id', how='inner')
                               .merge(calendar, on='service_id', how='inner')
                            )
        
        # Start date of the route must be on the given day or earlier, end date is on the given day or after, and service must run on the given day of the week
        self.timetable_for_given_date = self.full_timetable[
            (self.full_timetable.start_date <= self.given_date_as_int) & 
            (self.full_timetable.end_date >= self.given_date_as_int) & 
            (self.full_timetable[self.day_of_week]==1)
            ]
        print("Loaded the timetables and simplified to the given date.")
        return self.timetable_for_given_date

    def filter_timetables_by_trip_id(self, df, realtime_ids:list[str]) -> pd.DataFrame:
        # unique_ids_real_time = self.get_unique_trip_ids_as_list()
        filtered = df[df.trip_id.isin(realtime_ids)].filter(items=['agency_id', 'agency_name', 'route_short_name', 'trip_id'])
        print("Filtered the timetable based on realtime trip_ids")
        return filtered
    
    def group(self, df:pd.DataFrame, rename_for_trip_id_col:str):
        return df.groupby(['agency_name', 'agency_id'])['trip_id'].size().reset_index().rename(columns={'trip_id': rename_for_trip_id_col})
    
    def calculate_percentage_timetable_in_real(self, real: pd.DataFrame, timetable: pd.DataFrame):
        res = real.merge(timetable, on=['agency_name', 'agency_id'], how='left')
        res['percentage_real_in_timetable'] = (res['real'] / res['timetable']).mul(100).round(2)
        res.sort_values(by=['percentage_real_in_timetable'], inplace=True, ascending=True)
        
        return res
    
    def cleanup(self):
        shutil.rmtree(self.TEMPDIR / 'timetables')
        shutil.rmtree(self.TEMPDIR / 'gtfsrt')

    def run(self, date:str, regions=['north_east', 'north_west', 'yorkshire', 'east_anglia', 'east_midlands', 'west_midlands', 'south_east', 'south_west']):
        # Set all the dates we need
        self.set_dates(date)
        
        # Load the entities into a dataframe
        realtime_df = self.get_entities_as_df()

        # Get the trip_ids that appeared in the realtime data
        realtime_ids = self.get_unique_trip_ids_as_list(realtime_df)

        # TODO ALSO add a count of unique trip_ids. Then we join to timetable. We then have a number of gps points per trip.
        # TODO ADD total # gps points per operator. 
        for region in regions:
        
            # Load the timetable and filter down to given date
            timetable_for_given_date = self.load_timetables(region, date)

            # Filter the timetable down to the observed trip_ids' trips only
            filtered_timetable_based_on_observed_trip_ids = self.filter_timetables_by_trip_id(timetable_for_given_date, realtime_ids=realtime_ids)
            
            # Calculate the number of trips for both real and timetable, per operator, on a given dat
            real = self.group(df=filtered_timetable_based_on_observed_trip_ids, rename_for_trip_id_col='real')
            timetable = self.group(df=timetable_for_given_date, rename_for_trip_id_col='timetable') 

            result_df = self.calculate_percentage_timetable_in_real(real, timetable)

            result_df.to_csv(self.TEMPDIR / f"{date}_{region}_performance.csv", index=False)

        self.cleanup()
    
if __name__ == "__main__":
    OperatorPerformance().run(date='20250817')
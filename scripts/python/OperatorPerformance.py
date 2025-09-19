import pandas as pd
import shutil
from pathlib import Path
from operator import attrgetter
from datetime import datetime
from zipfile import ZipFile
import sys
import argparse
from datetime import timedelta

# from utils import ROOT, TEMPDIR, DIRS_DICT
from scripts.python.utils import Fore, Style
from scripts.python.gtfs_realtime_utils import get_gtfs_entities_from_directory, yield_gtfs_entities_per_file
from scripts.python.gtfs_utils import GTFSTimetable

class OperatorPerformance():
    def __init__(self):
        self.ROOT = Path(__file__).cwd().resolve()

        self.TEMPDIR = self.ROOT / "temp"
        self.TEMPDIR.mkdir(exist_ok=True)

        self.DIRS_DICT = {
            'gtfsrt': self.TEMPDIR / 'gtfsrt',
            'sirivm': self.TEMPDIR / 'sirivm',
            'timetables': self.TEMPDIR / 'timetables'
        }
        self.args = self._set_args()
        pass
    
    def _set_args(self):
        """
        Parses and returns command-line arguments for the archive downloader script.
        Arguments:
            -d, --date: Start date as a string in 'YYYYmmdd' format.
        Returns:
            argparse.Namespace: Parsed command-line arguments.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument("-d", "--date", required=False, help="Date string format 'YYYYmmdd'")
        args = parser.parse_args()
        return args
    
    def set_dates(self, given_date:str):
        self.given_date = datetime.strptime(given_date, "%Y%m%d")
        self.given_date_as_string = self.given_date.strftime("%Y%m%d")
        self.given_date_as_int = int(self.given_date_as_string)
        self.day_of_week = self.given_date.strftime("%A").lower()
        print("Date:", self.given_date, "\nDay of the week:", self.day_of_week)
    
    def unzip_bulk_download(self, formats=['gtfsrt', 'timetables']):
        for format in formats:
            z_file_path = self.TEMPDIR / f"{format}-{self.given_date_as_int}.zip"
            if not Path(z_file_path).exists():
                print(f"{Fore.RED}{z_file_path}{Style.RESET_ALL} does not exist.\nHave you downloaded the bulk files first?")
                sys.exit(1)
            with ZipFile(z_file_path) as zf:
                i = 1
                namelist = zf.namelist()
                total = len(namelist)
                for file in namelist:
                    with zf.open(file, 'r') as f:
                        # get the file name
                        file_name = Path(file).name
                        # read the content
                        content = f.read()
                        # write to a new file in the current directory
                        out_path = self.DIRS_DICT[format]
                        # ensure it exists
                        out_path.mkdir(exist_ok=True)
                        with open(out_path / file_name, 'wb') as out_file:
                            out_file.write(content)
                    if i % (total // 10) == 0:
                        print(f"Unzipped {Fore.YELLOW}{round(i*100 / total)}%{Style.RESET_ALL} of {Fore.YELLOW}{total}{Style.RESET_ALL} files into {Fore.GREEN}{out_path}{Style.RESET_ALL}")
                    i += 1

    # def get_entities_as_df(self):
    #     if not (Path(self.TEMPDIR / "gtfsrt")).exists():
    #         print("You don't appear to have the gtfsrt data for the date requested! You may need to extract them using BulkDownloader first.")
    #         sys.exit(0)
    #     entities = get_gtfs_entities_from_directory(str(Path(self.TEMPDIR / "gtfsrt")))
    #     print("Got entities as a list")
    #     #TODO add lat, long, timestamp here. then drop duplicates before we do any counting
    #     # print(entities[0])
    #     getter = attrgetter('vehicle.trip.trip_id', 'vehicle.position.latitude', 'vehicle.position.longitude', 'vehicle.timestamp')
    #     mapped_data = list(map(getter, entities))
    #     # print("mapped_data", mapped_data[0])
    #     # print("trip_ids", trip_ids)
    #     print("Got all records")
    #     # Define column names corresponding to the attributes
    #     column_names = ['trip_id', 'latitude', 'longitude', 'timestamp']

    #     # Create the DataFrame
    #     df = pd.DataFrame(mapped_data, columns=column_names)
    #     # df = pd.DataFrame(data={'trip_id': trip_ids})
    #     # print(df.head().to_csv())
    #     print("Added to df")
    #     print("Dropping dupes")
    #     # A duplicate is the same bus, at the same location, at the same time.
    #     df = df.drop_duplicates(subset=['trip_id', 'latitude', 'longitude', 'timestamp'])
    #     print("Dropped dupes")
    #     self.df = df
    #     return df

    def get_entities_as_df(self):
        gtfs_dir = Path(self.TEMPDIR / "gtfsrt")
        if not gtfs_dir.exists():
            print("GTFS-RT directory not found. Run BulkDownloader first.")
            sys.exit(0)

        paths = list(gtfs_dir.glob("*.zip"))
        if not paths:
            print("No GTFS-RT ZIP files found.")
            sys.exit(0)

        all_dfs = []
        getter = attrgetter(
            'vehicle.trip.trip_id',
            'vehicle.position.latitude',
            'vehicle.position.longitude',
            'vehicle.timestamp'
        )

        for entities in yield_gtfs_entities_per_file(paths):
            try:
                mapped = list(map(getter, entities))
                df = pd.DataFrame(mapped, columns=['trip_id', 'latitude', 'longitude', 'timestamp'])
                all_dfs.append(df)
            except AttributeError as e:
                print(f"Skipping one file due to missing fields: {e}")
                continue

        if not all_dfs:
            print("No valid GTFS-RT data found.")
            return pd.DataFrame(columns=['trip_id', 'latitude', 'longitude', 'timestamp'])

        df_all = pd.concat(all_dfs, ignore_index=True)
        df_all = df_all.drop_duplicates(subset=['trip_id', 'latitude', 'longitude', 'timestamp'])

        self.df = df_all
        return df_all

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
    
    def trip_id_occurences_per_agency(self, timetable_for_given_date:pd.DataFrame, realtime_df:pd.DataFrame):
        timetable_value_counts = self.group(timetable_for_given_date, 'timetable')
        
        # merged timetable to realtime data. This will give trips that actually occured.
        merged = timetable_for_given_date.merge(realtime_df, on='trip_id', how='inner')
        real_value_counts = merged.groupby(['agency_id', 'agency_name'])['trip_id'].value_counts().reset_index()

        # Define bins and labels
        bins = [1, 10, 20, 50, 1000]
        labels = ['1-10', '11-20', '21-50','51-1000']

        # Assign bins to a new column
        real_value_counts['count_range'] = pd.cut(real_value_counts['count'], 
                                                  bins=bins, 
                                                  labels=labels, 
                                                  right=True, 
                                                  include_lowest=True
                                                  )

        # Group by agency and count the number of occurrences in each range
        vc_unstacked = real_value_counts.groupby(['agency_id', 'count_range'], observed=False).size().unstack(fill_value=0)
        result = timetable_value_counts.merge(vc_unstacked.reset_index(), on='agency_id')

        return result
    
    def cleanup(self):
        shutil.rmtree(self.TEMPDIR / 'timetables')
        shutil.rmtree(self.TEMPDIR / 'gtfsrt')

    def run(self, regions=['north_east', 'north_west', 'yorkshire', 'east_anglia', 'east_midlands', 'west_midlands', 'south_east', 'south_west']):
        # Set all the dates we need from cmdline args
        date = self.args.date if self.args.date else (datetime.now() - timedelta(days=1))
        self.set_dates(date)
        
        # Unzip the downloads to temporary directory
        self.unzip_bulk_download()

        # Load the entities into a dataframe
        realtime_df = self.get_entities_as_df()

        for region in regions:
        
            # Load the timetable and filter down to given date
            timetable_for_given_date = self.load_timetables(region, date)

            # Filter the timetable down to the observed trip_ids' trips only
            # filtered_timetable_based_on_observed_trip_ids = self.filter_timetables_by_trip_id(timetable_for_given_date, realtime_ids=realtime_ids)
            
            # Calculate the number of trips for both real and timetable, per operator, on a given dat
            # real = self.group(df=filtered_timetable_based_on_observed_trip_ids, rename_for_trip_id_col='real')
            # timetable = self.group(df=timetable_for_given_date, rename_for_trip_id_col='timetable') 

            # result_df = self.calculate_percentage_timetable_in_real(real, timetable)

            result = self.trip_id_occurences_per_agency(timetable_for_given_date, realtime_df)

            result.to_csv(self.TEMPDIR / f"{date}_{region}_performance.csv", index=False)

        self.cleanup()
    
if __name__ == "__main__":
    OperatorPerformance().run()
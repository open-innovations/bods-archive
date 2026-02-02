from zipfile import ZipFile
from concurrent.futures import ThreadPoolExecutor
from google.transit import gtfs_realtime_pb2
import polars as pl
import gc
from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

class GTFSRT2Parquet:
    def __init__(self):
        self.gtfsrt_schema = self.get_schema()
        self.ROOT = Path.cwd()
        load_dotenv()
        self.BODS_ARCHIVE_DIR = Path(os.environ.get("BODSARCHIVE"))
        pass

    def setup_yesterday(self):
        self.yesterday = datetime.now() - timedelta(days=1)
        return self.yesterday.strftime("%Y%m%d")

    def get_schema(self):
        # this is currently based of UK BODS data.
        SCHEMA = [
            "entity_id",
            "trip_id",
            "route_id",
            "start_date",
            "start_time",
            "lat",
            "lon",
            "bearing",
            "timestamp",
            "vehicle_id",
        ]
        return SCHEMA
    
    def parse_member(self, member_bytes):
        """parse an individual gtsfrt binary file"""
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(member_bytes)

        out = []
        for ent in feed.entity:
            if not ent.HasField("vehicle"):
                continue

            v = ent.vehicle
            pos = v.position

            out.append((
                ent.id,
                v.trip.trip_id,
                v.trip.route_id,
                v.trip.start_date,
                v.trip.start_time,
                round(pos.latitude, 5),
                round(pos.longitude, 5),
                pos.bearing,
                v.timestamp,
                v.vehicle.id,
            ))
        return out

    def stream_gtfsrt(self, zip_path, batch_size=10000):
        print(f"Reading {zip_path}")
        batch = []
        futures = []

        with ZipFile(zip_path) as zf, ThreadPoolExecutor(max_workers=12) as ex:
            for info in zf.infolist():
                with zf.open(info) as subzip_bytes:
                    try:
                        with ZipFile(subzip_bytes) as subzf:
                            data = subzf.read("gtfsrt.bin")
                    except Exception as e:
                        print(f"Failed with exception: {e}")
                        print(f"Skipping: {subzip_bytes}")
                        continue

                futures.append(ex.submit(self.parse_member, data))

                if len(futures) >= 32:  # tune to CPU
                    for fut in futures:
                        batch.extend(fut.result())
                    futures.clear()

                if len(batch) >= batch_size:
                    yield pl.DataFrame(batch, schema=self.gtfsrt_schema, orient="row")
                    batch.clear()
                    gc.collect()

            # flush
            for fut in futures:
                batch.extend(fut.result())

            if batch:
                yield pl.DataFrame(batch, orient="row", schema=self.gtfsrt_schema)

    def write_dataset(self, stream:pl.DataFrame, temp_dir:Path):
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(exist_ok=True, parents=True)
        print(f"Saving to {self.temp_dir}")
        for i, df in enumerate(stream):
            pth = f"{self.temp_dir}/part-{i:06d}.parquet"
            df.write_parquet(pth)
            print(f"Wrote to {pth}")
    
    def read_and_combine(self):
        df = pl.scan_parquet(self.temp_dir / "*.parquet")

        colnames = df.collect_schema().names()
        df = df.with_columns(
            pl.col("lat").round(5).alias("lat"),
            pl.col("lon").round(5).alias("lon")
        )
        df = df.unique(subset=[col for col in colnames if col not in ("entity_id", "bearing")])
        df = df.collect()
        outpath = self.BODS_ARCHIVE_DIR / f"gtfsrt/{self.yesterday.year}/{str(self.yesterday.month).zfill(2)}/{str(self.yesterday.day).zfill(2)}/all_bus_locations_deduplicated.parquet"
        print(f"Writing to {outpath}")
        df.write_parquet(outpath)
        self.passing = True

    def clean_up(self):
        if self.passing:
            for f in self.temp_dir.glob("*.parquet"):
                f.unlink()
            self.temp_dir.rmdir()

    def run(self, date=None):
        if not date:
            zip_file_date = self.setup_yesterday()
            print(f"Zipfile date: {zip_file_date}")
        stream = self.stream_gtfsrt(zip_path=self.BODS_ARCHIVE_DIR / f"gtfsrt/{self.yesterday.year}/{str(self.yesterday.month).zfill(2)}/{str(self.yesterday.day).zfill(2)}" / f"gtfsrt-{zip_file_date}.zip")
        self.write_dataset(stream=stream, temp_dir=self.ROOT / "tmp")
        self.read_and_combine()
        self.clean_up()

if __name__ == "__main__":
    GTFSRT2Parquet().run(date=None)
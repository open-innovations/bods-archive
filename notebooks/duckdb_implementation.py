# Load DuckDB, obviously.
import duckdb as db

# Install and load spatial plugins
db.sql("INSTALL spatial; LOAD spatial;")
# Load the NAPTAN stops file to get the bearings of stops
# <https://beta-naptan.dft.gov.uk/download/national> download here
db.sql(
    """
    CREATE OR REPLACE TEMP TABLE NAPTAN AS 
    SELECT 
        ATCOCode AS stop_id, 
        Bearing
    FROM 
        read_csv_auto('../Stops.csv')"""
)
# Load each of the components of a GTFS timetable file as a table in DuckDB

# Just download a timetable from the archive and unzip it.
for f in [
    "agency",
    "calendar_dates",
    "calendar",
    "feed_info",
    "routes",
    "shapes",
    "stop_times",
    "stops",
    "trips",
]:
    db.sql(
        f"CREATE OR REPLACE TEMP TABLE {f} AS SELECT * FROM read_csv_auto('../itm_yorkshire_gtfs_20260208/{f}.txt')"
    )
# Convert named bearing to degrees from North clockwise
db.sql("""
    CREATE OR REPLACE TEMP TABLE stops AS 
    SELECT *,
    CASE
        WHEN Bearing = 'N' THEN 0
        WHEN Bearing = 'NE' THEN 45
        WHEN Bearing = 'E' THEN 90
        WHEN Bearing = 'SE' THEN 135
        WHEN Bearing = 'S' THEN 180
        WHEN Bearing = 'SW' THEN 225
        WHEN Bearing = 'W' THEN 270
        WHEN Bearing = 'NW' THEN 315
        ELSE 0
    END AS numeric_bearing
    FROM stops s JOIN NAPTAN n ON s.stop_id = n.stop_id""")
# Look at the stops table
db.sql("SELECT * FROM stops limit 1")
# Join trips, stop_times, stops to create TIMETABLE
db.sql(
    """
    CREATE OR REPLACE TEMP TABLE TIMETABLE AS
    SELECT 
        * 
    FROM
        trips t
    JOIN 
        stop_times st
    ON 
        st.trip_id = t.trip_id
    JOIN 
        stops s
    ON 
        s.stop_id = st.stop_id
    """
)
# Load bus locations that are definitely in the UK

# Download one of the deduped parquet files from the archive for the same day as the timetable.
db.sql(
    """
    CREATE OR REPLACE TEMP TABLE BUS_LOCATIONS AS 
    SELECT 
        * 
    FROM 
        '../all_bus_locations_deduplicated_20260208.parquet'
    WHERE 
        (lat BETWEEN 49 AND 59)
    AND 
        (lon BETWEEN -9 AND 2.2)
    """
)
db.sql("ALTER TABLE BUS_LOCATIONS RENAME COLUMN Bearing TO 'bus_bearing';")
# Have a look at the format
db.sql("DESCRIBE BUS_LOCATIONS;")
# Make an intermediate table with the distance between the bus and the stops
db.sql("""
    CREATE OR REPLACE TEMP TABLE ALL_BUS_TO_STOP_DISTANCES AS
    SELECT 
        T.trip_id,
        stop_id,
        arrival_time as timetabled_arrival_time,
        departure_time as timetabled_departure_time,
        timestamp as real_time,
        bus_bearing,
        numeric_bearing AS stop_bearing,
        ST_Point(lat, lon) AS bus_location,
        ST_Point(stop_lat, stop_lon) AS stop_location,
        ST_Distance_Sphere(bus_location, stop_location) AS bus_to_stop_distance_metres
    FROM TIMETABLE T JOIN BUS_LOCATIONS B ON T.trip_id = B.trip_id
    ORDER BY T.trip_id, stop_id""")
# In the GTFSRT data, a -1 bearing is a NULL value, so let's make it official to stop messing up our calculations
db.sql(
    """
    UPDATE ALL_BUS_TO_STOP_DISTANCES
    SET bus_bearing = NULL
    WHERE bus_bearing = -1
    """
)
nulls = db.sql(
    "SELECT COUNT(*) FROM ALL_BUS_TO_STOP_DISTANCES WHERE bus_bearing IS NULL;"
).fetchone()[0]
not_nulls = db.sql(
    "SELECT COUNT(*) FROM ALL_BUS_TO_STOP_DISTANCES WHERE bus_bearing IS NOT NULL;"
).fetchone()[0]
print("Percentage of live bus locations with null bearings:", 100 * nulls / not_nulls)
# Only consider buses that are within +-90 degrees of their stops (must be going the right way!)
# This isn't perfect but it works fairly well.
db.sql(
    """
    CREATE OR REPLACE TEMP TABLE ALL_BUS_TO_STOP_DISTANCES_BEARINGS AS
    SELECT * FROM ALL_BUS_TO_STOP_DISTANCES
    WHERE ABS((bus_bearing - stop_bearing)) <= 90
    """
)
# Get the bus which is closest to the stop.
db.sql(
    """
    CREATE OR REPLACE TEMP TABLE BUS_TO_STOP_MIN_DISTANCE AS
    SELECT
        trip_id,
        stop_id,
        ARG_MIN(timetabled_arrival_time, bus_to_stop_distance_metres) as timetabled_arrival_time,
        ARG_MIN(timetabled_departure_time, bus_to_stop_distance_metres) as timetabled_departure_time,
        ARG_MIN(strftime(to_timestamp(real_time), '%H:%M:%S'), bus_to_stop_distance_metres) as real_time_time_of_day,
        ARG_MIN(real_time, bus_to_stop_distance_metres) as real_time_timestamp,
        ARG_MIN(bus_bearing, bus_to_stop_distance_metres) as bus_bearing,
        ARG_MIN(stop_bearing, bus_to_stop_distance_metres) as stop_bearing,
        MIN(bus_to_stop_distance_metres) as distance_to_stop
    FROM ALL_BUS_TO_STOP_DISTANCES_BEARINGS
    GROUP BY trip_id, stop_id
    ORDER BY trip_id, stop_id
    """
)
# this will probably be quicker without the order at the end
db.sql("SELECT * FROM BUS_TO_STOP_MIN_DISTANCE LIMIT 1")
print("Bus locations\n", db.sql("SELECT COUNT(*) FROM BUS_LOCATIONS"))
print("Timetable\n", db.sql("SELECT COUNT(*) FROM TIMETABLE"))
print(
    "ALL_BUS_TO_STOP_DISTANCES\n",
    db.sql("SELECT COUNT(*) FROM ALL_BUS_TO_STOP_DISTANCES"),
)
print(
    "BUS TO STOP MIN DISTANCE\n",
    db.sql("SELECT COUNT(*) FROM BUS_TO_STOP_MIN_DISTANCE"),
)
# What is the furthest distance from a bus to it's stop?!
db.sql("SELECT MAX(bus_to_stop_distance_metres) FROM ALL_BUS_TO_STOP_DISTANCES")

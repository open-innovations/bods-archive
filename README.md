# Open Innovations BODS archive tool

At Open Innovations we like buses. We like Bus Open Data. We want to be able to archive Bus Open Data. This is our prototype for creating an archive of [BODS data](https://www.bus-data.dft.gov.uk/).

Before starting to create an archive you should set an environment variable:

```bash
export BODSARCHIVE=/path/to/archive
```

You should also ensure you have a `python` environment set up for this project. To make managing that easier, we use [`pipenv`](https://pipenv.pypa.io/en/latest/). If you don't already have pipenv installed, you can do so by running:

```bash
pip install pipenv
```

Once `pipenv` is installed, you can load the environment for this project by running the following command at the root of this directory:

```bash
pipenv sync
```

This will install all the necessary packages and ensure the correct versions. You can see a full list of commands by running `pipenv -h`.

## Running the archive tools

The archive is made up of several subtasks.

### Timetable data

The timetable data for each region (in GTFS format) can be downloaded using `scripts/timetable.sh`. This will save the files in:

`${BODSARCHIVE}/timetables/YYYY/MM/DD/itm_REGION_NAME_gtfs_YYMMDD.zip`

This script can be run as a cronjob once a day. Edit cron with:

```bash
crontab -e
```

Add a cronjob:

```bash
30 02 * * * /path/to/scripts/timetable.sh
```

This will download the timetables at 2:30am each day. Note that these tend to take up roughly 1.3GB per day.

### Real-time data

The real time data for each region is downloaded every 30 seconds using `scripts/archive.sh`. This saves files of the form:

* `${BODSARCHIVE}/sirivm/YYYY/MM/DD/sirivm-YYYYMMDDTHHMMSS.zip`
* `${BODSARCHIVE}/gtfsrt/YYYY/MM/DD/gtfsrt-YYYYMMDDTHHMMSS.zip`

### Building the CSV downloads

To make the outputs easier to use in a variety of situations we create simplified CSV versions of the real-time data using:

```bash
python scripts/python/gtfsrt_to_csv.py
```

This will look for all the GTFS-RT zip files from yesterday and output a zipped CSV file in:

`${BODSARCHIVE}/csv/YYYY/csv-YYYMMDD.csv.zip`

You can also explicitly set which day's data gets processed using e.g.

```bash
pipenv run python scripts/python/gtfsrt_to_csv.py --date "2025/05/29"
```

If the output file already exists you can force it to overwrite it using the `--force` flag:

```bash
pipenv run python scripts/python/gtfsrt_to_csv.py --date "2025/05/29" --force
```

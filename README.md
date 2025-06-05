# Open Innovations BODS archive tool

At Open Innovations we like buses. We like Bus Open Data. We want to be able to archive Bus Open Data. This is our prototype for creating an archive of [BODS data](https://www.bus-data.dft.gov.uk/).

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

### Automatically

The archive is made up of several subtasks. Both should be set up using a cronjob. Edit the crontab using:

```bash
crontab -e
```
Then add the following:
```bash
BODSARCHIVE=/path/to/archive
30 02 * * * /path/to/scripts/timetable.sh
* * * * * /path/to/scripts/archive.sh
```

This will download the timetables at 2:30am each day. Note that these tend to take up roughly 1.3GB per day.

The archive script will download two files per minute.

### Manually

If you want to run the scripts manually, you should set an environment variable:

```bash
export BODSARCHIVE=/path/to/archive
```

### Timetable data

The timetable data for each region (in GTFS format) can be downloaded by running `scripts/timetable.sh`. This will save the files in:

`${BODSARCHIVE}/timetables/YYYY/MM/DD/itm_REGION_NAME_gtfs_YYMMDD.zip`


### Real-time data

The real time data for each region is downloaded by running `scripts/archive.sh`. This saves files of the form:

* `${BODSARCHIVE}/sirivm/YYYY/MM/DD/sirivm-YYYYMMDDTHHMMSS.zip`
* `${BODSARCHIVE}/gtfsrt/YYYY/MM/DD/gtfsrt-YYYYMMDDTHHMMSS.zip`

Running this will save two files for both gtfsrt and sirivm, 30s apart. This is because we use the same script for cronjob (see above).

### Building the CSV downloads

To make the outputs easier to use in a variety of situations we create simplified (de-duplicated and rounded) CSV versions of the real-time data using:

```bash
pipenv run python scripts/python/gtfsrt_to_csv.py
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

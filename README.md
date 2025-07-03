# Open Innovations BODS archive tool

At Open Innovations we like buses. We like Bus Open Data. We want to be able to archive Bus Open Data. This is our prototype for creating an archive of [BODS data](https://www.bus-data.dft.gov.uk/).

## Python environment

You should also ensure you have a `python` environment set up for this project. To make managing that easier, we use [`pipenv`](https://pipenv.pypa.io/en/latest/). If you don't already have pipenv installed, you can do so by running:

```bash
pip install pipenv
```

Once `pipenv` is installed, you can load the environment for this project by running the following command at the root of this directory:

```bash
pipenv sync
```

When running Python scripts, you should do so inside a pipenv shell, which you can load by running:

```bash
pipenv shell
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

### Archive Downloader Script

#### Overview

The Archive Downloader script is a Python program designed to download `gtfsrt` or `sirivm` bus location data files from a the BODS archive based on user-defined date ranges.

#### Requirements

Make sure you follow the steps to set-up your [Python environment](#python-environment).

#### Usage

To run the script, you need to provide several command-line arguments. Here’s how to use it:

#### Command-Line Arguments

* `-s`, `--sd`: Start date in the format `YYYY/mm/dd`. Default is `2025/07/01`.
* `-e`, `--ed`: End date in the format `YYYY/mm/dd`. Default is `2025/07/01`.
* `-f`, `--format`: Data format to download. Options are `gtfsrt` or `sirivm`. Default is `gtfsrt`.
* `-o`, `--outpath`: Output directory to store downloaded files, relative to the current working directory. Default is `data`.

#### Example Command

To download data from July 1, 2025, to July 3, 2025, in the `gtfsrt` format and save it in a folder named `downloads`, you would run:

```bash
python archive_downloader.py -s 2025/07/01 -e 2025/07/03 -f gtfsrt -o downloads
```

#### Important Notes

* The script only downloads files that match the naming pattern `format-YYYYMMDDTHHMMSS.zip`.
* If a link does not match the expected format or is not a zip file, it will be skipped with a printed message.
* The script will print status messages for each link processed, including any errors encountered during the download process.

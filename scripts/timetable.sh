#!/bin/bash

regions=("yorkshire" "west_midlands" "wales" "south_west" "south_east" "scotland" "north_east" "north_west" "london" "east_midlands" "east_anglia")

for i in "${regions[@]}"; do

  url="https://data.bus-data.dft.gov.uk/timetable/download/gtfs-file/$i/"

  # Set the output directory - we explicitly work it out again in case we happen to have moved onto the next day since the start
  dir="${BODSARCHIVE}/timetables/$(TZ=UTC date +"%Y/%m/%d")"

  # Let's explicitly create the directory if it doen't exist
  if [ ! -d "$dir" ]; then
    # Create directory and set permissions
    echo -e "Making \e[36m$dir\e[0m"
    mkdir -p $dir
    chmod 755 $dir
  fi


  file="${dir}/itm_"$i"_gtfs_$(date +"%Y%m%d").zip"

  # Now save the file if we don't already have it
  if [[ -e "$file" ]]; then
    echo -e "File \e[36m$file\e[0m exists"
  else 
    curl "$url" -s --create-dirs -o "$file"
    chmod 0755 "$file"
  fi

done

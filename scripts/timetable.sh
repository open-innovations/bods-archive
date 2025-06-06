#!/bin/bash
regions=("yorkshire" "west_midlands" "wales" "south_west" "south_east" "scotland" "north_east" "north_west" "london" "east_midlands" "east_anglia")
for i in "${regions[@]}"; do
  url="https://data.bus-data.dft.gov.uk/timetable/download/gtfs-file/$i/"
  file="${BODSARCHIVE}/timetables/$(date +"%Y")/$(date +"%m")/$(date +"%d")/itm_"$i"_gtfs_$(date +"%Y%m%d").zip"
  if [[ -e "$file" ]]; then
    echo "file exists"
  else 
    curl "$url" -s --create-dirs -o "$file"
  fi
done

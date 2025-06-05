#!/bin/bash
v=0
while [ $v -lt 2 ];
do 
curl "https://data.bus-data.dft.gov.uk/avl/download/gtfsrt" -s --create-dirs -o "${BODSARCHIVE}/gtfsrt/$(date +"%Y")/$(date +"%m")/$(date +"%d")/gtfsrt-$(date +"%Y%m%dT%H%M%S.zip")";
curl "https://data.bus-data.dft.gov.uk/avl/download/bulk_archive" -s --create-dirs -o "${BODSARCHIVE}/sirivm/$(date +"%Y")/$(date +"%m")/$(date +"%d")/sirivm-$(date +"%Y%m%dT%H%M%S.zip")";
if [ $v -eq 0 ]; then
    sleep 30
fi
((v++))
done
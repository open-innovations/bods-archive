#!/bin/bash
v=0
while [ $v -lt 2 ];
do
gtfsrt="${BODSARCHIVE}/gtfsrt/$(TZ=UTC date +"%Y")/$(TZ=UTC date +"%m")/$(TZ=UTC date +"%d")/gtfsrt-$(TZ=UTC date +"%Y%m%dT%H%M%S.zip")"
sirivm="${BODSARCHIVE}/sirivm/$(TZ=UTC date +"%Y")/$(TZ=UTC date +"%m")/$(TZ=UTC date +"%d")/sirivm-$(TZ=UTC date +"%Y%m%dT%H%M%S.zip")"
curl "https://data.bus-data.dft.gov.uk/avl/download/gtfsrt" -s --create-dirs -o $gtfsrt && chmod 0775 $gtfsrt;
curl "https://data.bus-data.dft.gov.uk/avl/download/bulk_archive" -s --create-dirs -o $sirivm && chmod 0775 $sirivm;
if [ $v -eq 0 ]; then
    sleep 30
fi
((v++))
done

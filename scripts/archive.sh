while true;
do 
curl "https://data.bus-data.dft.gov.uk/avl/download/gtfsrt" -s --create-dirs -o "gtfsrt/$(date +"%Y")/$(date +"%m")/$(date +"%d")/gtfsrt-$(date +"%Y%m%dT%H%M%S.zip")";
curl "https://data.bus-data.dft.gov.uk/avl/download/bulk_archive" -s --create-dirs -o "sirivm/$(date +"%Y")/$(date +"%m")/$(date +"%d")/sirivm-$(date +"%Y%m%dT%H%M%S.zip")";
sleep 30
done
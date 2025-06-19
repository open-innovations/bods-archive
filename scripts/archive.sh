#!/bin/bash
v=0
types=("gtfsrt" "sirivm")
urls=("https://data.bus-data.dft.gov.uk/avl/download/gtfsrt" "https://data.bus-data.dft.gov.uk/avl/download/bulk_archive")
length=${#types[@]}
while [ $v -lt 2 ];
do
	# Get start time
	start=`date +%s`
	# Build the date part of the directory string
	dtdir="$(TZ=UTC date +"%Y/%m/%d")"
	# Loop over the types
	for (( j=0; j<${length}; j++ ));
	do
		dir="${BODSARCHIVE}/${types[$j]}/$dtdir"
		if [ ! -d "$dir" ]; then
			# Create directory and set permissions
			mkdir -p $dir
			chmod 755 $dir
		fi
		# Download file
		curl "${urls[$j]}" -s --create-dirs -o "$dir/${types[$j]}-$(TZ=UTC date +"%Y%m%dT%H%M%S.zip")" && chmod 0755 "${_}";
	done
	# Get end time
	end=`date +%s`
	# Calculate the time to sleep for (30s - time taken)
	wait=$((30-$((end-start))))
	if [ $v -eq 0 ]; then
		sleep $wait
	fi
	((v++))
done

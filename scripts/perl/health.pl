#!/usr/bin/perl

use strict;
use warnings;
use Data::Dumper;
use utf8;
binmode STDOUT, 'utf8';
binmode STDERR, 'utf8';
use Cwd qw(abs_path);
use POSIX qw(strftime);
my ($basedir, $path);
BEGIN { ($basedir, $path) = abs_path($0) =~ m{(.*/)?([^/]+)$}; push @INC, $basedir; }
use lib $basedir."lib/";	# Custom functions
use OpenInnovations::CalendarChart;

require "lib.pl";


my (@rows,$chart,$types,$type,$dir,@dirs,$d,$count,$webdir,$fh,$svg,$dt,$dt2,$file,$bytesh,$bytes,$df,$dayfile,$pattern,$dtiso,$today,$row,@files,$f,$total,$dirlink);

$webdir = $ARGV[0]||"/var/www/data.datalibrary.uk/resources/images/";
$types = {
	'gtfsrt'=>{'keep_days'=>60},
	'sirivm'=>{'keep_days'=>60},
	'timetables'=>{'filepattern'=>'*_gtfs_[0-9]*.zip'}
};

$today = $dt = strftime("%Y%m%d", gmtime());


$df = `df -B1 /`;
if($df =~ /([0-9]+)[\t\s]([0-9]+)[\t\s]([0-9]+)[\s\t]+[0-9\.]+\% \/[\n\r]/s){
	$df = sprintf("%0d days",($3/(2*90e9/7)));
	open($fh,">",$ENV{'BODSARCHIVE'}.($ENV{'BODSARCHIVE'} =~ /\/$/ ? '':'/')."free.txt");
	print $fh $df;
	close($fh);
}

# Build directory index for each type
foreach $type (sort(keys(%{$types}))){
	@rows = ();
	msg("Type: <green>$type<none>\n");
	$dir = $ENV{'BODSARCHIVE'}.($ENV{'BODSARCHIVE'} =~ /\/$/ ? '':'/').$type;

	if(defined($types->{$type}{'keep_days'})){ $types->{$type}{'recent'} = strftime("%Y%m%d", gmtime(time - 86400*$types->{$type}{'keep_days'})); }

	# Save total size
	$bytes = `du -sb $dir`;
	$bytes =~ s/\s+.*//s;
	$bytesh = humanBytes($bytes);
	$file = $dir."/total-bytes.txt";
	msg("Save <yellow>$type<none> size (<green>$bytesh<none>) to <cyan>$file<none>\n");
	open($fh,">",$file);
	print $fh $bytesh;
	close($fh);

	# Get all the directories that exist for this type
	@dirs = sort(`find $dir -maxdepth 3`);
	for($d = 0; $d < @dirs; $d++){
		if($dirs[$d] =~ /([0-9]{4})\/([0-9]{2})\/([0-9]{2})/){

			$dt = "$1-$2-$3";
			$dt2 = "$1/$2/$3";
			$dtiso = "$1$2$3";
			$dayfile = $dir."/".$dt2."/".$type."-".$dtiso.".zip";

			# Define a pattern to match the 10s zip files 
			$pattern = "$dir/$dt2/".(defined($types->{$type}{'filepattern'}) ? $types->{$type}{'filepattern'} : "$type-$dtiso"."T*.zip");

			# Create an archive zip if it doesn't yet exist
			if(!-e $dayfile && $dtiso lt $today){
				msg("Create zip archive for <green>$dt<none>\n");
				`zip $dayfile $dir/$dt2/*.zip`;
			}

			# Count the number of zip files (but not including the daily one)
			$count = `find $pattern 2> /dev/null | wc -l`;
			$count =~ s/(^[\n\r]|[\n\r]$)//sg;

			if($count > 0){
				if($types->{$type}{'recent'} && $dtiso lt $types->{$type}{'recent'}){
					msg("Removing $pattern ($count)\n");
					`rm $pattern`;
				}
			}
			if($count == 0 && -e $dayfile){
				$count = `zipinfo $dayfile |grep ^-|wc -l`;
				$count += 0;
				$dirlink = "";
			}else{
				$dirlink = "<a href=\"$dt2/\">Directory</a>";
			}
			if(-e $dayfile){
				# Get the bytes for this day's full zip
				$bytes = `du -sb $dayfile`;
				$bytes =~ s/\s+.*//s;
			}else{
				$bytes = 0;
			}
			$bytesh = humanBytes($bytes);

			# Build the row
			$row = {'date'=>$dt,'files'=>$count,'value'=>addCommas($count),'bytes'=>$bytes,'byteshuman'=>$bytesh,'links'=>''};
			if($dirlink){
				$row->{'links'} = $dirlink;
			}
			if(-e $dayfile && $dtiso lt $today){
				$row->{'links'} .= ($row->{'links'} ? "\n":"")."<a href=\"$dt2/$type-$dtiso.zip\">Download day</a> (<span class=\"size\">{{ byteshuman }}</span>)";
			}

			# Add to the rows for the calendar chart
			push(@rows,$row);
		}
	}

	if(-d $webdir){
		# Create a chart based on files
		$chart = OpenInnovations::CalendarChart->new();
		$chart->set({
			'data'=>\@rows,
			'key'=>'date',
			'value'=>'files',
			'order'=>'reverse',
			'tooltip'=>"<strong>%d %B %Y</strong>\nFiles: <strong>{{ value }}</strong>\n{{ links }}"
		});
		$svg = $chart->build();
		$file = $webdir.$type."-files.svg";
		msg("Save SVG <cyan>$file<none>\n");
		open($fh,">",$file);
		print $fh $svg;
		close($fh);

		# Create a chart based on bytes
		$chart = OpenInnovations::CalendarChart->new();
		$chart->set({
			'data'=>\@rows,
			'key'=>'date',
			'value'=>'bytes',
			'order'=>'reverse',
			'tooltip'=>"<strong>%d %B %Y</strong>\nFiles: <strong>{{ files }}</strong>\n{{ links }}"
		});
		$svg = $chart->build();
		$file = $webdir.$type."-bytes.svg";
		msg("Save SVG <cyan>$file<none>\n");
		open($fh,">",$file);
		print $fh $svg;
		close($fh);
	}
}

sub humanBytes {
	my $bytes = shift;
	if($bytes eq ""){ return "0"; }
	if($bytes > 1e12){ return sprintf("%0.2f TB",$bytes/1e12); }
	if($bytes > 1e9){ return sprintf("%0.2f GB",$bytes/1e9); }
	if($bytes > 1e6){ return sprintf("%0.1f MB",$bytes/1e6); }
	if($bytes > 1e3){ return sprintf("%0.1f kB",$bytes/1e3); }
	return $bytes;
}

sub addCommas {
	my $a = shift;
	my $b = reverse $a;               # $b = '87654321';
	my @c = unpack("(A3)*", $b);      # $c = ('876', '543', '21');
	my $d = join ',', @c;             # $d = '876,543,21';
	my $e = reverse $d;
	return $e;
}


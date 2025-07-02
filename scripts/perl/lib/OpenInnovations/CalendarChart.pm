# Version 0.1
package OpenInnovations::CalendarChart;

use strict;
use warnings;
use Data::Dumper;
use List::Util qw[min max];
use Scalar::Util qw(looks_like_number);
use DateTime;
use OpenInnovations::ColourScale;


sub new {
    my ($class, %args) = @_;
 
    my $self = \%args;
 
    bless $self, $class;
 
    return $self;
}

sub set {
	my ($self, $input) = @_;
	if(!defined($input)){
		error("No input provided for CalendarChart::set()\n");
	}

	$self->{'config'} = $input;
	if(!defined($input->{'defaultbg'})){ $input->{'defaultbg'} = "#efefef"; }
	return $self;
}

sub build {
	my $self = shift;

	my ($r,@rows,$d,$v,$key,$value,$min,$max,$minDate,$maxDate,$input,$days,$year,$i);
	$input = $self->{'config'};
	$key = $input->{'key'};
	$value = $input->{'value'};
	@rows = @{$input->{'data'}};
	$min = 1e100;
	$max = -1e100;
	$minDate = "3000-01-01";
	$maxDate = "0000-01-01";
	$days = {};
	for($r = 0; $r < @rows; $r++){
		# Expand min/max if the day field is a well-formatted string
		if(looks_like_date($rows[$r]{$key})){
			$d = $rows[$r]{$key};
			if($d lt $minDate){ $minDate = $d; }
			if($d gt $maxDate){ $maxDate = $d; }
		}else{
			warning("Value for '$key' in row $r doesn't look like 0000-00-00\n");
			print Dumper $rows[$r]{$key};
		}
		# Expand value min/max if the value field is a number 
		if(looks_like_number($rows[$r]{$value})){
			$v = $rows[$r]{$value};
			$min = min($min,$v);
			$max = max($max,$v);
			if(looks_like_date($d)){ $days->{$d} = $rows[$r]; }
		}
	}
	if(defined($input->{'min'}) && looks_like_number($input->{'min'})){ $min = $input->{'min'}; }
	if(defined($input->{'max'}) && looks_like_number($input->{'max'}||"")){ $max = $input->{'max'}; }

	if(looks_like_date($input->{'minDate'})){ $minDate = $input->{'minDate'}; }
	if(looks_like_date($input->{'maxDate'})){ $maxDate = $input->{'maxDate'}; }

	my $range = {
		'min'=>{ 'date'=>$minDate },
		'max'=>{ 'date'=>$maxDate }
	};
	if($minDate =~ /^([0-9]{4})/){ $range->{'min'}{'year'} = $1; }
	if($maxDate =~ /^([0-9]{4})/){ $range->{'max'}{'year'} = $1; }

	my $w = $input->{'width'}||1080;
	my $size = $w/56;
	my $space = $size*2;
	my $yr = ($range->{'max'}{'year'} - $range->{'min'}{'year'}) + 1;
	my $h = ($size*7)*$yr + ($yr > 0 ? $space*($yr-1) : 0);

	my $svg = '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" viewBox="0 0 '.sprintf("%.2f", $w).' '.sprintf("%.2f", $h).'" vector-effect="non-scaling-stroke" preserveAspectRatio="xMidYMin meet" overflow="visible" data-type="calendar-chart">';
	my $x = 0;
	my $y = 0;


	my $props = {
		'days'=>$days,
		'min'=>$min,
		'max'=>$max,
		'width'=>$w,
		'height'=>$h,
		'size'=>sprintf("%0.2f",$size),
		'origin'=>{'x'=>$x},
		'startofweek'=>(looks_like_number($input->{'startofweek'}) ? $input->{'startofweek'} : 1),
		'scale'=>$input->{'scale'}||"Viridis"
	};

	if(!defined($input->{'order'})){ $input->{'order'} = "chronological"; }

	$svg .= "<g class=\"data-layer\" role=\"table\">\n";
	if($input->{'order'} eq "reverse"){
		# For each year (starting at the lowest year)
		for($year = $range->{'max'}{'year'}, $i = 0; $year >= $range->{'min'}{'year'}; $year--, $i++){
			$y = ($size*7 + $space)*$i;
			$props->{'origin'}{'y'} = $y;
			$svg .= "\t<g class=\"year\" role=\"row\" aria-label=\"Year: $year\">\n";
			$svg .= buildYear($year,$props,$input);
			$svg .= "\t</g>\n";
		}
	}elsif($input->{'order'} eq "chronological"){
		# For each year (starting at the lowest year)
		for($year = $range->{'min'}{'year'}, $i = 0; $year <= $range->{'max'}{'year'}; $year++, $i++){
			$y = ($size*7 + $space)*$i;
			$props->{'origin'}{'y'} = $y;
			$svg .= "\t<g class=\"year\" role=\"row\" aria-label=\"Year: $year\">\n";
			$svg .= buildYear($year,$props,$input);
			$svg .= "\t</g>\n";
		}
	}
	$svg .= "</g>\n";
	$svg .= "</svg>\n";

	return $svg;
}
#

sub buildYear {
	my ($year, $opts, $input) = @_;
	
	my ($i,$x,$y,$iso,$svg,$v,$d,$sday,$eday,$syear,$eyear,$offx,$offy,$dat,$cells,$dx,$dy,$ncols,$nrows,$pos,$colour,$tooltip,$dur,$cs,@days,$pc,$mkey,$replace);

	if($year =~ /^([0-9]{4})/){ $syear = DateTime->new( year => $1, month => 1, day => 1 ); $eyear = DateTime->new( year => $1, month => 12, day => 31 ); }

	$sday = floorWeek($syear->clone,$opts->{'startofweek'});
	$eday = ceilWeek($eyear->clone,$opts->{'startofweek'});

	$x = sprintf("%0.2f",$opts->{'origin'}{'x'} + $opts->{'size'});
	$y = sprintf("%0.2f",$opts->{'origin'}{'y'} + 3.5*$opts->{'size'});
	$svg = "\t\t<text class=\"year\" x=\"$x\" y=\"$y\" transform=\"rotate(-90)\" transform-origin=\"$x $y\" text-anchor=\"middle\" font-size=\"".sprintf("%0.2f",$opts->{'size'}*1.5)."\" font-family=\"\" dominant-baseline=\"middle\">$year</text>";

	$dur = $sday->delta_days($eday);
	$ncols = int(0.5 + ($dur->in_units('days')/7));
	$nrows = 7;

	$dx = ($ncols*$opts->{'size'});
	$dy = ($nrows*$opts->{'size'});

	$d = $sday->clone;
	@days = ('S','M','T','W','T','F','S','S');
	for($i = 0; $i < 7; $i++){
		$x = sprintf("%0.2f",$opts->{'origin'}{'x'} + 2.5*$opts->{'size'});
		$y = sprintf("%0.2f",$opts->{'origin'}{'y'} + ($i + 0.5)*$opts->{'size'});
		$svg .= "\t\t<text class=\"day\" x=\"$x\" y=\"$y\" dominant-baseline=\"middle\" text-anchor=\"middle\" font-size=\"".sprintf("%0.2f",$opts->{'size'}*0.75)."\" font-family=\"\">$days[$d->day_of_week]</text>\n";
		$d->add( days => 1 );
	}

	$d = $sday->clone;

	$cs = OpenInnovations::ColourScale->new(scale=>$opts->{'scale'},empty=>$input->{'defaultbg'});

	while($d <= $eday){

		$iso = "";
		if($d->iso8601 =~ /([0-9]{4}-[0-9]{2}-[0-9]{2})/){
			$iso = $1;
		}
		$dat = {};
		if(defined($opts->{'days'}{$iso})){
			$dat = $opts->{'days'}{$iso};
		}

		$v = "";
		$colour = $input->{'defaultbg'}||"";
		if($d >= $syear && $d <= $eyear){
			if(defined($dat->{$input->{'value'}})){
				$v = $dat->{$input->{'value'}};
				if(looks_like_number($v)){
					if($opts->{'max'} == $opts->{'min'}){
						$pc = 1;
					}else{
						$pc = ($v - $opts->{'min'})/($opts->{'max'} - $opts->{'min'});
					}
					$colour = $cs->getColour($pc);
				}
			}
		}else{
			$colour = "transparent";
		}
	
		$pos = getXY($d,$sday,$opts);
		
		my $tooltip = ($input->{'tooltip'}||"%d %b %Y\n{{ value }}")."";
		$tooltip = $d->strftime($tooltip);

		while($tooltip =~ /\{\{ *([^\}]+?) *\}\}/){
			$mkey = $1;
			$replace = (defined($dat->{$mkey}) ? $dat->{$mkey} : "");
			$tooltip =~ s/\{\{ *$mkey *\}\}/$replace/sg;
		}

		$svg .= "\t\t<rect class=\"".($d >= $syear && $d <= $eyear ? "in-year" : "not-in-year").($tooltip ? " has-value" : "")."\"";
		if(defined($input->{'tooltip'}) && defined($dat) && defined($dat->{$input->{'tooltip'}})){ $svg .= ' '; }
		if($colour){ $svg .= " fill=\"$colour\""; }
		$svg .= " role=\"cell\"";
		$svg .= " x=\"$pos->{'x'}\" y=\"$pos->{'y'}\" width=\"$opts->{'size'}\" height=\"$opts->{'size'}\">";
		if($tooltip){ $svg .= "<title>$tooltip</title>"; }
		$svg .= "</rect>\n";

		# Increment day
		$d->add( days => 1 );
	}

	# Build outline
	#$svg .= '<path class="marker-group outline" d="'.cells.getBoundary(opts.size,0,opts.origin.x + 3*opts.size,opts.origin.y)+'" fill="transparent"></path>';

	return $svg;
}

sub getXY {
	my ($d,$sday,$opts) = @_;
	my ($offx,$offy,$x,$y);

	$offx = int($d->delta_days($sday)->in_units('days')/7);
	$offy = ($d->day_of_week - $opts->{'startofweek'});
	if($offy < 0){ $offy += 7; }
	if($offy >= 7){ $offy -= 7; }

	$x = sprintf("%0.2f",$opts->{'origin'}{'x'} + (3*$opts->{'size'}) + $offx*$opts->{'size'});
	$y = sprintf("%0.2f",$opts->{'origin'}{'y'} + $offy*$opts->{'size'});
	
	return {'x'=>$x,'y'=>$y};
}

sub floorWeek {
	my ($dt, $firstdayofweek) = @_;
	if(!defined($firstdayofweek)){ $firstdayofweek = 1; }
	my ($diff,$newday,$day);
	$diff = 0;
	$day = $dt->day_of_week;	# Monday = 1, Sunday = 7
	# Change to Sunday = 0
	if($day == 7){ $day = 0; }
	if($day > $firstdayofweek){ $diff = $firstdayofweek - $day; }
	elsif($day < $firstdayofweek){ $diff = -($day + 7 - $firstdayofweek); }
	return $dt->add( days => $diff );
}


sub ceilWeek {
	my ($dt, $firstdayofweek) = @_;
	if(!defined($firstdayofweek)){ $firstdayofweek = 1; }
	my ($diff,$newday,$day);
	$diff = 0;
	$day = $dt->day_of_week;	# Monday = 1, Sunday = 7
	# Change to Sunday = 0
	if($day == 7){ $day = 0; }
	if($day > $firstdayofweek){ $diff = 7 - ($day - $firstdayofweek); }
	elsif($day == $firstdayofweek){ $diff = 7; }
	elsif($day < $firstdayofweek){ $diff = 7 - ($firstdayofweek - $day); }
	$diff--;
	return $dt->add( days => $diff );
}

sub isoToDate {
	my $d = shift||"";
	if($d =~ /^([0-9]{4})\-([0-9]{2})\-([0-9]{2})/){
		return DateTime->new( year => $1, month => int($2), day => int($3) );
	}else{
		warning("Can't parse date <yellow>$d<none>.\n");
	}
}

sub looks_like_date {
	my $d = shift||"";
	return ($d =~ /^[0-9]{4}\-[0-9]{2}\-[0-9]{2}/);
}
sub len {
	my ($self, $v) = @_;
	$self->{'len'} = $v;
	return $v;
}

1;

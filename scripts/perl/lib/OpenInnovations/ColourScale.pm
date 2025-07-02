# Version 0.1
package OpenInnovations::ColourScale;

use strict;
use warnings;
use Data::Dumper;
use DateTime;
use Scalar::Util qw(looks_like_number);


sub new {
    my ($class, %args) = @_;
 
    my $self = \%args;
 
    bless $self, $class;

	$self->{'namedColourScales'} = {
		'Viridis'=>'#440154 0%, #482878 11.1%, #3e4989 22.2%, #31688e 33.333%, #26828e 44.444%, #1f9e89 55.555%, #35b779 66.666%, #6ece58 77.777%, #b5de2b 88.888%, #fde725 100%',
		'Viridis-light'=>'rgb(122,76,139) 0%, rgb(124,109,168) 12.5%, rgb(115,138,177) 25%, rgb(107,164,178) 37.5%, rgb(104,188,170) 50%, rgb(133,211,146) 62.5%, rgb(189,229,97) 75%, rgb(254,240,65) 87.5%, rgb(254,240,65) 100%',
		'Cividis'=>'#00224e 0%, #123570 11.1%, #3b496c 22.222%, #575d6d 33.333%, #707173 44.444%, #8a8678 55.555%, #a59c74 66.666%, #c3b369 77.777%, #e1cc55 88.888%, #fee838 100%',
		'Heat'=>'rgb(0,0,0) 0%, rgb(128,0,0) 25%, rgb(255,128,0) 50%, rgb(255,255,128) 75%, rgb(255,255,255) 100%',
		'Inferno'=>'#000004 0%, #1b0c41 11.1%, #4a0c6b 22.222%, #781c6d 33.333%, #a52c60 44.444%, #cf4446 55.555%, #ed6925 66.666%, #fb9b06 77.777%, #f7d13d 88.888%, #fcffa4 100%',
		'Magma'=>'#000004 0%, #180f3d 11.1%, #440f76 22.222%, #721f81 33.333%, #9e2f7f 44.444%, #cd4071 55.555%, #f1605d 66.666%, #fd9668 77.777%, #feca8d 88.888%, #fcfdbf 100%',
		'Mako'=>'#0B0405 0%, #357BA2 50%, #DEF5E5 100%',
		'Planck'=>'rgb(0,0,255) 0%, rgb(0,112,255) 16.666%, rgb(0,221,255) 33.3333%, rgb(255,237,217) 50%, rgb(255,180,0) 66.666%, rgb(255,75,0) 100%',
		'Plasma'=>'#0d0887 0%, #46039f 11.1%, #7201a8 22.222%, #9c179e 33.333%, #bd3786 44.444%, #d8576b 55.555%, #ed7953 66.666%, #fb9f3a 77.777%, #fdca26 88.888%, #f0f921 100%',
		'Rocket'=>'#03051A 0%, #CB1B4F 50%, #FAEBDD 100%',	
		'Turbo'=>'#30123b 0%, #4145ab 7.143%, #4675ed 14.286%, #39a2fc 21.429%, #1bcfd4 28.571%, #24eca6 35.714%, #61fc6c 42.857%, #a4fc3b 50%, #d1e834 57.143%, #f3c63a 64.286%, #fe9b2d 71.429%, #f36315 78.571%, #d93806 85.714%, #b11901 92.857%, #7a0402 100%',
		'PiPG'=>'#8e0152 0%, #c51b7d 10%, #de77ae 20%, #f1b6da 30%, #fde0ef 40%, #f7f7f7 50%, #e6f5d0 60%, #b8e186 70%, #7fbc41 80%, #4d9221 90%, #276419 100%',
		'PRGn'=>'#40004b 0%, #762a83 10%, #9970ab 20%, #c2a5cf 30%, #e7d4e8 40%, #f7f7f7 50%, #d9f0d3 60%, #a6dba0 70%, #5aae61 80%, #1b7837 90%, #00441b 100%',
		'PuOr'=>'#7f3b08 0%, #b35806 10%, #e08214 20%, #fdb863 30%, #fee0b6 40%, #f7f7f7 50%, #d8daeb 60%, #b2abd2 70%, #8073ac 80%, #542788 90%, #2d004b 100%',
		'RdBu'=>'#67001f 0%, #b2182b 10%, #d6604d 20%, #f4a582 30%, #fddbc7 40%, #f7f7f7 50%, #d1e5f0 60%, #92c5de 70%, #4393c3 80%, #2166ac 90%, #053061 100%',
	};

	$self->{'colourscales'} = {};
	if(!defined($self->{'empty'})){ $self->{'empty'} = "#dfdfdf"; }
	
	my (@cs,$i,$gradient);
	foreach my $scale (keys(%{$self->{'namedColourScales'}})){
		$gradient = $self->{'namedColourScales'}{$scale};
		$self->{'colourscales'}{$scale} = {
			'orig'=>$gradient,
			'gradient'=> "background: -moz-linear-gradient(left, $gradient);background: -webkit-linear-gradient(left, $gradient);background: linear-gradient(to right, $gradient);",
			'stops'=>[]
		};
	}

	if(defined($self->{'scale'})){
		$self->set($self->{'scale'});
	}

    return $self;
}

sub set {
	my ($self, $scale) = @_;
	if(defined($scale)){
		if(defined($self->{'namedColourScales'}{$scale})){
			$self->{'scale'} = $scale;
			if(@{$self->{'colourscales'}{$scale}{'stops'}}==0){
				my @cs = extractColours($self->{'namedColourScales'}{$scale});
				my $maxidx = @cs - 1;
				for(my $i = 0; $i < @cs; $i++){
					push(@{$self->{'colourscales'}{$scale}{'stops'}},$cs[$i]);

					if($cs[$i]{'v'} == 100){
						$maxidx = $i;
						$i = @cs;
					}
				}
				$self->{'colourscales'}{$scale}{'maxidx'} = $maxidx;
			}
			return $self;
		}
	}
	print "No colour scale named: \"".($scale||"")."\"\n";
	return $self;
}

sub getColour {
	my ($self, $v) = @_;

	if(!defined($self->{'scale'})){
		print "Error: No colour scale defined yet\n";
		return 
	}

	my ($cs,@stops,$min,$max,$gradient,$maxidx,$i,$v2,$j,$cfinal,$c,$pc);
	$cs = $self->{'colourscales'}{$self->{'scale'}};
	@stops = @{$cs->{'stops'}};
	$min = 0;
	$max = 1;
	$gradient = $cs->{'orig'};
	$v2 = 100 * ($v - $min) / ($max - $min);
	$cfinal = {};
	$maxidx = $cs->{'maxidx'};

	if(@stops == 1){
		$cfinal = {
			"r" => $stops[0]{'rgb'}{'r'},
			"g" => $stops[0]{'rgb'}{'g'},
			"b" => $stops[0]{'rgb'}{'b'},
			"alpha" => sprintf("%0.3f",($v2 / 100))
		};
	}else{
		if($v == $max){
			$cfinal = $stops[$maxidx]{'rgb'};
		}else{
			# Is the value greater than our scale?
			if($v2 > $stops[@stops-1]{'v'}){
				$j = @stops-1;
				$cfinal = $stops[$j]{'rgb'};
			}else{
				for($c = 0; $c < @stops - 1; $c++){
					if ($v2 >= $stops[$c]{'v'}){
						if ($c < @stops-1){
							if ($v2 <= $stops[$c + 1]{'v'}) {
								# On this colour stop
								$pc = 100 * ($v2 - $stops[$c]{'v'}) / ($stops[$c + 1]{'v'} - $stops[$c]{'v'});
								$cfinal = getColourPercent($pc, $stops[$c]{'rgb'}, $stops[$c + 1]{'rgb'});
								last;
							}
						} else {
							$cfinal = $stops[@stops-1]{'rgb'};
							last;
						}
					}
				}
			}
		}
	}
	# If no red value is set and the value is greater than the max value, we'll default to the max colour
	if (!looks_like_number($cfinal->{'r'}) && $v > $max){
		$cfinal = $stops[@stops - 1]{'rgb'};
	}
	return "rgba($cfinal->{'r'},$cfinal->{'g'},$cfinal->{'b'},$cfinal->{'alpha'})";
}

sub getColourPercent {
	my ($pc,$a,$b) = @_;

	$pc /= 100;
	if(!looks_like_number($a->{'alpha'})){
		$a->{'alpha'} = 1;
	}
	if(!looks_like_number($b->{'alpha'})){
		$b->{'alpha'} = 1;
	}
	return {
		"r"=>($a->{'r'} + ($b->{'r'} - $a->{'r'}) * $pc),
		"g"=>($a->{'g'} + ($b->{'g'} - $a->{'g'}) * $pc),
		"b"=>($a->{'b'} + ($b->{'b'} - $a->{'b'}) * $pc),
		"alpha"=>(($b->{'alpha'} - $a->{'alpha'}) * $pc + $a->{'alpha'}),
	};
}

sub extractColours {
	my $gradient = shift;
	my (@cs,$v,$aspercent,$p1,$i,@stops,$num);
	@stops = ();
	@cs = ();
	while($gradient =~ s/(([a-z]{3,4}\([^\)]+\)|#[A-Fa-f0-9]{6}) [0-9\.]+\%?)//){
		push(@stops,$1);
	}
	if(@stops == 0){
		print "Error: Can't parse gradient string \"$gradient\"\n";
		exit;
	}
	for($i = 0; $i < @stops; $i++){
		$v = 1e100;
		$aspercent = 0;
		if($stops[$i] =~ s/ ([0-9\.]+\%?)$//){
			$p1 = $1;
			if($p1 =~ "%"){ $aspercent = 1; }
			$v = $p1;
			$v =~ s/[^0-9\.\-\+]//g;
		}
		$num = {v=>$v,c=>$stops[$i],aspercent=>$aspercent};
		if($stops[$i] =~ /^\#[A-Fa-f0-9]{6}$/){ $num->{'rgb'} = hexToRGB(uc($stops[$i])); }
		push(@cs,$num);
	}
	return @cs;
}

sub hexToRGB {
	my $c = shift;	
	return {
		r=>hex(substr($c,1,2)),
		g=>hex(substr($c,3,2)),
		b=>hex(substr($c,5,2)),
		alpha=>1
	};
}
1;
#!/bin/bash
#
# Construction of a "GPS essentials" file which everyone should have.
# It is intended to contain:
# - entrances
# - main walking routes
# - other notable features (e.g. ski route markers).

set -eu -o pipefail

root=$(hg showconfig | grep mainreporoot | sed 's/[^=]*=//')
cd $root/gpx/gpx_publish

all=$root/1623-and-1626-no-schoenberg-hs.3d
kataster_boundaries=$root/kataster/kataster-boundaries-lukas-plan-2018-07-17/kataster-boundaries.3d

echo
echo "This script assumes that ${all} is up to date."
echo "If that is not the case, process the corresponding .svx file,"
echo "then re-run this script."
echo

output=essentials.gpx

entrances=entrances.gpx

sb_to_balkon=stone-bridge-to-balkon.gpx
sb_to_fisch=stone-bridge-to-fischgesicht.gpx
fisch_to_hc=fischgesicht-to-homecoming.gpx
sb_to_car_park=stone-bridge-to-car-park.gpx
balkon_to_organ=balkon-to-organhoehle.gpx

survexport --gpx --entrances \
  $all $entrances

survexport --gpx --surface-legs \
  --survey=stone-bridge-to-balkon_aday-2018-07-12 \
  $all $sb_to_balkon

survexport --gpx --surface-legs \
  --survey=stone-bridge-to-fischgesicht_aday-2018-07-12 \
  $all $sb_to_fisch

survexport --gpx --surface-legs \
  --survey=fischgesicht-to-painted-track_aday-2018-07-12 \
  $all $fisch_to_hc

survexport --gpx --surface-legs \
  --survey=car-park-to-stone-bridge_psargent-2017-08-06 \
  $all $sb_to_car_park

survexport --gpx --surface-legs \
  --survey=balkon-to-organhoehle_aday-2018-07-12 \
  $all $balkon_to_organ

# mshinwell: fix survexport to not emit vast numbers of
# track segments.
cat $entrances | grep -v "</gpx>" > $output

get_contents () {
  # mshinwell: The "tail" is dodgy but will do for now.
  tail -n +5 $1 | grep -v "</gpx>"
}

get_contents "$balkon_to_organ" >> $output
get_contents "$sb_to_balkon" >> $output
get_contents "$sb_to_fisch" >> $output
get_contents "$fisch_to_hc" >> $output
get_contents "$sb_to_car_park" >> $output

echo "</gpx>" >> $output

# Also build a GPX file of the kataster boundaries.
survexport --gpx $kataster_boundaries kataster-boundaries.gpx



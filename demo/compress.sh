#!/bin/bash

compress()
{
FNAME=$1
ffmpeg -i $FNAME".mp4" -vf scale=240:-1 temp_s.mp4
ffmpeg -i temp_s.mp4 -filter:v fps=fps=10 temp_sr.mp4
rm temp_s.mp4
ffmpeg -i temp_sr.mp4 -c copy -an $FNAME"_s_r_na.mp4"
rm temp_sr.mp4
}

compress bus_clip
compress subway_clip
compress weather_clip

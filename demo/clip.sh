#!/bin/bash

if [ ! -f "bus_clip.mp4" ]
then
ffmpeg -ss 00:00:08.500 -i bus.mp4 -t 00:00:03.500 -c copy bus_clip.mp4
else
echo "bus_clip.mp4 already exists. Skipped."
fi

if [ ! -f "subway_clip.mp4" ]
then
ffmpeg -ss 00:00:03 -i subway.mp4 -t 00:00:13.500 -c copy subway_clip.mp4
else
echo "subway_clip.mp4 already exists. Skipped."
fi

if [ ! -f "weather_clip.mp4" ]
then
ffmpeg -ss 00:00:03 -i weather.mp4 -t 00:00:09 -c copy weather_clip.mp4
else
echo "weather_clip.mp4 already exists. Skipped."
fi

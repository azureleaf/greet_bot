#!/bin/bash

ffmpeg -f concat -safe 0 -i concat.txt -c copy concat.mp4


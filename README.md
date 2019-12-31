# Garmin Dashcam Splicer
This utility allows you to input videos recorded with a Garmin Dashcam and splice them together. By default, these videos are split into one minute segments. The Garmin Drive app does this automatically, but it is inefficient for data transfer as the WiFi speed is slower and often fails to connect.

The output MP4 video is **large** (about 2 MB/s for 1080p and 1.5 MB/s for 720p).

The option is also given to generate a CSV file containing GPS data such as coordinates and speed directly from the AVC video stream.

## Prerequisites
*ffmpeg* and *exiftool* must be in PATH.

### Modules
- shutil
- datetime
- dateutil
- tkinter

*This program should work with all Garmin Dashcams released after 2017 (e.g. 46, 56, 66) and all operating systems.*

# Copyright

This software is provided under the MIT License. Copyright 2019 Darren R. Skidmore

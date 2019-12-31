import os
import re
import shutil
import time
import datetime
import dateutil.parser
import tkinter as tk
from tkinter import filedialog

video1 = False
video2 = False
newPath = False

videoRegex = "GRMN\d{4}\.MP4"
ffmpegTemp = os.getcwd() + "\\ffmpeg_ex.tmp"

exiftoolFileSaveFormat = "%Y%m%d%H%M%S"
exiftoolFileAppend = "_report-" + datetime.datetime.strftime( datetime.datetime.now(), exiftoolFileSaveFormat) + ".csv"

exifDefaultDateFormat = "%Y:%m:%d %H:%M:%S.000Z"
exifSaveDateFormat = "%Y-%m-%d %H:%M:%S"
exifHourOffsetSet = False
exifHourOffset = 0

requiredCommands = ["ffmpeg", "exiftool"]
requiredCommandsVerified = True

'''
    bool checkVideos(str a, str b)
    
    Checks if two input video paths are valid for processing
    
    str a    The first video to check
    str b    The last video to check
'''

def checkVideos(a, b):
    if a == False and b == False:
        # Initial execution
        return False
    else:
        dir = [
            os.path.dirname(a),
            os.path.dirname(b)
        ]
        
        videoRe = [
            re.match(videoRegex, os.path.basename(a), re.I),
            re.match(videoRegex, os.path.basename(b), re.I)
        ]
        
        if not a or not b:
            if not a:
                print("[ERR] The video in position 0 is null.")
            if not b:
                print("[ERR] The video in position 1 is null.")
        elif a == b:
            print("[ERR] The videos are identical.")
        elif dir[0] != dir[1]:
            print("[ERR] The paths do not match.")
        elif not videoRe[0] or not videoRe[1]:
            if not videoRe[0]:
                print("[ERR] The video in position 0 does not have a valid filename.\nAssure that it matches the pattern {}".format(videoRegex))
            if not videoRe[1]:
                print("[ERR] The video in position 1 does not have a valid filename.\nAssure that it matches the pattern {}".format(videoRegex))
        else:
            print("The videos of selection are located at\n{} and\n{}".format(a, b))
            return True
        
        print("")
        print("Please try again.")
        print("")
        return False

'''
    list getMedianVideos(str a, str b)
    
    Given two valid videos, detects all videos that would have been captured in between.
    
    str a   The first video to check
    str b   The last video to check
'''

def getMedianVideos(a, b):
    input = [
        int( os.path.basename(a)[4:8] ),
        int( os.path.basename(b)[4:8] )
    ]
    
    # Switch videos if the older video was chosen first, or vice-versa
    if input[1] < input[0]:
        input[0], input[1] = input[1], input[0]
    
    # Format numbers to video syntax format
    output = list( map( formatNumbers, range(input[0], input[1] + 1) ) )
    
    delIndices = []
    
    # Check for any non-existent files that would otherwise be present
    for i, p in enumerate(output):
        if not os.path.isfile( os.path.dirname(a) + "/" + p ):
            print("[WRN] Missing file {}. It will be omitted.".format(p))
            
            delIndices = [i] + delIndices
    
    print("{} videos will be merged.".format(len(output) - len(delIndices)))
    
    # Remove missing videos
    # Should be done in reverse to preserve list indices
    for i in reversed(delIndices):
        output.pop(i)
    
    return output

'''
    str formatNumbers(int n)
    
    Formats numbers to Garmin video syntax format
    
    int n   An integer between 0 and 9 999
'''

def formatNumbers(n):
    return "GRMN{:04}.MP4".format(n)

'''
    bool checkSave(str a)
    
    Checks if a to-be-saved file has a valid name
    
    str a   The video to be seaved
'''

def checkSave(a):
    if a == False:
        # Initial execution
        return False
    else:
        if not a or a == ".mp4":
            print("[ERR] The file path is null.")
        else:
            print("The generated video will be saved to \n{}".format(a))
            return True
            
        print("")
        print("Please try again.")
        return False

'''
    filedialog requestFile(str **kwargs)
    
    Generates a Tkinter file selection dialog
    
    str **kwargs    Attributes of the dialog
'''

def requestFile(**kwargs):
    window = tk.Tk()
    window.withdraw()
    
    # Generates using a window title and exclusive filetypes
    dialog = filedialog.askopenfilename(title=kwargs["title"], filetypes=kwargs["filetypes"])
    
    return dialog

'''
    filedialog requestSave(str **kwargs)
    
    Generates a Tkinter file save dialog
    
    str **kwargs    Attributes of the dialog
'''

def requestSave(**kwargs):
    window = tk.Tk()
    window.withdraw()
    
    # Generates using a window title and exclusive filetypes
    dialog = filedialog.asksaveasfilename(title=kwargs["title"], filetypes=kwargs["filetypes"])
    
    return dialog

'''
    void generateReport(str f, list p, str d)
    
    str f   The path to write the report to
    list p  Contains all video paths to write to
    str d   The directory in which files in p are stored in
'''

def generateReport(f, p, d):
    print("")
    
    initOutput = ""
    
    print("{} videos for data extraction.".format(len(p)))
        
    startTime = time.time()
    
    # write raw data to str initOutput and display a time-left message
    for c, i in enumerate(p):
        # This command inputs an AVC video stream d/i and extracts metadata (piped to findstr to filter non-GPS data)
        command = "exiftool -ee -c \"%.9f\" {}/{} | findstr \"GPS\"".format(d, i)
        
        initOutput += os.popen(command).read()
        
        currTime = time.time()
        pctComplete = (c + 1) / len(p)
        secondsLeft = ((currTime - startTime) / pctComplete) + startTime - currTime
        
        print("{:6.1f}% complete ... {:5.1f} seconds remaining ...".format( pctComplete * 100, secondsLeft ) )
    
    initOutputList = initOutput.splitlines()
    
    # helper values to process raw data
    defaultPadding = 34
    dpData = [
        [0, 1, 2, 3, 4],
        [0, 2, 3, 4, 5]
    ]
    
    dpIndices = []
    outputLines = []
    
    # header line for output
    outputLines.append("Time,Latitude,Longitude,Speed,Measurement")
    
    # GPS Date/Time is the starting key for each second, using that as the base
    for i, r in enumerate( initOutputList ):
        if r.startswith("GPS Date/Time"):
            dpIndices.append(i)
    
    # Parse raw data
    for i, r in enumerate( dpIndices ):
        try:
            dpIndices[i + 1]
        except IndexError:
            # final row(s), do not report
            pass
        else:
            # int lb is line breaks. Should be 5, may be 7 if the GPS screwed up and software interpolation corrected it.
            # Any other numbers will fail and report an error message. The program will then throw a fatal exception.
            
            lb = dpIndices[i + 1] - r
            if lb == 5:
                dpDataAIDX = 0
            elif lb == 7:
                dpDataAIDX = 1
            else:
                print("Unexpected behaviour at line {}.\nLine differential: {}.\nThe program cannot handle this anomaly; execution cannot continue.".format( str(r), lb ))
            
            a = cleanData( initOutputList[dpIndices[i]+dpData[dpDataAIDX][0]][defaultPadding:], 0, "{}/{}".format(d, p[0]) )
            b = cleanData( initOutputList[dpIndices[i]+dpData[dpDataAIDX][1]][defaultPadding:], 1)
            c = cleanData( initOutputList[dpIndices[i]+dpData[dpDataAIDX][2]][defaultPadding:], 2)
            d = cleanData( initOutputList[dpIndices[i]+dpData[dpDataAIDX][3]][defaultPadding:], 3)
            e = cleanData( initOutputList[dpIndices[i]+dpData[dpDataAIDX][4]][defaultPadding:], 4)
            
            outputLines.append('{},{},{},{},{}'.format( a,b,c,d,e ))
    
    # Write to disk
    with open(f, "w") as fw:
        print("Writing to disk at {} ...".format(f))
        fw.write("\n".join(outputLines))

'''
    str cleanData(str d, int i, str OR None p)
    
    Parses raw data from the AVC video stream and returns a properly-formatted object
    
    str d   The data to parse
    int i   The type of data that will be parsed
        i=0 Time
                Time string is malformed and in an ambiguous time zone, this is accounted for
                There are duplicates, this should be fixed in future?
        i=1 Latitude
        i=2 Longitude
                Converted to a string which is a signed int
        i=3 Speed
        i=4 Speed Measurement
                Returned as-is
    str OR  The path of the videos to read from. ONLY necessary if the exitHourOffsetSet is False,
    None p  otherwise it will be set as None and ignored.
'''

def cleanData(d, i, p=None):
    if i == 0:
        # Input should be a date
        # Must be global so it can be stored for all future calls
        global exifHourOffsetSet
        global exifHourOffset
        
        initial = datetime.datetime.strptime(d, exifDefaultDateFormat)
        
        if not exifHourOffsetSet:
            # Get the unix time of the date string
            unix = time.mktime(initial.timetuple())
            # Compare it with the FAT32 date created time of the video
            exifHourOffset = getTimeOffset(p, unix)
            exifHourOffsetSet = True
        
        fixed = initial + datetime.timedelta(hours=exifHourOffset)
        
        return fixed
    elif i == 1 or i == 2:
        # Should be a %.9f decimal coordinate
        if d.startswith("-180"):
            return ""
        else:
            if d[-1:] == "W" or d[-1:] == "S":
                return "-{}".format(d[:-2])
            else:
                return "{}".format(d[:-2])
    else:
        # Should be a speed or speed measurement, no conversion necessary
        return d

'''
    int getTimeOffset(str path, int unix)
    
    Returns the time offset, in hours, of the file creation time and GPS reported time
    
    str path    The path of the video
    int unix    The Unix timestamp of the GPS
'''

def getTimeOffset(path, unix):
    # The timestamps seem to be offset by a varying amount of hours. Attempts to adjust it to the FAT32 timestamp on the video file.
    uts = os.path.getctime(path)
    hours = round((uts - unix) / 3600)
    
    return hours

if __name__ == "__main__":
    print("Checking dependencies...")
    
    for c in requiredCommands:
        if shutil.which(c) is None:
            requiredCommandsVerified = False
            print("A dependency, {}, is missing. Execution cannot continue.".format(c))
        
    print("")

    if requiredCommandsVerified:
        print("Welcome to the Garmin Dashcam Video Splicer!")
        print("This utility should work with all major Garmin Dashcams released since 2017.")
        print("It will allow you to splice together unsaved videos that would appear congruent in the Garmin Drive app.")
        print("You can also generate a CSV file showing the coordinates and speeds that were tracked.")
        
        print("")
        
        print("Copyright (C) 2019-2020 by Darren R. Skidmore")
        
        print("")
        
        while not checkVideos(video1, video2):
            video1 = requestFile(title="Select the first video", filetypes=[("Garmin Dash Cam Footage","*.mp4")])
            video2 = requestFile(title="Select the last video", filetypes=[("Garmin Dash Cam Footage","*.mp4")])
            
            # Only decomment for debugging
            #video1=r"E:\DCIM\105UNSVD\GRMN0218.MP4"
            #video2=r"E:\DCIM\105UNSVD\GRMN0222.MP4"
        
        paths = getMedianVideos(video1, video2)
        
        print("")
        
        while not checkSave(newPath):
            newPath = requestSave(title="Choose a new file to save to", filetypes=[("MPEG-4 Video","*.mp4")])
            
            # Append file extension
            if newPath[-4:] != ".mp4":
                newPath += ".mp4"
        
        print("")
        
        with open(ffmpegTemp, "w") as f:
            # Write the required ffmpeg commands
            for p in paths:
                f.write("file '{}'\n".format(os.path.dirname(video1) + "/" + p))
        
        # This ffmpeg commands concatenates the files at the path ffmpegTemp and creates a new file at newPath
        command = "ffmpeg -f concat -i \"{}\" -c copy -fflags +genpts \"{}\"".format(ffmpegTemp, newPath)
        
        print("$({})".format(command))
        os.system(command)
        
        os.remove(ffmpegTemp)
        
        print("")
        
        if input("Would you also like a report given these video files? [y/n] > ").strip().lower() == "y":
            print("Report WILL be generated.")
            
            # File name is derived from the video name
            exiftoolFile = newPath[:newPath.index(".")] + exiftoolFileAppend
            
            generateReport(exiftoolFile, paths, os.path.dirname(video1))
        else:
            print("Report WILL NOT be generated.")
        
        print("")
        
        print("Thank you for using the Garmin Dashcam Video Splicer!")
        print("Have a splendid day.")
import cv2
import shapely
from shapely.geometry import Polygon, LineString
from vidgear.gears import CamGear
import numpy as np
import time

# I'm using VidGear async video capture for faster resutls
# Went from 16.8 FPS in my Mac to 25.1 FPS without any other change
# After eliminating the wait key safeguard (as it would be in production) it reached 27.6 FPS very close to real time (30 FPS in this particular camera setup)

# First, load the video using standard capture to generate a background image. In reallity, we should find a way to make this process automatic
# without requiring ideal situation (empty court) and with resilience to changes in light coditions (light will change depending on hour)
# But for now it works and allows me to establish a baseline

cap = cv2.VideoCapture("./unido.avi")
frame_width = int( cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height =int( cap.get( cv2.CAP_PROP_FRAME_HEIGHT))
factor = 10 #If changed, you need to manually reenter coordinates
skip_factor = 8 # Number of frames to "jump" without actual motion detection
dim = (int(frame_width/factor),int(frame_height/factor))
frames_background_loading = 30*10 #Every minute at 30FPS

# Establish an starting point
vid_x = int(frame_width/4)
target_x = vid_x
target_x_prev = vid_x
amt = 0

# These correspond to the coordinates of the court boundary as seen from the pano camera. Depend on specific camera installation
points = [[270, 940],
          [1380, 1440],
          [3500, 1440],
          [4490, 985],
          [3475, 380],
          [3000, 300],
          [2385, 255],
          [1810, 280],
          [1310, 345]]

# These are the same points reduced by the factor (10). I don't know how to automate this
points_small = [[27,94],
                [138,144],
                [350,144],
                [449,98],
                [347,38],
                [300,30],
                [238,25],
                [181,28],
                [131,34]]

roi = Polygon(points)
roi_small = Polygon(points_small)

# Sample 10 frames from first 1000 and average them to create background
num_frames_vid = min(1000,cap.get(cv2.CAP_PROP_FRAME_COUNT))
frame_indices = num_frames_vid * np.random.uniform(size=10)
frames = []

for idx in frame_indices:
    cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ret, frame = cap.read()
    frames.append(frame)

#Calculate the background as an averaged image, and reduce its size
background = np.median(frames, axis = 0).astype(np.uint8)
background_small = cv2.resize(background, dim, interpolation = cv2.INTER_AREA)
background_small_gray = cv2.cvtColor(background_small, cv2.COLOR_BGR2GRAY)

# Release video object
cap.release()

# Start async video capture stream
cap = CamGear(source="./unido.avi").start()

start = time.time()

frame_count = 0

while True:
    # read frames from stream
    frame = cap.read()
    
    # check for frame if Nonetype
    if frame is None:
        break

    frame_small = cv2.resize(frame, dim, interpolation = cv2.INTER_AREA)

    frame_count += 1

    # Detect if it is a frame where we want to apply motion detection
    if frame_count % skip_factor == 0:
        #Reduce frame sie to reduce noise and accelerate calculations
        #frame_small = cv2.resize(frame, dim, interpolation = cv2.INTER_AREA)
        frame_small_gray = cv2.cvtColor(frame_small, cv2.COLOR_BGR2GRAY)

        # Compute difference with "static" background
        diff = cv2.absdiff(background_small_gray,frame_small_gray)
        blur = cv2.GaussianBlur(diff, (5,5), 0)
        _, thresh = cv2.threshold(blur, 20, 255, cv2.THRESH_BINARY)
        dilated = cv2.dilate(thresh, None, iterations=3)

        # Establish contours
        #sC = time.time()
        contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        top = 0
        bottom = 0
        target_x_prev = target_x

        # Iterate over the founded contours to discard the small ones or those outside of the roi. Compute center of mass.
        # I'm aware there should be a better way to do this process, to start with, it would be interesting to compute as an array
        # instead of carrying the variable. Second, might be interesting to use some kind of Non Maxima Suppresion (NMS) to discard
        # boxes within boxes, but as it is results are ok. Any help here would be really appreciated
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > (1000/(factor*factor)):
                x, y, w, h = cv2.boundingRect(cnt)
                player_feet = LineString([[x, y + h], [x + w, y + h]])
                if roi_small.contains(player_feet):
                    cv2.rectangle(frame_small, (x,y), (x+w,y+h),(0,255,0),3)
                    # For the computation of center of mass
                    top += x*area
                    bottom += area

        # Safenet just in case there were no BLOBS detected
        if bottom == 0:
            target_x = target_x_prev

        # Establish target_x considering limits of the visible field, both to the left and to the right, values are specific to this camera installation
        else:
            target_x = int(max(100,min(top/bottom*factor-2560/2,4900-2560)))

        # Virtual panning of the camera
        if abs(target_x - vid_x) >= 100:
            if abs(target_x - vid_x) >= 300:
                amt = int(((target_x - vid_x)/5)//skip_factor)
            else:
                amt = int(((target_x - vid_x)/10)//skip_factor)
        else:
            amt=0

    # I don't know why this is needed, but got some errors due to being a float
    vid_x = int(vid_x+amt)

    # Display will contain the frame as seen on the broadcasting. This is done for ALL frames. First we crop the panoramic frame (panning) the we reduce its size to FullHD
    display = frame[0: 1440,vid_x: vid_x+2560]
    display = cv2.resize(display, (1920,1080), interpolation = cv2.INTER_AREA)

    # Different views to see it is working right
    #cv2.imshow("Frame", frame)
    cv2.imshow("Blobs", frame_small)
    #cv2.imshow("Mask", dilated)
    cv2.imshow("Display", display)

    #Break if ESC key is pressed
    key = cv2.waitKey(30)
    if key == 27:
        break

end = time.time()
print("Total")
print(end - start)
print("Frames per second")
print(frame_count/(end-start))

# Release objects
cap.stop()
cv2.destroyAllWindows()

# Copyright 2021 Jaime Nebrera & Sameer Chaturvedi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


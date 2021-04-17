import numpy as np
import cv2
import time
import shapely
from shapely.geometry import Polygon, LineString
import pandas as pd


# TODO: Pass as argument
vid = 'videos_4_15/game.avi' # game footage, should be changed approproately.
vidcap = cv2.VideoCapture(vid) # Open the video
fps = vidcap.get(cv2.CAP_PROP_FPS)

num_frames_vid = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)

frame_indices = num_frames_vid * np.random.uniform(size=50)

frames = []

for idx in frame_indices:
    vidcap.set(cv2.CAP_PROP_POS_FRAMES, idx)
    ret, frame = vidcap.read()
    frames.append(frame)
    
background = np.median(frames, axis = 0).astype(np.uint8) # create a background frame from the median of pixels in each frame (ideally would calibrate a background when setting up camera but this works)

bw_background = cv2.cvtColor(background, cv2.COLOR_BGR2GRAY)
data = []
# These correspind to the coordinates of the court boundary as seen from the pano camera
points = [[270, 940],
          [1380, 1440],
          [3500, 1440],
          [4490, 985],
          [3475, 380],
          [3000, 300],
          [2385, 255],
          [1810, 280],
          [1310, 345]]

court_poly = Polygon(points)

cnt = 0 # Initialize frame counter
# Some characteristics from the original video
w_frame, h_frame = int(vidcap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(vidcap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps, frames = vidcap.get(cv2.CAP_PROP_FPS), vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
# print(w_frame, h_frame, fps, frames)

num_frames = 1
area_thres = 2000

frame_diffs = []
ret = True
i = 0

start = time.time()

frame_width = int(vidcap.get(3))
frame_height = int(vidcap.get(4))

# define cropping values
vid_x,vid_y,vid_h,vid_w = 2400,0,1000,1700 
right = False

# output 
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter('result.avi', fourcc, fps/num_frames, (vid_w, vid_h))

df = pd.DataFrame(data, columns = ['frame', 'x', 'w', 'y', 'h'])

cnt=0
s = time.time()
while True:
    ret, frame = vidcap.read()
    cnt += 1 # Counting frames
    # Avoid problems when video finishes
    if ret:
        bw_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        frame_diff = cv2.absdiff(bw_frame, bw_background) # frame differencing between current frame and background
        ret, thres = cv2.threshold(frame_diff, 50, 255, cv2.THRESH_BINARY)
        dilate_frame = cv2.dilate(thres, None, iterations=2)
        frame_diffs.append(dilate_frame)
        if i % num_frames == num_frames - 1:
#             print(f'{round(time.time() - start, 3)} seconds, {round((i/num_frames_vid)*100, 1)}% complete')
            to_save = sum(frame_diffs)
            contours, hierarchy = cv2.findContours(to_save, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE) # find the player blobs
            to_save = cv2.cvtColor(to_save, cv2.COLOR_GRAY2RGB)
            cp = background.copy()
            cp[to_save > 0] = 255
            frame_diffs = []
            avg = 0 # for avg x pos in each frame
            n=0
            for c in contours:
                if cv2.contourArea(c) < area_thres:
                    continue
                else:
                    (x, y, w, h) = cv2.boundingRect(c) # create bounding boxes
                    player_feet = LineString([[x, y + h], [x + w, y + h]]) # corresponds to bottom of the box
                    if court_poly.contains(player_feet): # if feet are within the court boundaries
                        data.append([i, x, w, y, h])
                        avg+=x
                        n+=1
#                         cv2.rectangle(cp, (x, y), (x+w, y+h), (255, 0, 0), 2)
#                         cv2.polylines(cp, [np.array(points).reshape((-1, 1, 2))],
#                                       isClosed = True, color = (0, 0 ,255), thickness = 5)
#                         cv2.line(cp, (x, y + h), (x + w, y + h), (0, 255, 0), thickness = 5)
            try:
                com_ = com_df.loc[i]
#                 cv2.line(cp, (com_, 0), (com_, frame_height), (0, 0, 255), thickness = 5)
            except Exception as e:
                pass
            new_x = max(200,int(avg/n)-850) # 850 is arbitrary so the video doesn't start exactly at the median x 
            # auto-panning solution
            if (new_x - vid_x) >= 200:
                right = True
            elif (vid_x - new_x) >=200:
                left = True
            else: 
                right = False
                left = False
            if right:
                amt = (new_x - vid_x)//30
                if amt>10:
                    vid_x+=amt
            if left: 
                amt = (vid_x - new_x)//30
                if amt>10:
                    vid_x-=amt
            crop_frame = frame[vid_y:vid_y+vid_h, vid_x:vid_x+vid_w] # Cropping the frame
#             pcnt = cnt *100/frames # Percentage

            out.write(crop_frame)
#             cv2.imshow('cropped',crop_frame)
        i += 1
    else:
        break

vidcap.release()
cv2.destroyAllWindows()
out.release()
print(time.time() - s)

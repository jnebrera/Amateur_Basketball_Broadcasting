# Amateur Basketball Broadcasting Camera System

![](./images/Title.jpg "Cover")

# First software releases as of April 27th 2021

You can see the design and consideration in the [about section](https://github.com/jnebrera/Amateur_Basketball_Broadcasting/blob/main/about.md).

In this past week, both Sameer and me have found some time to finally work on the coding aspects of the project. In the repository you have both scripts.

Bear in mind this software needs a video recorded with a panoramic camera and some tunning for the specific playground.

My script is a refined version of Sameer's, but I have left out by now the recording of the video itself, thus the script is good to play with and see if the algorithmic ideas are right or not.

# The background

In both cases we create a static background by extracting some random frames from the video and averaging them. This system should be improved so it is able to work in a streaming fashion instead of loading from a recorded video. Also, it is hard to get a static image with no players in such facilities, specially if you consider changing lighting conditions and different baskets utilized, so I have discarded such option. This is an area of improvement.

# Motion detection

Motion detection is done every nth frame by substracting the background image. From there, only bigger than a limit area are considered. To those, the feet position is computed and seen if it is withing the playground area.

In the case of Sameer's, the center of gravity is computed just with the center of the feet. In my version, both the position and the area are considered. My alternative makes biggher rectangles weight more in the positioning decision (for example, multiple players detected as just one box, have significant weight as the area is big).

My version implements the idea of the [Automatic Camera Selection](https://hal.archives-ouvertes.fr/hal-01835033/file/automatic-camera-selection.pdf) paper.

In my version, I believe there is a better way to compute it, working directly with arrays.

Also, might be interesting to apply some Non Maxima Substraction (NMS) to reduce false positives, but reality is, as those tend to happen were there are players, I'm not worried by this factor.

Still, the possibility of shapes entering the field while their feet are outside of it and not being related to the game (like coach or public) is clearly affecting the results if their body is partially boxed. In many cases the bounding box doesn't cover the whole body and it is within the field (for example, the upper torso). It would be very important to reduce this effect to the maximum by proper camera placement (in our lab unfortunately the bodies of the coaches clearly enter the field many times).

I just purchased a Jetson Nano 2GB Dev Kit. Hope that by using a more advanced motion detection mechanism while still being able to sustain the framerate, will improve this situation.

# The panning

The implemented panning system is quite simple. Surely it could be improved to make it smoother. We establish limits both to the left and right, so the camera doesn't focus on an area of little interest for the game (values are specific to the field seen by the camera).

# Async video capture

The last improvement to my version has been to make the reading of the video async. Performance improved from 16 to 24 FPS which is a huge boost. For the background computation I don't use it, but I'm not worried by now about that is it is only computed once in its current form and is outside of the hot code path.

What is more important, the same [VidGear](https://abhitronix.github.io/vidgear/v0.2.1-stable/) library provides methods to read video from a RTSP server (most CCTV cameras have one) and to send the final video to Youtube or Facebook using RTMP (which is the ultimate goal of the project). 

So not only we have improved performance, but found the way to easily support source and sink video streams !!!

# Discarded ideas

One way to speed up the center of gravity computation was to do it directly over the mask image. It does work, producing good results but surprisingly is slower that finding the contours and iterating over them, thus we discarded it.

Also, instead of using an static background image we tried to detect movement by substracting a prior frame. We tried both frame -1 and frame -skip but the results were too erratic (the problem of the coach being partially detected as within the field).

# Things to try

I want to try to apply a bitmask to the image to discard from further computation areas that we know for sure have no effect on the game itself (public areas, benches). Unfortunately I'm quite new to Python and OpenCV and have been unable to do it by myself. Any help would be appreciated. The key here is that the "active" area is defined by a polygon shape.

When I receive the Jetson Nano, I will try to improve all the code with the help of GPU acceleration. Let's see.



## Advanced Lane Finding
[![Udacity - Self-Driving Car NanoDegree](https://s3.amazonaws.com/udacity-sdc/github/shield-carnd.svg)](http://www.udacity.com/drive)
![Lanes Image](./example_output.jpg)


Overview
---

This project aims to find lane lines in a video stream from a mounted on the dashboard of a car. A pipeline is used to process the video stream 
and output a resulting video stream with the detected lane overlaid along with auxiliary information such as lane curvature and position relative
to the centre of the lane. An example of the output is shown above.

Project Instructions
---

The goals / steps of this project are the following:

* Compute the camera calibration matrix and distortion coefficients given a set of chessboard images.
* Apply a distortion correction to raw images.
* Use color transforms, gradients, etc., to create a thresholded binary image.
* Apply a perspective transform to rectify binary image ("birds-eye view").
* Detect lane pixels and fit to find the lane boundary.
* Determine the curvature of the lane and vehicle position with respect to center.
* Warp the detected lane boundaries back onto the original image.
* Output visual display of the lane boundaries and numerical estimation of lane curvature and vehicle position.

The images for camera calibration are stored in the folder called `camera_cal`.  The images in `test_images` are for testing the pipeline on single frames.  

Project Structure
---
- **[calibration_utils.py](./calibration_utils.py):** Helper functions for camera calibration
 
- **[perspective_transform_utils.py](./perspective_transform_utils.py):** Helper functions for perspective_transform
 
- **[binary_utils.py](./binary_utils.py):** Helper functions for creating color transform and thresholded gradient binary map
 
- **[lane_pixels_utils.py](./lane_pixels_utils.py):** Helper functions for detect the lane line pixels
 
- **[line_utils.py](./line_utils.py):** Define a class of lane lines
 
- **[curvature_utils.py](./curvature_utils.py):** Helper functions for calculating radius of curvature and the offset
 
- **[plot_image.py](./plot_image.py):** Helper function to plot images
 
- **[pipeline.py](./pipeline.py):** Pipeline for finding the lanes

- **[P2.pynb](./P2.ipynb):** Jupyter notebook containing all steps to detect lane lines
 
- **[writeup.md](./writeup.md):** Writeup of the pipeline implementation describing the steps taken to extract lane pixels and convert them to lanes

- **[test_videos_output](./test_videos_output):** Directory containing the processed test videos

- **[output_images](./output_images):** Directory containing examples of the processed test images

Running the code
---

The IPython notebook can be run using a Jupyter Notebook app such as Anaconda. The project depends on the NumPy, OpenCV, Matplotlib & MoviePy libraries.

To see the results of this project, you can directly run the codes in `P2.ipynb`.




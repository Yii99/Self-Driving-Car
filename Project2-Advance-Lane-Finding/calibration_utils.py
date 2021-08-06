import cv2
import numpy as np
import matplotlib.image as mpimg
import matplotlib.pyplot as plt
import os

def camera_calibration(images, nx, ny):
    '''

    :param images: images list
    :param nx: points per row of a image
    :param ny: points per column of a image
    :return: the parameters of a calibration image
    '''

    # the 3D coordinates of the real undistorted chessboard corners
    objpoints = []
    # the coordinates of the corners in 2D image
    imgpoints = []
    # prepare object points
    objp = np.zeros((nx * ny, 3), np.float32)
    # x, y coordinate
    objp[:, :2] = np.mgrid[0:nx, 0:ny].T.reshape(-1, 2)

    for fname in images:
        # read image
        image = mpimg.imread(fname)
        # split the name of image
        head_tail = os.path.split(fname)
        # apply grayscale transform
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        # find the chessboard corners
        ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)

        if ret == True:
            imgpoints.append(corners)
            objpoints.append(objp)
            # draw corners
            image = cv2.drawChessboardCorners(image, (9, 6), corners, ret)
            # save the image
            path = os.path.join('output_images/', 'corner'+head_tail[1])
            plt.imshow(image)
            plt.savefig(path)
    # calibrate the camera
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, image.shape[1:], None, None)

    return ret, mtx, dist, rvecs, tvecs

def undistorted_images(image, mtx, dist):
    '''

    :param image: original image
    :param mtx: camera matrix (to transform 3D object points to 2D image points)
    :param dist: distortion coefficient
    :return: undistorted image
    '''
    undist = cv2.undistort(image, mtx, dist, None, mtx)
    return undist

def warped_image(image, undist, nx, ny):
    '''
    Apply perspective transform on the image
    :param image: original image
    :param undist: undistorted image
    :param nx: points per row of a image
    :param ny: points per column of a image
    :return: a warped image
    '''

    # apply grayscale transform
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    # find corners
    ret, corners = cv2.findChessboardCorners(gray, (nx, ny), None)
    img_size = (image.shape[1], image.shape[0])

    if ret == True:
        # define 4 source points src
        src = np.float32([corners[8], corners[-1],
                          corners[len(corners) - 9], corners[0]])
        # define 4 destination points dst
        dst = np.float32([[image.shape[1] - 100, 100], [image.shape[1] - 100, image.shape[0] - 100],
                          [100, image.shape[0] - 100], [100, 100]])
        # apply perspective transform to get the transform matrix
        M = cv2.getPerspectiveTransform(src, dst)
        # warp the image to a top-down view
        warped = cv2.warpPerspective(undist, M, img_size, flags=cv2.INTER_LINEAR)

    return warped



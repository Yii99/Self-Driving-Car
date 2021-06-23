import cv2
import numpy as np

def warped_test_images(undist, inverse):
    '''
    Apply perspective transform on the image
    :param undist: undistorted image
    :param inverse: if True, returen the inverse warped image
    :return: a warped image
    '''

    # length of x and y
    img_size = (undist.shape[1], undist.shape[0])

    # define 4 source points src
    src = np.float32([[200, img_size[1]-10], # bottom left
                     [img_size[0]-200, img_size[1]-10], # bottom right
                     [img_size[0]/2+60, img_size[1]/2+100], # upper right
                     [img_size[0]/2-60, img_size[1]/2+100]]) # upper left
    # define 4 destination points dst
    dst = np.float32([[320, img_size[1]-10], # bl
                      [img_size[0]-320, img_size[1]-10], # br
                      [img_size[0]-320, 0], #ur
                      [320, 0]]) # ul
    # apply perspective transform to get the transform matrix

    if inverse:
        M = cv2.getPerspectiveTransform(dst, src)

    else:
        M = cv2.getPerspectiveTransform(src, dst)

    # warp the image to a top-down view
    warped = cv2.warpPerspective(undist, M, img_size, flags=cv2.INTER_LINEAR)
    return warped


def weighted_img(img, initial_img, α=0.8, β=.2, γ=0.):
    '''

    :param img: the warped image with marked lane lines
    :param initial_img: original image
    The result image is computed as follows:

    initial_img * α + img * β + γ
    NOTE: initial_img and img must be the same shape!
    :return: An overlay of img and initial_img
    '''

    return cv2.addWeighted(initial_img, α, img, β, γ)
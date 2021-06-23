from calibration_utils import undistorted_images
from binary_utils import combined_gradient_threshold, combined_color_threshold, region_of_interest
from perspective_transform_utils import warped_test_images, weighted_img
from lane_pixels_utils import find_lane_pixels_blind, find_lane_pixels, fit_polynomial, visualization_outimg
from curvature_utils import measure_curvature_pixels, offset_to_center
import numpy as np
import cv2


def pipeline(ini_img, mtx, dist, left_lane_line, right_lane_line, nwindows, margin, minpix, verbose, test):

    undist = undistorted_images(ini_img, mtx, dist)
    combined = combined_gradient_threshold(undist, sx_thresh=(20, 100), dir_thresh=(0.7, 1.3), sobel_kernel=9)
    combined_binary = combined_color_threshold(undist, s_thresh=(170, 255), combined=combined)
    imshape = ini_img.shape
    vertices = np.array([[(0, imshape[0]), (imshape[1] / 2 - 25, imshape[0] / 2 + 50),
                          (imshape[1] / 2 + 25, imshape[0] / 2 + 50), (imshape[1], imshape[0])]], dtype=np.int32)
    masked_image = region_of_interest(combined_binary, vertices)
    warped_test_image = warped_test_images(masked_image, inverse=False)

    if  left_lane_line.detected == False or right_lane_line.detected == False:
        left_lane_line, right_lane_line, out_img = find_lane_pixels_blind(warped_test_image, left_lane_line, right_lane_line, nwindows, margin, minpix, verbose)
    else:
        left_lane_line, right_lane_line, out_img = find_lane_pixels(warped_test_image, left_lane_line, right_lane_line, margin)

    left_lane_line, right_lane_line, ploty = fit_polynomial(left_lane_line, right_lane_line, warped_test_image, thresh=50, sanity=True)
    result = visualization_outimg(warped_test_image, left_lane_line, right_lane_line, ploty, margin, test)
    warped_inverse = warped_test_images(result, inverse=True)
    weighted_image = weighted_img(warped_inverse, undist, α=1, β=0.5, γ=0.)
    left_lane_line, right_lane_line = measure_curvature_pixels(left_lane_line, right_lane_line, ploty)
    offset = offset_to_center(combined_binary,left_lane_line, right_lane_line)
    mean_curvature_meter = np.mean([left_lane_line.radius_of_curvature, right_lane_line.radius_of_curvature])
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(weighted_image, 'Curvature radius: {:.02f}m'.format(mean_curvature_meter), (10, 60), font, 1.5,
                (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(weighted_image, 'Offset from center: {:.02f}m'.format(offset), (10, 130), font, 1.5, (255, 255, 255), 2,
                cv2.LINE_AA)

    return weighted_image
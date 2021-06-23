from lane_pixels_utils import find_lane_pixels
import numpy as np

def offset_to_center(binary_warped,left_lane_line, right_lane_line):
    '''
    Calculate the offset of the car center and the lane lines center
    '''
    # car center
    img_center = binary_warped.shape[1]//2
    xm_per_pix = 3.7/640

    # calculate the position of the lane lines in the front of the car
    y = binary_warped.shape[0]-1
    left_lane_x = left_lane_line.best_fit[0] * y ** 2 + left_lane_line.best_fit[1] * y + left_lane_line.best_fit[2]
    right_lane_x = right_lane_line.best_fit[0] * y ** 2 + right_lane_line.best_fit[1] * y + right_lane_line.best_fit[2]
    # calculate the center of lane lines
    lane_lines_center = (left_lane_x+right_lane_x)//2
    # if positive, the car is on the right of the lane lines center
    # if negative, the car is on the left of the lane lines center
    offset = (img_center - lane_lines_center) * xm_per_pix

    return offset


def measure_curvature_pixels(left_lane_line, right_lane_line, ploty):
    '''
    Calculates the curvature of polynomial functions in pixels.
    '''
    # meters per pixel in y dimension
    ym_per_pix = 30/720
    # meters per pixel in x dimension
    xm_per_pix = 3.7/640

    # define y-value where we want radius of curvature
    # we'll choose the maximum y-value, corresponding to the bottom of the image
    y_eval = np.max(ploty)

    left_fit = np.polyfit(left_lane_line.ally * ym_per_pix, left_lane_line.allx * xm_per_pix , 2)
    right_fit = np.polyfit(right_lane_line.ally * ym_per_pix, right_lane_line.allx * xm_per_pix, 2)

    # implement the calculation of R_curve (radius of curvature)
    left_curverad = np.sqrt((1 + (2 * left_fit[0] * y_eval * ym_per_pix + left_fit[1]) ** 2) ** 3) / np.absolute(2 * left_fit[0])
    right_curverad = np.sqrt((1 + (2 * right_fit[0] * y_eval * ym_per_pix + right_fit[1]) ** 2) ** 3) / np.absolute(2 * right_fit[0])

    left_lane_line.update_radius(left_curverad)
    right_lane_line.update_radius(right_curverad)
    return left_lane_line, right_lane_line

import numpy as np
import cv2

def hist(img):
    '''
    :param img: binary warped image
    :return: histogram along the x axis
    '''
    # grab only the bottom half of the image
    # lane lines are likely to be mostly vertical nearest to the car
    bottom_half = img[img.shape[0] // 2:, :]
    # sum across image pixels vertically - make sure to set an `axis`
    # i.e. the highest areas of vertical lines should be larger values
    histogram = np.sum(bottom_half, axis=0)
    return histogram


def find_lane_pixels_blind(binary_warped, left_lane_line, right_lane_line, nwindows, margin, minpix, verbose):
    '''
    :param binary_warped: binary warped image
    :param left_lane_line: the instance of left lane line
    :param right_lane_line: the right of left lane line
    :param nwindows: the number of sliding windows
    :param margin: the width of the windows +/- margin
    :param minpix: minimum number of pixels found to recenter window
    :param verbose: if True, draw sliding windows
    :return: the coordinates of x and y axis of nonezero pixels within the window
    '''

    # take a histogram of the bottom half of the image
    histogram = hist(binary_warped)
    # create an output image to draw on and visualize the result
    out_img = np.dstack((binary_warped, binary_warped, binary_warped))
    # find the peak of the left and right halves of the histogram
    # these will be the starting point for the left and right lines
    midpoint = np.int(histogram.shape[0] // 2)
    leftx_base = np.argmax(histogram[:midpoint])
    rightx_base = np.argmax(histogram[midpoint:]) + midpoint

    # set height of windows - based on nwindows above and image shape
    window_height = np.int(binary_warped.shape[0] // nwindows)
    # identify the x and y positions of all nonzero pixels in this image
    # return the indices of the elements that are non-zero
    nonzero = binary_warped.nonzero()
    nonzeroy = np.array(nonzero[0])
    nonzerox = np.array(nonzero[1])

    # current positions to be updated later for each window in nwindows
    leftx_current = leftx_base
    rightx_current = rightx_base

    # create empty lists to receive left and right lane pixel indices
    left_lane_inds = []
    right_lane_inds = []

    # step through the windows one by one
    for window in range(nwindows):
        # identify window boundaries in x and y (and right and left)
        win_y_low = binary_warped.shape[0] - (window + 1) * window_height
        win_y_high = binary_warped.shape[0] - window * window_height
        win_leftx_low = leftx_current - margin
        win_leftx_high = leftx_current + margin
        win_rightx_low = rightx_current - margin
        win_rightx_high = rightx_current + margin

        # draw the windows on the visualization image
        if verbose:
            cv2.rectangle(out_img, (win_leftx_low, win_y_low), (win_leftx_high, win_y_high), (0, 255, 0), 2)
            cv2.rectangle(out_img, (win_rightx_low, win_y_low), (win_rightx_high, win_y_high), (0, 255, 0), 2)

        # ((...)) return 0 or 1 of vector nonzerox and nonzeroy, elements outside the window are 0
        # use .nonzero() because we are interested in the value 1 (elements inside the window)
        # final result is the index of pixels inside the window
        good_left_inds = ((nonzeroy >= win_y_low) & (nonzeroy <= win_y_high) &
                          (nonzerox >= win_leftx_low) & (nonzerox <= win_leftx_high)).nonzero()[0]

        good_right_inds = ((nonzeroy >= win_y_low) & (nonzeroy <= win_y_high) &
                           (nonzerox >= win_rightx_low) & (nonzerox <= win_rightx_high)).nonzero()[0]

        # append these indices to the lists
        left_lane_inds.append(good_left_inds)
        right_lane_inds.append(good_right_inds)

        # if the number of nonzero pixels > minpix pixels, recenter next window
        if len(good_left_inds) > minpix:
            # nonzerox[good_left_inds] return the x coordinate of the nonzero pixels within the window
            # leftx_current returns the mean value of all x coordinates of those pixels
            leftx_current = np.int(np.mean(nonzerox[good_left_inds]))
        if len(good_right_inds) > minpix:
            rightx_current = np.int(np.mean(nonzerox[good_right_inds]))

    # concatenate the arrays of indices (previously was a list of lists of pixels)

    left_lane_inds = np.concatenate(left_lane_inds)
    right_lane_inds = np.concatenate(right_lane_inds)

    # extract left and right line pixel positions
    left_lane_line.allx = nonzerox[left_lane_inds]
    left_lane_line.ally = nonzeroy[left_lane_inds]
    right_lane_line.allx = nonzerox[right_lane_inds]
    right_lane_line.ally = nonzeroy[right_lane_inds]

    return left_lane_line, right_lane_line, out_img


def find_lane_pixels(binary_warped, left_lane_line, right_lane_line, margin):
    '''
    :param binary_warped: warped binary image
    :param left_lane_line: the instance of left lane line
    :param right_lane_line: the right of left lane line
    :param margin: the width of the lane line +/- margin
    :return:
    '''
    out_img = np.dstack((binary_warped, binary_warped, binary_warped))

    nonzero = binary_warped.nonzero()
    nonzeroy = np.array(nonzero[0])
    nonzerox = np.array(nonzero[1])

    left_lane_inds = ((nonzerox >= (
                left_lane_line.best_fit[0] * (nonzeroy ** 2) + left_lane_line.best_fit[1] * nonzeroy +
                left_lane_line.best_fit[2] - margin)) &
                      (nonzerox <= (
                                  left_lane_line.best_fit[0] * (nonzeroy ** 2) + left_lane_line.best_fit[1] * nonzeroy +
                                  left_lane_line.best_fit[2] + margin)))

    right_lane_inds = ((nonzerox >= (
                right_lane_line.best_fit[0] * (nonzeroy ** 2) + right_lane_line.best_fit[1] * nonzeroy +
                right_lane_line.best_fit[2] - margin)) &
                       (nonzerox <= (right_lane_line.best_fit[0] * (nonzeroy ** 2) + right_lane_line.best_fit[
                           1] * nonzeroy + right_lane_line.best_fit[2] + margin)))

    left_lane_line.allx = nonzerox[left_lane_inds]
    left_lane_line.ally = nonzeroy[left_lane_inds]
    right_lane_line.allx = nonzerox[right_lane_inds]
    right_lane_line.ally = nonzeroy[right_lane_inds]

    return left_lane_line, right_lane_line, out_img


def abs_distance(a, b, thresh):
    if np.absolute(a - b) < thresh:
        return True
    else:
        return False


def sanity_check(left_fitx, right_fitx, thresh):
    xm_per_pix = 3.7 / 640
    top = left_fitx[0] - right_fitx[0]
    middle = left_fitx[left_fitx.shape[0] // 2] - right_fitx[right_fitx.shape[0] // 2]
    bottom = left_fitx[-1] - right_fitx[-1]
    if abs_distance(top, middle, thresh) and abs_distance(middle, bottom, thresh) and abs_distance(top, bottom, thresh) \
            and (0.9 * 3.7) < np.absolute(bottom * xm_per_pix) < (1.1 * 3.7):
        status = True
    else:
        status = False

    return status


def fit_polynomial(left_lane_line, right_lane_line, img, thresh=50, sanity=False):
    '''
    :param left_lane_line: the instance of left lane line with the information of x ang y values
    :param right_lane_line: the right of left lane line with the information of x and y values
    :param img: image
    :return: the x values for all y
    '''
    # x = a*y**2 + by + c
    # return a, b and c

    detected = True

    if not list(left_lane_line.allx) or not list(left_lane_line.ally):
        left_fit = left_lane_line.best_fit
        detected = False
    else:
        left_fit = np.polyfit(left_lane_line.ally, left_lane_line.allx, 2)
        left_lane_line.update_coefficients(left_fit, detected)
    if not list(right_lane_line.allx) or not list(right_lane_line.ally):
        right_fit = right_lane_line.best_fit
        detected = False
    else:
        right_fit = np.polyfit(right_lane_line.ally, right_lane_line.allx, 2)
        right_lane_line.update_coefficients(right_fit, detected)

    # generate all values of y coordinate
    ploty = np.linspace(0, img.shape[0] - 1, img.shape[0])

    left_fitx = left_fit[0] * ploty ** 2 + left_fit[1] * ploty + left_fit[2]
    right_fitx = right_fit[0] * ploty ** 2 + right_fit[1] * ploty + right_fit[2]

    if sanity:
        status = sanity_check(left_fitx, right_fitx, thresh)
        if status == True:
            left_lane_line.update_x(left_fitx)
            right_lane_line.update_x(right_fitx)
        else:
            pass
    else:
        left_lane_line.update_x(left_fitx)
        right_lane_line.update_x(right_fitx)
    return left_lane_line, right_lane_line, ploty


def visualization_window(out_img, left_lane_line, right_lane_line):
    '''
    Visualization two lines with different colors
    :param out_img: black image with the same shape as the original image
    :param left_lane_line: the instance of left lane line
    :param right_lane_line: the right of left lane line
    :return:
    '''
    # colors in the left and right lane regions
    out_img[left_lane_line.ally, left_lane_line.allx] = [255, 0, 0]
    out_img[right_lane_line.ally, right_lane_line.allx] = [0, 0, 255]

    return out_img


def visualization_outimg(binary_warped, left_lane_line, right_lane_line, ploty, margin, test):
    '''
    :param binary_warped: combined binary map
    :param left_lane_line: left lane line
    :param right_lane_line: right lane line
    :param ploty: all y values
    :param margin: the width of the windows +/- margin
    :param test: if True, plot the region between two lines
    :return:
    '''
    out_img = np.dstack((binary_warped, binary_warped, binary_warped))
    window_img = np.zeros_like(out_img)
    # colors in the left and right lane regions
    out_img[left_lane_line.ally, left_lane_line.allx] = [255, 0, 0]
    out_img[right_lane_line.ally, right_lane_line.allx] = [0, 0, 255]

    if test:
        left_pts = np.array([np.transpose(np.vstack([left_lane_line.bestx, ploty]))])
        right_pts = np.array([np.flipud(np.transpose(np.vstack([right_lane_line.bestx, ploty])))])

        lane_line_pts = np.hstack((left_pts, right_pts))
        cv2.fillPoly(window_img, np.int_([lane_line_pts]), (0, 255, 0))
        cv2.polylines(window_img, np.int_([left_pts]), isClosed=False, color=(255,0,0), thickness=30)
        cv2.polylines(window_img, np.int_([right_pts]), isClosed=False, color=(0,0,255), thickness=30)

    else:
        # generate a polygon to illustrate the search window area
        # and recast the x and y points into usable format for cv2.fillPoly()
        # np.vstack stack x and y arrays - shape [2, 720]
        # np.transpose - shape [720,2]. This is equivalent to matching each x and y coordinate together
        # np.flipud - flip array in the up/down direction.
        left_line_window1 = np.array([np.transpose(np.vstack([left_lane_line.bestx - margin, ploty]))])
        left_line_window2 = np.array([np.flipud(np.transpose(np.vstack([left_lane_line.bestx + margin,
                                                                        ploty])))])
        # why we need to upside down the right part of the left window?
        # The result will be provided to cv2.fillPoly which draws a polygon onto the image.
        # When we provide the points of the polygon to the function
        # we have to provide them in order in a clockwise or anticlockwise manner.
        # For example if we follow the anti-clockwise order and we provide the left side points from the top towards the bottom,
        # then the right side should go from the bottom towards the top.
        left_line_pts = np.hstack((left_line_window1, left_line_window2))
        right_line_window1 = np.array([np.transpose(np.vstack([right_lane_line.bestx - margin, ploty]))])
        right_line_window2 = np.array([np.flipud(np.transpose(np.vstack([right_lane_line.bestx + margin,
                                                                         ploty])))])
        right_line_pts = np.hstack((right_line_window1, right_line_window2))

        # Draw the lane onto the warped blank image
        cv2.fillPoly(window_img, np.int_([left_line_pts]), (255, 0, 0))
        cv2.fillPoly(window_img, np.int_([right_line_pts]), (0, 0, 255))

    return window_img

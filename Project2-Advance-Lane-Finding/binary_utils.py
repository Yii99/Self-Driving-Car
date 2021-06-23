import cv2
import numpy as np

def compare_color_space(img):
    '''
    Generate color channel maps of 3 color space
    '''
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    hls = cv2.cvtColor(img, cv2.COLOR_RGB2HLS)
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    R = img[:, :, 0]
    G = img[:, :, 1]
    B = img[:, :, 2]
    H = hls[:, :, 0]
    L = hls[:, :, 1]
    S = hls[:, :, 2]
    H2 = hsv[:, :, 0]
    S2 = hsv[:, :, 1]
    V2 = hsv[:, :, 2]
    return gray, R, G, B, H, L, S, H2, S2, V2

def compare_binary(img, thresh):
    '''
    Apply threshold on images and obtain a binary image
    '''
    binary = np.zeros_like(img)
    binary[(img > thresh[0]) & (img <= thresh[1])] = 1

    return binary

def abs_sobel_thresh(img, thresh, orient='x', sobel_kernel=3):
    '''
    Sobel x or y of an image
    '''
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    if orient == 'x':
        # take the derivative in x
        sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=sobel_kernel)
        # absolute x derivative to accentuate lines away from horizontal
        abs_sobelx = np.absolute(sobelx)
        # scale to 8-bit (0 - 255) then convert to type = np.uint8
        scaled_sobel = np.uint8(255*abs_sobelx/np.max(abs_sobelx))
    else:
        scaled_sobel = np.uint8(255*np.absolute(cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=sobel_kernel))/np.max(np.absolute(cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=sobel_kernel))))
    binary = np.zeros_like(scaled_sobel)
    binary[(scaled_sobel >= thresh[0]) & (scaled_sobel < thresh[1])] = 1
    return binary


def mag_thresh(img, sobel_kernel=3, mag_thresh=(0, 255)):
    '''
    Magnitude of gradient
    '''
    # convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # take the gradient in x and y separately
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=sobel_kernel)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=sobel_kernel)
    # calculate the magnitude
    abs_sobel = np.absolute(np.sqrt(sobelx ** 2 + sobely ** 2))
    # scale to 8-bit (0 - 255) and convert to type = np.uint8
    scaled_sobel = np.uint8((255 * abs_sobel) / np.max(abs_sobel))
    # create a binary mask where mag thresholds are met
    sobelbinary = np.zeros_like(scaled_sobel)
    # return this mask as your binary_output image
    sobelbinary[(scaled_sobel >= mag_thresh[0]) & (scaled_sobel <= mag_thresh[1])] = 1
    binary_output = sobelbinary
    return binary_output

def ang_thresh(img, sobel_kernel=3, thresh=(0, np.pi / 2)):
    '''
    Direction of gradient
    '''
    # convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    # take the gradient in x and y separately
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=sobel_kernel)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=sobel_kernel)
    # take the absolute value of the x and y gradients
    abs_sobelx = np.absolute(sobelx)
    abs_sobely = np.absolute(sobely)
    # use np.arctan2(abs_sobely, abs_sobelx) to calculate the direction of the gradient
    angle = np.arctan2(abs_sobely, abs_sobelx)
    # create a binary mask where direction thresholds are met
    sobel_binary = np.zeros_like(angle)
    sobel_binary[(angle >= thresh[0]) & (angle <= thresh[1])] = 1
    return sobel_binary

def get_sxbinary(scaled_sobel, sx_thresh):
    '''
    Set a threshold to gradients and return a binary map
    '''

    # create a mask where the scaled gradient magnitude
    sxbinary = np.zeros_like(scaled_sobel)
    # the value of the pixels within the given threshold is set to 1, otherwise 0
    sxbinary[(scaled_sobel >= sx_thresh[0]) & (scaled_sobel < sx_thresh[1])] = 1

    return sxbinary

def combined_gradient_threshold(img, sx_thresh, dir_thresh, sobel_kernel):
    '''
    Combine gradient thresh and color thresh
    :param img: original image
    :param s_thresh: threshold of saturation color channel
    :param sx_thresh: gradient threshold
    :param sobel_kernel: kernel size
    :return: color map and combined image
    '''

    gradx = abs_sobel_thresh(img, thresh=sx_thresh, orient='x', sobel_kernel=sobel_kernel)
    grady = abs_sobel_thresh(img, thresh=sx_thresh, orient='y', sobel_kernel=sobel_kernel)
    magbinary = mag_thresh(img, sobel_kernel, sx_thresh)
    dirbinary = ang_thresh(img, sobel_kernel=sobel_kernel, thresh=dir_thresh)

    # combine the two binary thresholds
    combined_binary = np.zeros_like(magbinary)
    combined_binary[((gradx == 1) & (grady == 1)) | ((magbinary == 1) & (dirbinary == 1))] = 1

    return combined_binary

def combined_color_threshold(img, s_thresh, combined):
    '''
    Combine gradient thresh and color thresh
    :param img: original image
    :param s_thresh: threshold of saturation color channel
    :param combined: the combined gradient image
    :return: color map and combined image
    '''

    # convert to HLS color space
    hls = cv2.cvtColor(img, cv2.COLOR_RGB2HLS)

    # separate the color channel
    s_channel = hls[:, :, 2]

    # threshold color channel
    s_binary = np.zeros_like(s_channel)
    s_binary[(s_channel >= s_thresh[0]) & (s_channel < s_thresh[1])] = 1


    # combine the two binary thresholds
    combined_binary = np.zeros_like(combined)
    combined_binary[(s_binary == 1) | combined == 1] = 1

    return combined_binary

def region_of_interest(img, vertices):
    """
    Applies an image mask.

    Only keeps the region of the image defined by the polygon
    formed from `vertices`. The rest of the image is set to black.
    `vertices` should be a numpy array of integer points.
    """
    # defining a blank mask to start with
    mask = np.zeros_like(img)

    # defining a 3 channel or 1 channel color to fill the mask with depending on the input image
    if len(img.shape) > 2:
        channel_count = img.shape[2]
        ignore_mask_color = (255,) * channel_count
    else:
        ignore_mask_color = 255

    # filling pixels inside the polygon defined by "vertices" with the fill color
    cv2.fillPoly(mask, vertices, ignore_mask_color)

    # returning the image only where mask pixels are nonzero
    masked_image = cv2.bitwise_and(img, mask)
    return masked_image

def color_transform(img, s_thresh, sx_thresh, sobel_kernel):
    '''
    Combine gradient thresh and color thresh
    :param img: original image
    :param s_thresh: threshold of saturation color channel
    :param sx_thresh: gradient threshold
    :param sobel_kernel: kernel size
    :return: color map and combined image
    '''
    image = np.copy(img)
    # convert to HLS color space
    hls = cv2.cvtColor(image, cv2.COLOR_RGB2HLS)
    # separate the color channel
    s_channel = hls[:, :, 2]

    sxbinary = mag_thresh(image, sobel_kernel, sx_thresh)

    # threshold color channel
    s_binary = np.zeros_like(s_channel)
    s_binary[(s_channel >= s_thresh[0]) & (s_channel < s_thresh[1])] = 1

    # stack each channel
    color_binary = np.dstack((np.zeros_like(sxbinary), sxbinary, s_binary))*255

    return color_binary

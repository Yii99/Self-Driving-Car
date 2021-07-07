import numpy as np
import collections


class Line():
    def __init__(self):
        # number of the frames to be considered
        self.len = 10
        # was the line detected in the last iteration?
        self.detected = False
        # x values of the last n fits of the line
        self.recent_xfitted = collections.deque(maxlen=self.len)
        # average x values of the fitted line over the last n iterations
        self.bestx = None
        # polynomial coefficients of the last n iterarions
        self.recent_fit = collections.deque(maxlen=self.len)
        # polynomial coefficients averaged over the last n iterations
        self.best_fit = None
        # radius of curvature of the line in some units
        self.radius_of_curvature = None
        # x values for detected line pixels
        self.allx = None
        # y values for detected line pixels
        self.ally = None

    def update_x(self, x):
        self.recent_xfitted = []
        if len(self.recent_xfitted) > 0:
            if np.absolute(self.bestx - x).all() < 50:
                self.recent_xfitted.append(x)
                self.bestx = np.mean(np.array(self.recent_xfitted), 0)

        else:
            self.recent_xfitted.append(x)
            self.bestx = x

    def update_coefficients(self, fit, detected):
        self.recent_xfitted = []
        self.detected = detected
        if len(self.recent_fit) > 0:
            self.recent_fit.append(fit)
            self.best_fit = np.mean(np.array(self.recent_fit), 0)
        else:
            self.recent_fit.append(fit)
            self.best_fit = fit

    def update_radius(self, radius):
        if self.radius_of_curvature == None:
            self.radius_of_curvature = radius
        elif np.absolute(self.radius_of_curvature - radius).all() < 100:
            self.radius_of_curvature = (self.radius_of_curvature + radius) / 2
        else:
            return " Sanity check failed: The radius of curvature is not similar. "
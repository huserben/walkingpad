import cv2 as cv
import numpy as np
import os
from time import time
from windowcapture import WindowCapture
from utils import ResizeWithAspectRatio

# Change the working directory to the folder this script is in.
# Doing this because I'll be putting the files from each video in their own folder on GitHub
os.chdir(os.path.dirname(os.path.abspath(__file__)))


# initialize the WindowCapture class
wincap = WindowCapture('Dota 2')

skill_off_cooldown_img = cv.imread('assets/skill-off-cooldown-1080p.png', cv.IMREAD_UNCHANGED)
skill_on_cooldown_img = cv.imread('assets/skill-on-cooldown-1080p.png', cv.IMREAD_UNCHANGED)

def find_match(image, match):
    result = cv.matchTemplate(image, match, cv.TM_SQDIFF_NORMED)

    # I've inverted the threshold and where comparison to work with TM_SQDIFF_NORMED
    threshold = 0.25
    # The np.where() return value will look like this:
    # (array([482, 483, 483, 483, 484], dtype=int32), array([514, 513, 514, 515, 514], dtype=int32))
    locations = np.where(result <= threshold)
    # We can zip those up into a list of (x, y) position tuples
    locations = list(zip(*locations[::-1]))
    print(locations)

    if locations:
        print('Found object.')

        object_w = match.shape[1]
        object_h = match.shape[0]
        line_color = (0, 255, 0)
        line_type = cv.LINE_4

        # Loop over all the locations and draw their rectangle
        for loc in locations:
            # Determine the box positions
            top_left = loc
            bottom_right = (top_left[0] + object_w, top_left[1] + object_h)
            # Draw the box
            cv.rectangle(image, top_left, bottom_right, line_color, line_type)
    return image


loop_time = time()
while(True):

    # get an updated image of the game
    screenshot = wincap.get_screenshot()

    match_result = find_match(screenshot, skill_on_cooldown_img)

    screenshot_resized = ResizeWithAspectRatio(match_result, width=1280)

    cv.imshow('Computer Vision', screenshot_resized)

    # debug the loop rate
    print('FPS {}'.format(1 / (time() - loop_time)))
    loop_time = time()

    # press 'q' with the output window focused to exit.
    # waits 1 ms every loop to process key presses
    if cv.waitKey(1) == ord('q'):
        cv.destroyAllWindows()
        break

print('Done.')

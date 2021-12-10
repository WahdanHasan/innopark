import tesserocr
from PIL import Image
import re as regex
import cv2
import numpy as np


def GetLicenseFromImage(license_plate):
    # Takes a cropped license plate to extract [A-Z] and [0-9] ascii characters from the image.
    # The extracted characters are then returned as a string

    # Define regex pattern
    valid_ascii_pattern = "([A-Z]|[0-9])"

    # Pre-process image
    height, width, _ = license_plate.shape

    resized = cv2.resize(license_plate, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 11, 5, 5)
    ret, thresh1 = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY)

    modified = cv2.erode(thresh1, np.ones((5, 5), np.uint8), iterations=1)

    resized = cv2.resize(modified, (width, height), interpolation=cv2.INTER_AREA)

    # Extract text from image
    text = tesserocr.image_to_text(Image.fromarray(resized))

    # Extract characters that match the regex pattern
    license_plate = []
    for character in text:
        if regex.match(valid_ascii_pattern, character[0]):
            license_plate.append(character)

    license_plate = ''.join(license_plate)

    return license_plate

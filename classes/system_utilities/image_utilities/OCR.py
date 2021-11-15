import tesserocr
from PIL import Image
import re as regex


def GetLicenseFromImage(license_plate):
    # Takes a cropped license plate to extract [A-Z] and [0-9] ascii characters from the image.
    # The extracted characters are then returned as a string

    # Define regex pattern
    valid_ascii_pattern = "([A-Z]|[0-9])"

    # Extract text from image
    text = tesserocr.image_to_text(Image.fromarray(license_plate))

    # Extract characters that match the regex pattern
    license_plate = []
    for character in text:
        if regex.match(valid_ascii_pattern, character[0]):
            license_plate.append(character)

    license_plate = ''.join(license_plate)

    return license_plate

import pytesseract
import re as regex
import cv2

pytesseract.pytesseract.tesseract_cmd = "modules\\TesseractOCR\\tesseract.exe"

def GetLicenseFromImage(license_plate):
    # Takes a cropped license plate to extract [A-Z] and [0-9] ascii characters from the image.
    # The extracted characters are then returned as a string

    # Define regex pattern
    valid_ascii_pattern = "([A-Z]|[0-9])"

    # Extract text from image
    boxes = pytesseract.image_to_boxes(license_plate)
    # Split text into entries of Character : Bounding_box format
    boxes = boxes.splitlines()

    # Extract characters that match the regex pattern
    boxes_temp = []
    for box in boxes:
        box = box.split(' ')
        if regex.match(valid_ascii_pattern, box[0]):
            boxes_temp.append(box)

    boxes = boxes_temp

    license_plate = ""

    # Create a list of the characters
    for box in boxes:
        license_plate = license_plate + box[0]

    return license_plate

def RescaleImageToScale(img, scale_factor):
    # Takes an image and a scale_factor.
    # Rescales the image based on the scale_factor and returns the scaled image

    # Rescale width and height based on scale factor
    width = int(img.shape[1] * scale_factor)
    height = int(img.shape[0] * scale_factor)

    dimensions = (width, height)

    # Rescale image to new dimensions
    rescaled_img = cv2.resize(src=img,
                              dsize=dimensions,
                              interpolation=cv2.INTER_AREA)

    return rescaled_img

def RescaleImageToResolution(img, new_dimensions):
    # Takes an image and the new dimensions (resolution) for it in the form of the tuple (width, height)
    # Rescales the image to the new dimensions and returns the scaled image

    rescaled_img = cv2.resize(src=img,
                              dsize=new_dimensions,
                              interpolation=cv2.INTER_AREA)

    return rescaled_img

def CropImage(img, bounding_set):
    # Crop an image based on the provided bounding set.
    # This bounding set should be in the tuple (TopLeftPoint, BottomRightPoint) format.
    # Returns the cropped image

    # Define Top Left and Bottom Right points to crop upon
    x_min = bounding_set[0][0]
    y_min = bounding_set[0][1]
    x_max = bounding_set[1][0]
    y_max = bounding_set[1][1]

    # Determine absolute width and length
    width = x_max - x_min
    length = y_max - y_min

    # Write the region of the image to be cropped back onto the image started from the origin
    img[0:length, 0:width] = img[y_min:y_max, x_min:x_max]

    # Crop the image up until the overwritten region
    img = img[0:length, 0:width]

    return img

def PlaceImage(base_image, img_to_place, center_x, center_y):
    # From the center point, it figures out the top left and bottom right points based on the character width then it
    # replaces the pixel points on the base with the image provided.
    # Returns the new image.

    height_img, width_img, _ = img_to_place.shape

    # Define top left and bottom right bounding box points for the image to be placed
    top_y = center_y - int(height_img/2)
    left_x = center_x - int(width_img/2)

    bottom_y = top_y + height_img
    right_x = left_x + width_img

    # Overwrite the base image's points based on the bounding box calculated
    temp_image = base_image.copy()
    temp_image[top_y:bottom_y, left_x:right_x] = img_to_place

    return temp_image

def CalculatePointPositionAfterTransform(point, M):
    # Calculates the new position of a point after transformation with set M
    # Returns the transformed points in the list [x, y]

    point_transformed_x = (M[0][0] * point[0] + M[0][1] * point[1] + M[0][2]) / (M[2][0] * point[0] + M[2][1] * point[1] + M[2][2])
    point_transformed_y = (M[1][0] * point[0] + M[1][1] * point[1] + M[1][2]) / (M[2][0] * point[0] + M[2][1] * point[1] + M[2][2])

    return [int(point_transformed_x), int(point_transformed_y)]

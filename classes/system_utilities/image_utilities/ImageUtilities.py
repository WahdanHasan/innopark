import cv2
import numpy as np


def ImageToBlob(image, input_size):
    blob = cv2.dnn.blobFromImage(image, 1/255, (input_size, input_size), [0, 0, 0], 1, crop=False)


    return blob

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

    img_temp = img.copy()

    # Define Top Left and Bottom Right points to crop upon
    x_min = int(bounding_set[0][0])
    y_min = int(bounding_set[0][1])
    x_max = int(bounding_set[1][0])
    y_max = int(bounding_set[1][1])


    # Validation
    img_height, img_width, _ = img_temp.shape
    if y_min < 0:
        y_min = 0
    if y_max > img_height:
        y_max = img_height
    if x_min < 0:
        x_min = 0
    if x_max > img_width:
        x_max = img_width

    # Determine absolute width and length
    width = x_max - x_min
    length = y_max - y_min

    # Write the region of the image to be cropped back onto the image started from the origin
    img_temp[0:length, 0:width] = img[y_min:y_max, x_min:x_max]

    # Crop the image up until the overwritten region
    img_temp = img_temp[0:length, 0:width]


    return img_temp

def PlaceImage(base_image, img_to_place, center_x, center_y):
    # From the center point, it figures out the top left and bottom right points based on the image width then it
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

def SaveImage(image, name, extension='.png', path='data\\saves\\'):
    # Takes an image and saves it
    # It is recommended to use cv2.waitKey(0) when debugging after calling the function in order to prevent overwriting.

    # print("Saving image to " + name + extension + " to " + path + "...")

    cv2.imwrite(path + name + extension, image)

    # print("Finished saving.")

def CalculatePointPositionAfterTransform(point, M):
    # Calculates the new position of a point after transformation with set M
    # Returns the transformed points in the list [x, y]

    point_transformed_x = (M[0][0] * point[0] + M[0][1] * point[1] + M[0][2]) / (M[2][0] * point[0] + M[2][1] * point[1] + M[2][2])
    point_transformed_y = (M[1][0] * point[0] + M[1][1] * point[1] + M[1][2]) / (M[2][0] * point[0] + M[2][1] * point[1] + M[2][2])


    return [int(point_transformed_x), int(point_transformed_y)]

def ConcatenatePictures(img_set):
    # The images provided must be of identical dimensions
    # Returns the images concatenated in a 3 column format

    image_height, image_width, _ = img_set[0].shape
    image_count = len(img_set)

    columns = 3

    if image_count < columns:
        columns = image_count

    base_width = int(img_set[0].shape[1] * columns)

    rows = int(np.ceil(image_count / columns))

    base_height = img_set[0].shape[0] * rows

    img_base = np.zeros((base_height, base_width, 3), dtype=np.uint8)



    for i in range(rows):
        for j in range(columns):
            if (i*columns) + j >= image_count:
                break
            img_base[(i * image_height):((i+1) * image_height), (j * image_width):((j+1) * image_width)] = img_set[(i*columns) + j]


    return img_base

def FloatBBToIntBB(bb):
    # Accepts a bounding box of float values into a bounding box of int values
    # It should be noted that the bounding box provided must be in the [TL, BR] format
    # Returns the int version of the bounding box

    return [[int(bb[0][0]), int(bb[0][1])], [int(bb[1][0]), int(bb[1][1])]]

def GetIncreasedBB(img_dimensions, bbox, increase_factor=0.1):
    # Takes a bounding box and increases its size while making sure the bounding box is not out of bounds of its image.
    # It should be noted that the img_dimensions that are supplied should be in the tuple format of (height, width)

    # Create new bbox
    increased_bbox = [[bbox[0][0], bbox[0][1]], [bbox[1][0], bbox[1][1]]]

    # Increase the top left point while making sure it does not go out of bounds, if it does, set it to max bound
    for j in range(2):
        increased_bbox[0][j] = int(increased_bbox[0][j] - (increased_bbox[0][j] * increase_factor))
        if increased_bbox[0][j] < 0:
            increased_bbox[0][j] = 0

    # Increase the bottom right point while making sure it does not go out of bounds, if it does, set it to max bound
    increased_bbox[1][0] = int(increased_bbox[1][0] + (increased_bbox[1][0] * increase_factor))
    if increased_bbox[1][0] > img_dimensions[1]:
        increased_bbox[1][0] = img_dimensions[1]

    increased_bbox[1][1] = int(increased_bbox[1][1] + (increased_bbox[1][1] * increase_factor))
    if increased_bbox[1][1] > img_dimensions[0]:
        increased_bbox[1][1] = img_dimensions[0]

    return increased_bbox

def GetBBInRespectTo(bbox, bbox_of_new_parent):
    # Takes a bounding box and updates its local coordinates in respect to the bounding box of the new parent provided.
    # This is to be used when getting a bounding box's local points in respect to a larger bounding box. the bounding
    # box in this case would be a subset of the larger bounding box.
    # Returns the bbox's new local point values

    TL = [bbox[0][0] - bbox_of_new_parent[0][0], bbox[0][1] - bbox_of_new_parent[0][1]]
    BR = [bbox[1][0] - bbox_of_new_parent[0][0], bbox[1][1] - bbox_of_new_parent[0][1]]

    local_bb = [[TL[0], TL[1]], [BR[0], BR[1]]]

    return local_bb

def GetFullBoundingBox(bounding_box):
    # Takes a bounding box in the format of [TL, BR]
    # Returns the full bounding box in the format of [TL, TR, BL, BR]

    # Calculate top right points
    top_right_x = bounding_box[1][0]
    top_right_y = bounding_box[0][1]
    top_right = [top_right_x, top_right_y]

    # Calculate bottom left points
    bottom_left_x = bounding_box[0][0]
    bottom_left_y = bounding_box[1][1]
    bottom_left = [bottom_left_x, bottom_left_y]

    return [bounding_box[0], top_right, bottom_left, bounding_box[1]]

def GetPartialBoundingBox(bounding_box):
    # Takes a bounding box in the format of [TL, TR, BL, BR]
    # Returns the equivalent [TL, BR] format box

    partial_bounding_box = [bounding_box[0], bounding_box[3]]

    return partial_bounding_box

def GetBoundingBoxCenter(bounding_box):
    # Takes a bounding box in the format of [TL, BR]
    # Returns the center of the bounding box

    center_x = int((bounding_box[1][0] + bounding_box[0][0])/2)
    center_y = int((bounding_box[1][1] + bounding_box[0][1])/2)


    return [center_x, center_y]

def GetFullBoundingBoxCenter(bounding_box):
    # Takes a bounding box in the format of [TL, TR, BL, BR]
    # Returns the center of the bounding box

    center_x = bounding_box[3][0] - bounding_box[0][0]
    center_y = bounding_box[3][1] - bounding_box[0][1]


    return [center_x, center_y]

def GetDimensionsFromBoundingBox(bounding_box):
    # Takes a bounding box in the format of [TL, BR]
    # Returns the height and the width as a tuple

    height = bounding_box[1][1] + bounding_box[0][1]
    width = bounding_box[1][0] + bounding_box[0][0]

    return (height, width)

def DrawLine(image, point_a, point_b, color=(255, 0, 255), thickness=1):

    temp_image = image.copy()

    cv2.line(temp_image, point_a, point_b, color, thickness)

    return temp_image

def DrawBoundingBoxes(image, bounding_boxes, color=(255, 0, 255), thickness=1):
    # Takes an image and places bounding boxes on it from the detections.
    # It should be noted that the bounding boxes must be in the [TL, BR] format
    # Returns the image with all the drawn boxes on it.

    if bounding_boxes is None:
        return image

    if len(bounding_boxes) == 0:
        return image

    temp_image = image.copy()

    for i in range(len(bounding_boxes)):
        temp_image = cv2.rectangle(img=temp_image,
                                   pt1=bounding_boxes[i][0],
                                   pt2=bounding_boxes[i][1],
                                   color=color,
                                   thickness=thickness)

    return temp_image

def DrawParkingBoxes(image, bounding_boxes, are_occupied, thickness=3):
    # Takes an image and places the parking space bounding boxes on it from the detections
    # It should be noted that the bounding boxes must be in the [TL, TR, BL, BR] format
    # Returns the image with all the boxes and their appropriate colors drawn on it.

    if bounding_boxes is None:
        return image

    temp_image = image.copy()

    for i in range(len(bounding_boxes)):
        temp_color = (0, 0, 255) if are_occupied[i] else (0, 255, 0)
        cv2.line(temp_image, bounding_boxes[i][0], bounding_boxes[i][1], temp_color, thickness)
        cv2.line(temp_image, bounding_boxes[i][0], bounding_boxes[i][2], temp_color, thickness)
        cv2.line(temp_image, bounding_boxes[i][1], bounding_boxes[i][3], temp_color, thickness)
        cv2.line(temp_image, bounding_boxes[i][2], bounding_boxes[i][3], temp_color, thickness)

    return temp_image

def DrawBoundingBoxAndClasses(image, class_names, bounding_boxes, probabilities=None, color=(255, 0, 255), thickness=1):
    # Takes an image and places class names, probabilities, and bounding boxes on it from the detections.
    # It should be noted that the bounding boxes must be in the [TL, BR] format
    # Returns the image with all the drawn boxes on it.

    if bounding_boxes is None:
        return image

    if len(bounding_boxes) == 0:
        return image

    temp_image = image.copy()

    for i in range(len(class_names)):
        temp_image = cv2.rectangle(img=temp_image,
                                   pt1=bounding_boxes[i][0],
                                   pt2=bounding_boxes[i][1],
                                   color=color,
                                   thickness=thickness)

        if probabilities is not None:
            temp_image = cv2.putText(img=temp_image,
                                     text=f'{class_names[i]} {int(probabilities[i])}%',
                                     org=(bounding_boxes[i][0][0], bounding_boxes[i][0][1] - 10),
                                     fontFace=cv2.FONT_HERSHEY_DUPLEX,
                                     fontScale=0.5,
                                     color=(0, 0, 255),
                                     thickness=1)
        else:
            temp_image = cv2.putText(img=temp_image,
                                     text=f'{class_names[i]}',
                                     org=(bounding_boxes[i][0][0], bounding_boxes[i][0][1] - 10),
                                     fontFace=cv2.FONT_HERSHEY_DUPLEX,
                                     fontScale=0.5,
                                     color=(0, 0, 255),
                                     thickness=1)

    return temp_image
import random
import cv2
import os
import copy
import numpy as np

PLATES_PER_CHARACTER = 1
PLATES_PER_TYPE = 2
CENTER_Y = 41
RANGE_X_LETTER = [28, 60]
RANGE_X_DIGIT = [183, 333]
STYLE_BOUNDING_SETS = []
STYLE_AUGMENTED_BOUNDING_SETS = []
STYLE_CROP_BOUNDING_SETS = []
SET_OF_M = []
SET_OF_TRANSFORM = []
SET_OF_OFFSET = []
BRIGHTNESS_BASE = 2
SET_OF_BRIGHTNESS_POWERS = [6]

def main():

# Define bounding box sets
    STYLE_BOUNDING_SETS.append([[6, 6], [344, 6], [6, 76], [344, 76]])
    STYLE_BOUNDING_SETS.append([[6, 6], [344, 6], [6, 76], [344, 76]])

# Calculate offset for bounding box
    for i in range(len(STYLE_BOUNDING_SETS)):
        temp_height = STYLE_BOUNDING_SETS[i][0][1] + STYLE_BOUNDING_SETS[i][3][1]
        temp_width = STYLE_BOUNDING_SETS[i][0][0] + STYLE_BOUNDING_SETS[i][3][0]

        if temp_height > temp_width:
            SET_OF_OFFSET.append(temp_height * 1)
        else:
            SET_OF_OFFSET.append(temp_width * 1)

# Declare transformation sets
    for i in range(PLATES_PER_TYPE):
        SET_OF_TRANSFORM.append([])

# Define transformation sets
    TransformPlates()

# Declare and Calculate set of M
    for i in range(PLATES_PER_TYPE):
        SET_OF_M.append([])
        for j in range(len(SET_OF_TRANSFORM[0])):
            SET_OF_M[i].append(cv2.getPerspectiveTransform(SET_OF_TRANSFORM[i][j][0], SET_OF_TRANSFORM[i][j][1]))

# Calculate augmented bounding boxes
    for i in range(PLATES_PER_TYPE):
        STYLE_AUGMENTED_BOUNDING_SETS.append([])
        for j in range(len(SET_OF_TRANSFORM[0])):
            temp_bounding_box = AugmentBoundingBox(bounding_box=STYLE_BOUNDING_SETS[i], style_number=i, m_index=j)
            STYLE_AUGMENTED_BOUNDING_SETS[i].append(temp_bounding_box)

# Define paths and directories
    path_data = "Data\\DataGenerator\\"
    path_blanks = path_data + "Template_Blanks"
    directory_blanks = os.listdir(path_blanks)
    path_ascii = path_data + "Template_Ascii"
    directory_ascii = os.listdir(path_ascii)

    path_generated_images = path_data + "Generated_Licenses\\"

# Define variables
    directory_blanks_length = len(directory_blanks)
    image_file_extension = '.png'
    xml_file_extension = '.xml'

    license_digit_min = 0
    license_digit_max = 10

    license_character_min = 10
    license_character_max = 36

    images_of_digits = []
    images_of_characters = []
    images_of_blanks = []
    images_of_generated_plates = []
    xml_of_generated_plates = []

# Load blanks, digits, and characters
    print("Loading blanks, digits, and characters...")
    LoadImages(path=path_blanks, directory=directory_blanks, array=images_of_blanks, end_pos=directory_blanks_length)
    LoadImages(path=path_ascii, directory=directory_ascii, array=images_of_digits, end_pos=license_digit_max, start_pos=license_digit_min)
    LoadImages(path=path_ascii, directory=directory_ascii, array=images_of_characters, end_pos=license_character_max, start_pos=license_character_min)
    print("Finished loading.\n")

# Declare size variables
    number_to_generate = len(images_of_characters) * PLATES_PER_CHARACTER
    styles_to_generate = PLATES_PER_TYPE

# Generate number plates
    print("Generating licenses...")
    GeneratePlates(images_of_blanks, images_of_characters, images_of_digits, images_of_generated_plates, xml_of_generated_plates, image_file_extension, number_to_generate, styles_to_generate)
    print("Finished generating.\n")

# Augment plates
    #AugmentBrightness(generated_plates=images_of_generated_plates)

# Save generates plates
    SaveGeneratedPlates(generated_plates=images_of_generated_plates, count=len(images_of_generated_plates), path=path_generated_images, extension=image_file_extension, xmls=xml_of_generated_plates, xml_extension=xml_file_extension)

def LoadImages(path, directory, array, end_pos, start_pos=0):

    for i in range(start_pos, end_pos):
        temp_path = path + '/' + directory[i]

        temp_image = cv2.imread(temp_path)

        array.append(temp_image)

def GeneratePlates(blanks, characters, digits, plates, xmls, xml_extension, number_to_generate, styles_to_generate):

    digit_width = int(digits[0].shape[1])
    half_digit_width = int(digit_width/2)
    file_name = 0
# Loops through every style.. For every style it goes through A-Z n times.. It places the character first, then decides
# a random amount of digits to place, and places them in their correct places.
# The generated plate is then augmented by M
    for i in range(styles_to_generate):
        for j in range(number_to_generate):
            index_of_character = j % len(characters)

            temp_image = blanks[i].copy()

            center_x = int((RANGE_X_LETTER[0] + RANGE_X_LETTER[1]) / 2)

            PlaceImage(base_image=temp_image,
                       img_to_place=characters[index_of_character],
                       center_x=center_x,
                       center_y=CENTER_Y)

            number_of_digits = random.randint(1, 5)

            center_x = int((RANGE_X_DIGIT[0] + RANGE_X_DIGIT[1])/2)

            center_x = int(center_x - ((number_of_digits-1) * half_digit_width))

            for k in range(number_of_digits):

                digit = random.randint(0, 9)
                digit = digits[digit]

                PlaceImage(base_image=temp_image,
                           img_to_place=digit,
                           center_x=center_x,
                           center_y=CENTER_Y)

                center_x = center_x + digit_width


            temp_bounding_box = GetBoundingBoxTLBR(bounding_set=STYLE_BOUNDING_SETS[i])

            temp_xml = GenerateXML(bounding_box=temp_bounding_box,
                                   image_shape=temp_image.shape,
                                   name=file_name,
                                   extension=xml_extension)

            plates.append(temp_image)
            xmls.append(temp_xml)

            # for k in range(len(SET_OF_BRIGHTNESS_POWERS)):
            #     b_and_d = AugmentPlateBrightness(plate=temp_image,
            #                                      base=BRIGHTNESS_BASE,
            #                                      power=SET_OF_BRIGHTNESS_POWERS[k],
            #                                      )
            #
            #     file_name = file_name + 1
            #     temp_bright_xml = GenerateXML(bounding_box=temp_bounding_box,
            #                            image_shape=temp_image.shape,
            #                            name=file_name,
            #                            extension=xml_extension)
            #
            #     file_name = file_name + 1
            #     temp_dark_xml = GenerateXML(bounding_box=temp_bounding_box,
            #                            image_shape=temp_image.shape,
            #                            name=file_name,
            #                            extension=xml_extension)
            #
            #     plates.append(b_and_d[0])
            #     plates.append(b_and_d[1])
            #     xmls.append(temp_bright_xml)
            #     xmls.append(temp_dark_xml)

            for k in range(len(SET_OF_TRANSFORM[0])):
                file_name = file_name + 1

                temp_augmented_bounding_box = GetBoundingBoxTLBR(bounding_set=STYLE_AUGMENTED_BOUNDING_SETS[i][k])

                temp_augmented_image = AugmentPlateTransform(plate=temp_image,
                                                             style_number=i,
                                                             m_index=k,
                                                             bounding_set=temp_augmented_bounding_box)

                temp_augmented_xml = GenerateXML(bounding_box=temp_augmented_bounding_box,
                                                 image_shape=temp_augmented_image.shape,
                                                 name=file_name,
                                                 extension=xml_extension)

                plates.append(temp_augmented_image)
                xmls.append(temp_augmented_xml)

                # for l in range(len(SET_OF_BRIGHTNESS_POWERS)):
                #     b_and_d = AugmentPlateBrightness(plate=temp_augmented_image,
                #                                      base=BRIGHTNESS_BASE,
                #                                      power=SET_OF_BRIGHTNESS_POWERS[l],
                #                                      )
                #
                #     file_name = file_name + 1
                #     temp_augmented_bright_xml = GenerateXML(bounding_box=temp_augmented_bounding_box,
                #                                   image_shape=temp_augmented_image.shape,
                #                                   name=file_name,
                #                                   extension=xml_extension)
                #
                #     file_name = file_name + 1
                #     temp_augmented_dark_xml = GenerateXML(bounding_box=temp_augmented_bounding_box,
                #                                 image_shape=temp_augmented_image.shape,
                #                                 name=file_name,
                #                                 extension=xml_extension)
                #
                #     plates.append(b_and_d[0])
                #     plates.append(b_and_d[1])
                #     xmls.append(temp_augmented_bright_xml)
                #     xmls.append(temp_augmented_dark_xml)

            file_name = file_name + 1

def PlaceImage(base_image, img_to_place, center_x, center_y):
# From the center point, it figures out the top left and bottom right points based on the character width then it
# replaces the pixel points on the blank with the character provided
    height_img, width_img, _ = img_to_place.shape

    # Define top left and bottom right bounding box points for the image to be placed
    top_y = center_y - int(height_img/2)
    left_x = center_x - int(width_img/2)

    bottom_y = top_y + height_img
    right_x = left_x + width_img

    # Overwrite the base image's points based on the bounding box calculated
    base_image[top_y:bottom_y, left_x:right_x] = img_to_place

def GenerateXML(bounding_box, image_shape, name, extension):

    height = image_shape[0]
    width = image_shape[1]

    xml = ''.join(("\n",
                   "<annotation>\n",
                   "    <folder>images</folder>\n",
                   "    <filename>Cars" + str(name) + extension + "</filename>\n",
                   "    <size>\n",
                   "        <width>" + str(width) + "</width>\n",
                   "        <height>" + str(height) + "</height>\n",
                   "        <depth>3</depth>\n",
                   "    </size>\n",
                   "    <segmented>0</segmented>\n",
                   "    <object>\n",
                   "        <name>licence</name>\n",
                   "        <pose>Unspecified</pose>\n",
                   "        <truncated>0</truncated>\n",
                   "        <occluded>0</occluded>\n",
                   "        <difficult>0</difficult>\n",
                   "        <bndbox>\n",
                   "            <xmin>" + str(bounding_box[0][0]) + "</xmin>\n",
                   "            <ymin>" + str(bounding_box[0][1]) + "</ymin>\n",
                   "            <xmax>" + str(bounding_box[1][0]) + "</xmax>\n",
                   "            <ymax>" + str(bounding_box[1][1]) + "</ymax>\n",
                   "        </bndbox>\n",
                   "    </object>\n",
                   "</annotation>\n"
                   ))

    return xml

def GetBoundingBoxTLBR(bounding_set):

    x_min = 99999
    x_max = 0
    y_min = 99999
    y_max = 0

    for i in range (len(bounding_set)):
        if bounding_set[i][0] < x_min:
            x_min = bounding_set[i][0]
        elif bounding_set[i][0] > x_max:
            x_max = bounding_set[i][0]

        if bounding_set[i][1] < y_min:
            y_min = bounding_set[i][1]
        elif bounding_set[i][1] > y_max:
            y_max = bounding_set[i][1]

    return [[x_min, y_min], [x_max, y_max]]

def AugmentPlateBrightness(plate, base, power):

    im = np.ones(plate.shape, dtype="uint8") * pow(base, power)
    bright_temp = cv2.add(plate, im)
    dark_temp = cv2.subtract(plate, im)

    return [bright_temp, dark_temp]

def AugmentPlateTransform(plate, style_number, m_index, bounding_set):

    plate_height = plate.shape[0]
    plate_width = plate.shape[1]

    # Create translation matrix to offset the plate
    T1 = np.float32([[1, 0, int(SET_OF_OFFSET[style_number]/2)], [0, 1, int(SET_OF_OFFSET[style_number]/2)]])

    # Translate the plate into the center of the image
    temp_plate = cv2.warpAffine(plate, T1, (plate_width + SET_OF_OFFSET[style_number], plate_height + SET_OF_OFFSET[style_number]))

    # Perform transformation augment on image
    temp_plate = cv2.warpPerspective(temp_plate, SET_OF_M[style_number][m_index], (plate_width + SET_OF_OFFSET[style_number], plate_height + SET_OF_OFFSET[style_number]))

    # Crop plate
    temp_plate = CropPlate(plate=temp_plate, bounding_set=bounding_set)

    return temp_plate

def AugmentBoundingBox(bounding_box, style_number, m_index):

    bounding_box_temp = copy.deepcopy(bounding_box)

    for i in range(len(bounding_box_temp)):
        for j in range(len(bounding_box_temp[i])):
            bounding_box_temp[i][j] = int(bounding_box_temp[i][j] + (SET_OF_OFFSET[style_number]/2))
        bounding_box_temp[i] = CalculatePointPositionWithTransform(bounding_box_temp[i], SET_OF_M[style_number][m_index])

    return bounding_box_temp

def CalculatePointPositionWithTransform(point, M):

    point_transformed_x = (M[0][0] * point[0] + M[0][1] * point[1] + M[0][2]) / (M[2][0] * point[0] + M[2][1] * point[1] + M[2][2])
    point_transformed_y = (M[1][0] * point[0] + M[1][1] * point[1] + M[1][2]) / (M[2][0] * point[0] + M[2][1] * point[1] + M[2][2])

    return [int(point_transformed_x), int(point_transformed_y)]

def SaveGeneratedPlates(generated_plates, count, path, extension, xmls, xml_extension):

    print("Saving licenses to disk...")
    for i in range(count):
        cv2.imwrite(path + "Cars" + str(i) + extension, generated_plates[i])
        temp_file = open(path + "Cars" + str(i) + xml_extension, 'w')
        temp_file.write(xmls[i])

    print("Finished saving.\n")

def CropPlate(plate, bounding_set):

    x_min = bounding_set[0][0]
    y_min = bounding_set[0][1]
    x_max = bounding_set[1][0]
    y_max = bounding_set[1][1]

    width = x_max - x_min
    length = y_max - y_min

    plate[0:length, 0:width] = plate[y_min:y_max, x_min:x_max]
    plate = plate[0:length, 0:width]

    bounding_set[0][0] = 0
    bounding_set[0][1] = 0
    bounding_set[1][0] = width
    bounding_set[1][1] = length

    return plate

def TransformPlates():
    for i in range(PLATES_PER_TYPE):
        temp_offset = SET_OF_OFFSET[i]

        x = 40
        y = 90
        pts1 = np.float32([
            [(56 + temp_offset), (56 + temp_offset)],
            [(368 + temp_offset), (52 + temp_offset)],
            [(28 + temp_offset), (387 + temp_offset)],
            [(389 + temp_offset), (290 + temp_offset)]])

        pts2 = np.float32([
            [(56 + temp_offset), (56 + temp_offset)],
            [((368-x) + temp_offset), ((52-x) + temp_offset)],
            [(28 + temp_offset), (387 + temp_offset)],
            [(389 + temp_offset), (290 + temp_offset)]])

        SET_OF_TRANSFORM[i].append([pts1, pts2])

        pts1 = np.float32([
            [(56 + temp_offset), (56 + temp_offset)],
            [(368 + temp_offset), (52 + temp_offset)],
            [(28 + temp_offset), (387 + temp_offset)],
            [(389 + temp_offset), (290 + temp_offset)]])

        pts2 = np.float32([
            [(56 + temp_offset), (56 + temp_offset)],
            [((368-x) + temp_offset), (52 + temp_offset)],
            [(28 + temp_offset), (387 + temp_offset)],
            [(389 + temp_offset), (290 + temp_offset)]])

        SET_OF_TRANSFORM[i].append([pts1, pts2])

        pts1 = np.float32([
            [(56 + temp_offset), (56 + temp_offset)],
            [(368 + temp_offset), (52 + temp_offset)],
            [(28 + temp_offset), (387 + temp_offset)],
            [(389 + temp_offset), (290 + temp_offset)]])

        pts2 = np.float32([
            [((56+x) + temp_offset), ((56-x) + temp_offset)],
            [((368-x) + temp_offset), (52 + temp_offset)],
            [((28-x) + temp_offset), (387 + temp_offset)],
            [(389 + temp_offset), ((290-x) + temp_offset)]])

        SET_OF_TRANSFORM[i].append([pts1, pts2])

        pts1 = np.float32([
            [(56 + temp_offset), (56 + temp_offset)],
            [(368 + temp_offset), (52 + temp_offset)],
            [(28 + temp_offset), (387 + temp_offset)],
            [(389 + temp_offset), (290 + temp_offset)]])

        pts2 = np.float32([
            [((56+x) + temp_offset), ((56-x) + temp_offset)],
            [((368-x) + temp_offset), ((52-x) + temp_offset)],
            [((28-x) + temp_offset), (387 + temp_offset)],
            [(389 + temp_offset), ((290-x) + temp_offset)]])

        SET_OF_TRANSFORM[i].append([pts1, pts2])

        pts1 = np.float32([
            [(56 + temp_offset), (56 + temp_offset)],
            [(368 + temp_offset), (52 + temp_offset)],
            [(28 + temp_offset), (387 + temp_offset)],
            [(389 + temp_offset), (290 + temp_offset)]])

        pts2 = np.float32([
            [((56+y) + temp_offset), ((56-x) + temp_offset)],
            [((368-x) + temp_offset), ((52-x) + temp_offset)],
            [((28-y) + temp_offset), (387 + temp_offset)],
            [(389 + temp_offset), ((290-x) + temp_offset)]])

        SET_OF_TRANSFORM[i].append([pts1, pts2])

        pts1 = np.float32([
            [(56 + temp_offset), (56 + temp_offset)],
            [(368 + temp_offset), (52 + temp_offset)],
            [(28 + temp_offset), (387 + temp_offset)],
            [(389 + temp_offset), (290 + temp_offset)]])

        pts2 = np.float32([
            [((56+x) + temp_offset), ((56) + temp_offset)],
            [((368-y) + temp_offset), ((52) + temp_offset)],
            [(28 + temp_offset), (387 + temp_offset)],
            [((389-y) + temp_offset), ((290) + temp_offset)]])

        SET_OF_TRANSFORM[i].append([pts1, pts2])

        pts1 = np.float32([
            [(56 + temp_offset), (56 + temp_offset)],
            [(368 + temp_offset), (52 + temp_offset)],
            [(28+y + temp_offset), (387-y + temp_offset)],
            [(389 + temp_offset), (290 + temp_offset)]])

        pts2 = np.float32([
            [((56+y) + temp_offset), ((56-y) + temp_offset)],
            [((368+y) + temp_offset), ((52-y) + temp_offset)],
            [((28-y) + temp_offset), ((387-y) + temp_offset)],
            [((389+y) + temp_offset), ((290-y) + temp_offset)]])

        SET_OF_TRANSFORM[i].append([pts1, pts2])

        pts1 = np.float32([
            [(56 + temp_offset), (56 + temp_offset)],
            [(368 + temp_offset), (52 + temp_offset)],
            [(28 + temp_offset), (387 + temp_offset)],
            [(389 + temp_offset), (290 + temp_offset)]])

        pts2 = np.float32([
            [((56+y) + temp_offset), ((56-x) + temp_offset)],
            [((368-y) + temp_offset), ((52+y) + temp_offset)],
            [((28+y) + temp_offset), ((387-y) + temp_offset)],
            [((389-y) + temp_offset), ((290+y) + temp_offset)]])

        SET_OF_TRANSFORM[i].append([pts1, pts2])

        pts1 = np.float32([
            [(56-x + temp_offset), (56+y + temp_offset)],
            [(368 + temp_offset), (52 + temp_offset)],
            [(28 + temp_offset), (387 + temp_offset)],
            [(389 + temp_offset), (290 + temp_offset)]])

        pts2 = np.float32([
            [((56+y) + temp_offset), ((56-x) + temp_offset)],
            [((368-y) + temp_offset), ((52+y) + temp_offset)],
            [((28+y) + temp_offset), ((387-x) + temp_offset)],
            [((389-y) + temp_offset), ((290+y) + temp_offset)]])

        SET_OF_TRANSFORM[i].append([pts1, pts2])

        pts1 = np.float32([
            [(56-x + temp_offset), (56+y + temp_offset)],
            [(368 + temp_offset), (52 + temp_offset)],
            [(28 + temp_offset), (387 + temp_offset)],
            [(389+y + temp_offset), (290-x + temp_offset)]])

        pts2 = np.float32([
            [((56) + temp_offset), ((56) + temp_offset)],
            [((368-y) + temp_offset), ((52+y) + temp_offset)],
            [((28+y) + temp_offset), ((387-x) + temp_offset)],
            [((389+y) + temp_offset), ((290+y) + temp_offset)]])

        SET_OF_TRANSFORM[i].append([pts1, pts2])

        pts1 = np.float32([
            [(56-x + temp_offset), (56+y + temp_offset)],
            [(368-x + temp_offset), (52-y + temp_offset)],
            [(28+y + temp_offset), (387+x + temp_offset)],
            [(389+y + temp_offset), (290-x + temp_offset)]])

        pts2 = np.float32([
            [((56) + temp_offset), ((56) + temp_offset)],
            [((368-y) + temp_offset), ((52+y) + temp_offset)],
            [((28+y) + temp_offset), ((387-x) + temp_offset)],
            [((389+y) + temp_offset), ((290+y) + temp_offset)]])

        SET_OF_TRANSFORM[i].append([pts1, pts2])

        pts1 = np.float32([
            [(56-x + temp_offset), (56+y + temp_offset)],
            [(368-x + temp_offset), (52-y + temp_offset)],
            [(28+y + temp_offset), (387+x + temp_offset)],
            [(389+y + temp_offset), (290-x + temp_offset)]])

        pts2 = np.float32([
            [((56-y) + temp_offset), ((56-y) + temp_offset)],
            [((368-y) + temp_offset), ((52+y) + temp_offset)],
            [((28+y) + temp_offset), ((387-x) + temp_offset)],
            [((389+y) + temp_offset), ((290+y) + temp_offset)]])

        SET_OF_TRANSFORM[i].append([pts1, pts2])

        pts1 = np.float32([
            [(56-x + temp_offset), (56-x + temp_offset)],
            [(368-x + temp_offset), (52-y + temp_offset)],
            [(28 + temp_offset), (387 + temp_offset)],
            [(389+y + temp_offset), (290-x + temp_offset)]])

        pts2 = np.float32([
            [((56+y) + temp_offset), ((56) + temp_offset)],
            [((368-y) + temp_offset), ((52-y) + temp_offset)],
            [((28) + temp_offset), ((387) + temp_offset)],
            [((389) + temp_offset), ((290-y) + temp_offset)]])

        SET_OF_TRANSFORM[i].append([pts1, pts2])

if __name__ == "__main__":
    main()

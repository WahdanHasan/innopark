import pytesseract
import re as regex
import cv2

pytesseract.pytesseract.tesseract_cmd = "lib\\TesseractOCR\\tesseract.exe"

def GetTextFromImage(license_plate):
    valid_ascii_pattern = "([A-Z]|[0-9])"

    boxes = pytesseract.image_to_boxes(license_plate)
    boxes = boxes.splitlines()

    boxes_temp = []
    for box in boxes:
        box = box.split(' ')
        if regex.match(valid_ascii_pattern, box[0]):
            boxes_temp.append(box)

    boxes = boxes_temp

    license_plate = ""

    for box in boxes:
        license_plate = license_plate + box[0]

    return license_plate

def RescaleImage(img, scale):
    width = int(img.shape[1] * scale)
    height = int(img.shape[0] * scale)

    dimensions = (width, height)

    rescaled_img = cv2.resize(src=img,
                              dsize=dimensions,
                              interpolation=cv2.INTER_AREA)

    return rescaled_img
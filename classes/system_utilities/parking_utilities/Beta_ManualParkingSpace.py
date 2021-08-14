from tkinter import *
import cv2
import numpy as np

root = Tk()
root.geometry("350x330")
root.title("InnoPark")

global counter
counter = 0

img = cv2.imread("..\\..\\..\\data\\reference footage\\images\\parking_lot_1.png")
global temp
image_copy = img.copy()
drawing = False
coordinates = []
coordinates_copy = []
temp_list = []
full_bounding_box = []
global point_counter
bottom_right = False
top_right = False
submitted = False
image_reset = False
point_counter = 0
radio_count_BL = 0
radio_count_TL = 0
radio_count_TR = 0
radio_count_BR = 0

parking_id = StringVar()
radio_var = IntVar()

# def createTransparentMask(image):
#     global output
#
#     for alpha in np.arange(0, 1.1, 0.1)[::-1]:
#         # create two copies of the original image -- one for
#         # the overlay and one for the final output image
#         overlays = image.copy()
#         output = image.copy()
#
#         dst = cv2.addWeighted(overlays, alpha, output, 1 - alpha,
#                         0, output)
#
#         #cv2.imshow("Output", output)
#
#         return output

def intersectionOverUnion(parking_bounding_box, car_bounding_box):
    #takes two full bounding boxes
    #uses the TL, BR points to get intersection, area and IoU

    acceptable_threshold = 0.6

    #get x,y coordinates of TL, BR
    xA = max(parking_bounding_box[0][0], car_bounding_box[0][0])                                                #A = [[283, 330], [346,329], [309, 365], [381,360]]                                                                                                            #B = [[282, 331], [347, 330], [307, 366], [379, 364]]
    yA = max(parking_bounding_box[0][1], car_bounding_box[0][1])

    xB = min(parking_bounding_box[3][0], car_bounding_box[3][0])
    yB = min(parking_bounding_box[3][1], car_bounding_box[3][1])

    #check whether intersection exists first
    if (xA > xB or yA > yB):
        print ("No intersection")
        return -1

    #get area of intersecting width and height
    intersecting_area = max(0, xB - xA) * max(0, yB - yA)

    #get the area of both bounding boxes separately
    parking_bounding_box_area = (parking_bounding_box[3][0] - parking_bounding_box[0][0]) * (parking_bounding_box[3][1] - parking_bounding_box[0][1])
    car_bounding_box_area = (car_bounding_box[3][0] - car_bounding_box[0][0]) * (car_bounding_box[3][1] - car_bounding_box[0][1])

    #calculate IoU
    #union = area - intersecting area
    iou = intersecting_area / float(parking_bounding_box_area + car_bounding_box_area - intersecting_area)

    # return the intersection over union value
    print (iou)

    if (iou > acceptable_threshold):
        return True

    return iou


def getBoundingBoxCoordinates(bounding_box):
    #get points from mouse click into a bounding box list
    # [TL, TR, BL, BR]
    full_bounding_box

    top_left_x = bounding_box[1][0]
    top_left_y = bounding_box[1][1]
    top_left = [top_left_x, top_left_y]

    top_right_x = bounding_box[2][0]
    top_right_y = bounding_box[2][1]
    top_right = [top_right_x, top_right_y]

    bottom_left_x = bounding_box[0][0]
    bottom_left_y = bounding_box[0][1]
    bottom_left = [bottom_left_x, bottom_left_y]

    bottom_right_x = bounding_box[3][0]
    bottom_right_y = bounding_box[3][1]
    bottom_right = [bottom_right_x, bottom_right_y]

    if len(full_bounding_box) == 0:
        full_bounding_box.append([top_left, top_right, bottom_left, bottom_right])
    else:
        print("Top left: ", top_left, "Top right: ", top_right, "Bottom left: ", bottom_left, "Bottom right: ", bottom_right)
        full_bounding_box[0][0] = top_left
        full_bounding_box[0][1] = top_right
        full_bounding_box[0][2] = bottom_left
        full_bounding_box[0][3] = bottom_right
    print("Bounding box captured: ", full_bounding_box)

def drawLine():
    #uses the mouse clicks from user to draw lines to it
    #these coordinates are then passed to bounding box function

    #close window after each click to allow only one dot at a time
    global point_counter
    global radio_count_BL
    global radio_count_TL
    global radio_count_TR
    global radio_count_BR
    global submitted

    # if (point_counter % 1 == 0):
    #     cv2.destroyWindow("image")
    print(f"in drawline: {temp_list}, point counter: {point_counter}")
    #draw a line using the last two clicks

    # if (point_counter == 2):
    #     print(f"in method: {temp_list}, point counter: {point_counter}")
    #     cv2.line(img, temp_list[0], temp_list[1], (0, 0, 255), 1)
    #     print(f"in drawline: {temp_list[-1], temp_list[-2]}, point counter: {point_counter}")
    if (point_counter >= 4 and counter == 4):
        coordinates_copy = coordinates.copy()
        getBoundingBoxCoordinates(coordinates_copy)

    if (point_counter >= 2):
        #print(f"in method: {temp_list}, point counter: {point_counter}")
        cv2.line(img, temp_list[-2], temp_list[-1], (0, 0, 255), 1)
        #print(f"in drawline: {temp_list[-1], temp_list[-2]}, point counter: {point_counter}")

    #after every 4 clicks, draw a line between the last and the first point to enclose it
    #copy the points to another list and pass that to bbox function and empty current list
    if (point_counter % 4 == 0):
        print("in % 4", "Submitted status: ", submitted)
        cv2.line(img, temp_list[3],temp_list[0],(0, 0, 255),1)
        radio_count_BR = 0
        radio_count_TL = 0
        radio_count_BL = 0
        radio_count_TR = 0

def draw_circle(event, x, y, flags, param):
    #mouse callback function to allow user to draw on image

    global drawing
    global bottom_right
    global top_right
    global point_counter
    global counter
    global radio_count_BL
    global radio_count_TL
    global radio_count_TR
    global radio_count_BR
    global temp_list
    global cache
    global img
    global submitted
    global image_reset
    global temp
    radio_btn = radio_var.get()
    max_list_size = 4

    #when user holds down mouse button, append the points to a list
    #increment counter for drawLine function
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        coordinates.append((x, y))
        #temp_list = coordinates.copy()
        print("Coordinates list: ", coordinates, "\n temp list: ", temp_list)

        #cache = copy.deepcopy(img)

        if (radio_btn == 1 and len(coordinates) != 0):
                radio_count_BL += 1
                print("radio count BL: ", radio_count_BL)
                if radio_count_BL > 1:
                    point_counter -=1
                    counter -= 1
                    print("Point counter in BL method: ", point_counter)
                    #img = copy.deepcopy(cache)
                    #cv2.imshow('image', img)
                print(point_counter)
                #coordinates.insert(0, (x, y))
                #coordinates.pop()
                #del coordinates[-1]
                print(f" Before: {coordinates}")
                coordinates.insert(0, (x, y))
                coordinates.pop(-1)
                if len(coordinates) > max_list_size:
                    print(f"Before deletion: {coordinates}")
                    coordinates[0] = (x, y)
                    del coordinates[1]
                print(f" After: {coordinates}")
        elif (radio_btn == 2):
                radio_count_TL += 1
                if radio_count_TL > 1:
                    point_counter -= 1
                    counter -=1
                print(point_counter)
                print(f" Before: {coordinates}")
                if len(coordinates) > max_list_size:
                    coordinates[1] = (x, y)
                    del coordinates[-1]
                elif len(coordinates) < max_list_size and top_right is True:
                    coordinates[:0] = [(x, y)]
                    del coordinates[-1]
                else:
                    coordinates.insert(1, (x, y))
                    coordinates.pop(-1)
                print(f" After: {coordinates}")
        elif (radio_btn == 3):
                radio_count_TR += 1
                if radio_count_TR > 1:
                    point_counter -= 1
                    counter -= 1
                top_right = True
                print(f" Before: {coordinates}")
                if len(coordinates) > max_list_size:
                    coordinates[2] = (x, y)
                    del coordinates[-1]
                elif len(coordinates) < 3 and bottom_right is True:
                    coordinates[:0] = [(x,y)]
                    del coordinates[-1]
                elif len(coordinates) < max_list_size and bottom_right is True:
                    coordinates.insert(1, (x, y))
                    del coordinates[-1]
                else:
                    coordinates.insert(2, (x,y))
                    coordinates.pop(-1)
                print(f" After: {coordinates}")
        elif (radio_btn == 4):
                radio_count_BR += 1
                if radio_count_BR > 1:
                    point_counter -= 1
                    counter -= 1
                print(f" Before: {coordinates}")
                bottom_right = True
                if len(coordinates) > max_list_size:
                    coordinates[3] = (x, y)
                    del coordinates[-1]
                else:
                    coordinates.insert(3, (x, y))
                    coordinates.pop(-1)
                print(f" After: {coordinates}")

        point_counter += 1
        counter += 1
        if counter == max_list_size + 1:
            counter -= 1
        print("Counter: ", counter)
        temp_list = coordinates.copy()
        print("Coordinates list: ", coordinates, "\n temp list: ", temp_list)
        #cv2.circle(img, center=temp_list[-1], radius=3, color=(0, 0, 255), thickness=-1)

    #when user lets go of mouse click, draw circle
    if event == cv2.EVENT_LBUTTONUP:
        drawing = False
        cv2.circle(img, center=(x, y), radius=3, color=(0, 0, 255), thickness=-1)
        cv2.circle(img, center=(x, y), radius=3, color=(0, 0, 255), thickness=-1)
        drawLine()

def createWindow():
    #call mousecallback function in created window
    cv2.namedWindow('Image')
    cv2.setMouseCallback('Image', draw_circle)

def radioClicked():
    return
    radio_btn = radio_var.get()
    if (radio_btn == 1 or radio_btn == 2 or radio_btn == 3 or radio_btn == 4):
        loadGUI()

def reset():

    # global image_reset
    # global new_image

    print("Hi")
    # cv2.destroyWindow("Image")
    # image_reset = True


def createMenu():
    l = Label(root, text="Select Bounding Box Corners: ")
    l.config(font=("Courier", 14))
    l.grid(row=0, column=0, pady=(7, 0), padx=(10, 30), sticky="e")

    R1 = Radiobutton(root,
                     text="Bottom Left",
                     variable=radio_var,
                     value=1,
                     command=radioClicked)
    R1.grid(row=1, column=0, pady=(7, 0), padx=(10, 30), sticky="w")

    R2 = Radiobutton(root,
                     text="Top Left",
                     variable=radio_var,
                     value=2,
                     command=radioClicked)

    R2.grid(row=3, column=0, pady=(7, 0), padx=(10, 30), sticky="w")

    R3 = Radiobutton(root,
                     text="Top Right",
                     variable=radio_var,
                     value=3,
                     command=radioClicked)

    R3.grid(row=4, column=0, pady=(7, 0), padx=(10, 30), sticky="w")

    R4 = Radiobutton(root,
                     text="Bottom Right",
                     variable=radio_var,
                     value=4,
                     command=radioClicked)

    R4.grid(row=5, column=0, pady=(7, 0), padx=(10, 30), sticky="w")

    l2 = Label(root, text="Input parking space ID: ")
    l2.config(font=("Courier", 14))
    l2.grid(row=9, column=0, pady=(7, 0), padx=(10, 30), sticky="w")

    # user_input = Text(root, height = 3, width = 33, bg = "light yellow")
    user_input = Entry(root, textvariable=parking_id)
    user_input.grid(row=10, column=0, pady=(7, 0), padx=(10, 30), ipadx=60, ipady=10, sticky="w")

    submit_btn = Button(root, text="Submit", command=submit)
    submit_btn.grid(row=12, column=0, pady=(7, 0), padx=(10, 30), sticky="e")

    reset_btn = Button(root, text="Reset", command=reset)
    reset_btn.grid(row=12, column=0, pady=(7, 0), padx=(10, 30), sticky="w")

    print ("Hi")
    root.mainloop()
    print ("bye")

def loadGUI():

    # global image_reset
    # global temp

    createWindow()
    cv2.imshow("Image", img)
    # print(image_reset)
    # if image_reset is False:
    #     cv2.imshow("Image", image_copy)
    # else:
    #     img_copy = img.copy()
    #     temp = img_copy
    #     cv2.imshow("Image", temp)
     #   image_reset = False
    # if image_reset is False:
    #     cv2.imshow('image', img)
    # elif image_reset is True:
    #     image_copy = img.copy()
    #     cv2.imshow("image", image_copy)
    # while (1):
    #     cv2.imshow('image', img)
    #     k = cv2.waitKey(0) & 0xFF
    #     if k == 27:
    #         break

def error():
    screen = Toplevel(root)
    screen.geometry("450x50")
    screen.title("Error!")
    Label(screen, text="The radio buttons have to be used and parking ID field have to be filled!", fg="red").pack()

def submit():
    global counter
    global submitted
    #when user clicks submit button
    parking_txt = parking_id.get()
    if parking_txt == "" or counter < 4:
        error()
    elif counter % 4 == 0 and parking_txt != "":
        submitted = True
        if submitted is True:
            # point_counter = 0
            print("Submitted is true")
            temp_list.clear()
        print (parking_txt)
        print("Submit BB: ", full_bounding_box)
        counter = 0
        return full_bounding_box
        return parking_txt

        print("Submitted after pressing button: ", submitted)

createMenu()

A = [[283, 330], [346,329], [309, 365], [381,360]]

B = [[282, 329], [345, 328], [308, 364], [380, 359]]

intersectionOverUnion(A, B)
from tkinter import *
import cv2

root = Tk()
root.geometry("350x330")
root.title("InnoPark")

global counter
counter = 0

img = cv2.imread("C:\\Users\\hassa\\PycharmProjects\\untitled1\\data\\parking_lot_1.png")
drawing = False
coordinates = []
coordinates_copy = []
global point_counter
point_counter = 0

parking_id = StringVar()
radio_var = IntVar()

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

    full_bounding_box = []

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

    full_bounding_box.append([top_left, top_right, bottom_left, bottom_right])
    print(full_bounding_box)
    return full_bounding_box

def drawLine():
    #uses the mouse clicks from user to draw lines to it
    #these coordinates are then passed to bounding box function

    #close window after each click to allow only one dot at a time
    global point_counter
    if (point_counter % 1 == 0):
        cv2.destroyWindow("image")

    #draw a line using the last two clicks
    if (point_counter >= 2):
        cv2.line(img, coordinates[-2], coordinates[-1], (0, 0, 255), 1)

    #after every 4 clicks, draw a line between the last and the first point to enclose it
    #copy the points to another list and pass that to bbox function and empty current list
    if (point_counter % 4 == 0):
        cv2.line(img,coordinates[3],coordinates[0],(0, 0, 255),1)
        coordinates_copy = coordinates.copy()
        getBoundingBoxCoordinates(coordinates_copy)
        point_counter = 0
        coordinates.clear()

def draw_circle(event,x,y, flags, param):
    #mouse callback function to allow user to draw on image

    global drawing

    #when user holds down mouse button, append the points to a list
    #increment counter for drawLine function
    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        coordinates.append((x, y))
        global point_counter
        point_counter += 1

    #when user lets go of mouse click, draw circle
    if event == cv2.EVENT_LBUTTONUP:
        drawing = False
        cv2.circle(img, center=(x,y), radius=3, color=(0,0,255), thickness=-1)
        drawLine()

def createWindow():
    #call mousecallback function in created window
    cv2.namedWindow('image')
    cv2.setMouseCallback('image', draw_circle)

def radioClicked():
    radio_btn = radio_var.get()
    global counter
    if (radio_btn == 1 or radio_btn == 2 or radio_btn == 3 or radio_btn == 4):
        counter += 1
        loadGUI()
        print(counter)


def loadGUI():
    createWindow()
    while (1):
        cv2.imshow('image', img)
        k = cv2.waitKey(1) & 0xFF
        if k == 27:
            break

def error():
    screen = Toplevel(root)
    screen.geometry("450x50")
    screen.title("Error!")
    Label(screen, text="The radio buttons have to be used and parking ID field have to be filled!", fg="red").pack()


def submit():
    #when user clicks submit button
    parking_txt = parking_id.get()
    if parking_txt == "" or counter < 4:
        error()
    else:
        #Label(root, text="Data recorded")
        print (parking_txt)
        return parking_txt

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
submit_btn.grid(row=11, column=0, pady=(7, 0), padx=(10, 30), sticky="e")

root.mainloop()

A = [[283, 330], [346,329], [309, 365], [381,360]]

B = [[282, 329], [345, 328], [308, 364], [380, 359]]

intersectionOverUnion(A, B)
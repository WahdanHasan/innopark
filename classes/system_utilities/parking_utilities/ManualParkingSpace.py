from tkinter import *
import cv2

image_window_name = "Parking Space Manual"
tkinter_thread = 0
radio_button_index = 0
parking_space_id = 0
parking_space_id_input = 0
parking_space_ids = []
invalid_point = [-5, -5]
bounding_box = [[-5, -5], [-5, -5], [-5, -5], [-5, -5]]
bounding_boxes = []
base_image = 0

def Load(camera):
    # Launches a tkinter window for option selecting and an opencv window for drawing points

    # Initialize tkinter items
    global radio_button_index
    global parking_space_id
    global tkinter_thread

    tkinter_thread = Tk()
    tkinter_thread.geometry("350x330") # This should scale with window size
    tkinter_thread.title("InnoPark Manual Parking")

    radio_button_index = IntVar()
    parking_space_id = StringVar()

    # Get base image to display
    global base_image
    # base_image = camera.GetScaledNextFrame()
    base_image = cv2.imread("..\\..\\..\\data\\reference footage\\images\\parking_lot_1.png")

    # Create the window for display and set the mouse event function for it
    cv2.namedWindow(image_window_name)
    cv2.setMouseCallback(image_window_name, MouseClickCallBack)
    DrawImage(image=base_image)

    # Launch tkinter menu
    InitializeMenu()


    # Once tkinter thread is stopped, destroy cv2 window and then return the parking space ids and bounding boxes
    cv2.destroyWindow(image_window_name)
    return (parking_space_ids, bounding_boxes)

def DrawImage(image):
    # Redraw the image provided after drawing lines and points on it

    # Draw lines and points
    DrawLines(image)
    DrawPoints(image)

    # Open the image
    cv2.imshow(image_window_name, image)

def DrawLines(image, color=(0, 0, 255)):
    # Draw lines from point pairs to each other

    global bounding_box

    # Draw lines
    if bounding_box[0] != invalid_point:
        if bounding_box[2] != invalid_point:
            cv2.line(image, bounding_box[0], bounding_box[2], color, 1)
        if bounding_box[1] != invalid_point:
            cv2.line(image, bounding_box[0], bounding_box[1], color, 1)

    if bounding_box[3] != invalid_point:
        if bounding_box[2] != invalid_point:
            cv2.line(image, bounding_box[3], bounding_box[2], color, 1)
        if bounding_box[1] != invalid_point:
            cv2.line(image, bounding_box[3], bounding_box[1], color, 1)

def DrawPoints(image, color=(0, 0, 255)):
    # Draw the points that are not set to the invalid point on the image provided

    for point in bounding_box:
        if point == invalid_point:
            continue

        cv2.circle(image, center=point, radius=3, color=color, thickness=-1)

def InitializeMenu():
    # Initialize and draw tkinter menu

    # Define title label
    label_title = Label(tkinter_thread, text="Select Bounding Box Corners:")

    # Set title label font
    label_title.config(font=("Courier", 14))

    # Position title label
    label_title.grid(row=0,
                     column=0,
                     pady=(7, 0),
                     padx=(10, 30),
                     sticky="e")

    # Create and set top left radio button
    tl_radio = Radiobutton(tkinter_thread,
                           text="Top Left",
                           variable=radio_button_index,
                           value=0)

    tl_radio.grid(row=1,
                  column=0,
                  pady=(7, 0),
                  padx=(10, 30),
                  sticky="w")

    # Create and set top right radio button
    tr_radio = Radiobutton(tkinter_thread,
                           text="Top Right",
                           variable=radio_button_index,
                           value=1)

    tr_radio.grid(row=3,
                  column=0,
                  pady=(7, 0),
                  padx=(10, 30),
                  sticky="w")

    # Create and set bottom left radio button
    bl_radio = Radiobutton(tkinter_thread,
                           text="Bottom Left",
                           variable=radio_button_index,
                           value=2)

    bl_radio.grid(row=4,
                  column=0,
                  pady=(7, 0),
                  padx=(10, 30),
                  sticky="w")

    # Create and set bottom right radio button
    br_radio = Radiobutton(tkinter_thread,
                           text="Bottom Right",
                           variable=radio_button_index,
                           value=3)

    br_radio.grid(row=5,
                  column=0,
                  pady=(7, 0),
                  padx=(10, 30),
                  sticky="w")

    # Create and set parking id label
    label_parking_id = Label(tkinter_thread, text="Input parking space ID: ")

    label_parking_id.config(font=("Courier", 14))

    label_parking_id.grid(row=9,
                          column=0,
                          pady=(7, 0),
                          padx=(10, 30),
                          sticky="w")

    
    # Create and set parking id text box
    global parking_space_id_input
    parking_space_id_input = Entry(tkinter_thread,
                                   textvariable=parking_space_id)

    parking_space_id_input.grid(row=10,
                                column=0,
                                pady=(7, 0),
                                padx=(10, 30),
                                ipadx=60,
                                ipady=10,
                                sticky="w")
    
    # Create and set submit button
    submit_btn = Button(tkinter_thread, text="Submit", command=SubmitButtonCallBack)
    submit_btn.grid(row=12,
                    column=0,
                    pady=(7, 0),
                    padx=(10, 30),
                    sticky="e")
    
    # Create and set next button
    next_btn = Button(tkinter_thread,
                      text="Set Box",
                      command=NextBox)

    next_btn.grid(row=12,
                  column=0,
                  pady=(7, 0),
                  padx=(10, 30),
                  sticky="w")

    # Start tkinter thread
    tkinter_thread.mainloop()

def MouseClickCallBack(event, x, y, flags, param):
    # When the user clicks on the image, the appropriate bounding box point is modified
    valid = 0
    idx = 0

    if event != cv2.EVENT_LBUTTONDOWN:
        return

    # Get the index chosen from the radio button
    index = radio_button_index.get()

    # Write new bounding box value
    bounding_box[index] = [x, y]

    for idx, _ in enumerate(bounding_box):
        if bounding_box[idx] != invalid_point:
            valid += 1
            print(valid)

    # Check for bounding box pt intersection
    if valid > 3:
        if (bounding_box[1][0] < min(bounding_box[0][0], bounding_box[2][0])):
            print("Lines cannot intersect1")
            bounding_box[index] = invalid_point
        if ((bounding_box[1][0] < max(bounding_box[2][0], bounding_box[3][0]) and bounding_box[1][1] > max(bounding_box[2][1], bounding_box[3][1]))):
            print("Lines cannot intersect2")
            bounding_box[index] = invalid_point
        if (bounding_box[2][0] > max(bounding_box[1][0], bounding_box[3][0])):
            print("Lines cannot intersect3")
            bounding_box[index] = invalid_point
        if ((bounding_box[2][0] < max(bounding_box[0][0], bounding_box[1][0]) and bounding_box[2][1] < max(bounding_box[0][1], bounding_box[1][1]))):
            print("Lines cannot intersect4")
            bounding_box[index] = invalid_point
        if (bounding_box[0][0] > max(bounding_box[1][0], bounding_box[3][0])):
            print("Lines cannot intersect5")
            bounding_box[index] = invalid_point
        if (bounding_box[3][0] < max(bounding_box[0][0], bounding_box[2][0])):
            print("Lines cannot intersect6")
            bounding_box[index] = invalid_point
        if ((bounding_box[3][0] < max(bounding_box[0][0], bounding_box[1][0]) and bounding_box[3][1] < max(bounding_box[0][1], bounding_box[1][1]))):
            print("Lines cannot intersect7")
            bounding_box[index] = invalid_point
    print(bounding_box)

    # Redraw image
    image = base_image.copy()
    DrawImage(image)

def NextBox():
    # When the user goes to the next box, we paint the old box into the base image and
    # reset any variables

    global bounding_box
    global parking_space_id

    # Check if all points have been drawn, if they have, return
    for box in bounding_box:
        if box == invalid_point:
            Error()
            return

    # Check if parking space id is empty, if it is, return
    if len(parking_space_id.get()) == 0:
        Error()
        return

    # Draw lines and points
    DrawLines(base_image, color=(0, 255, 0))
    # DrawPoints(base_image, color=(0, 255, 0))

    # Append box and id to list
    bounding_boxes.append(bounding_box)
    parking_space_ids.append(parking_space_id.get())

    # Reset bounding box and id
    bounding_box = [[-5, -5], [-5, -5], [-5, -5], [-5, -5]]
    parking_space_id_input.delete(0, END)

    # Redraw image
    DrawImage(base_image)

def SubmitButtonCallBack():
    # Stop tkinter thread.
    # It should be noted that that the Load function returns the bounding boxes and ids after the tkinter thread stops

    tkinter_thread.quit()

def Error():
    screen = Toplevel(tkinter_thread)
    screen.geometry("450x50")
    screen.title("Error!")
    Label(screen, text="The radio buttons have to be used and parking ID field have to be filled!", fg="red").pack()

Load(5)

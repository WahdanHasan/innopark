import cv2
from classes.Camera.Camera import Camera
import classes.SystemUtilities.ImageUtilities as IU

x = Camera("data\\reference footage\\IP7_Test.mov", 0)
img = cv2.imread("data\\reference footage\\example_1.PNG")

while True:
    frame = x.GetNextFrame()

    frame = IU.RescaleImage(frame, 0.5)

    cv2.imshow("Feed", frame)

    #text = IU.GetTextFromImage(img)

    #print(text)

    if cv2.waitKey(10) & 0xFF == ord('q'):
        cv2.destroyAllWindows()

cv2.waitKey(0)
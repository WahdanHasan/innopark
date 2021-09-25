import cv2

class SubtractionModel:
    # As this form of object detection builds on the output of a stationary camera, it is essentially tied to that
    # camera. Due to this, we must treat it as a class of its own so that we may create multiple copies of it to be
    # used on a per stationary camera basis.

    def __init__(self, detectShadows=False, history=100):
        # Initialize subtraction object detection model

        self.subtraction_model = cv2.createBackgroundSubtractorMOG2(history=history)
        self.subtraction_model.setDetectShadows(detectShadows)
        self.subtraction_model_output_mask = 0

    def FeedSubtractionModel(self, image, learningRate=-1):
        # This function is to be called once per iteration if DetectMovingObjects is being used.

        self.subtraction_model_output_mask = self.subtraction_model.apply(image, learningRate=learningRate)

        # Filter out shadows
        # _, self.subtraction_model_output_mask = cv2.threshold(self.subtraction_model_output_mask, 254, 255, cv2.THRESH_BINARY)


    def GetOutput(self):
        return self.subtraction_model_output_mask

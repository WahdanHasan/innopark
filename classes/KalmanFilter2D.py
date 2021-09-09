import numpy as np
import cv2 as cv2

class KalmanFilter2D(object):
    def __init__(self, dt, x_control_acc_value, y_control_acc_value,
                 std_acc, x_std_measurement, y_std_measurement) -> None:

        self._x = np.matrix([[0], [0], [0], [0]])

        self._dt = dt

        self._control_acc_value = np.matrix([[x_control_acc_value], [y_control_acc_value]])
        self._std_acc = std_acc
        self._x_std_measurement = x_std_measurement
        self._y_std_measurement = y_std_measurement

        self._A = np.matrix([[1, 0, self._dt, 0],
                             [0, 1, 0, self._dt],
                             [0, 0, 1, 0],
                             [0, 0, 0, 1]])

        self._B = np.matrix([[(self._dt**2)/2, 0],
                             [0, (self._dt**2)/2],
                             [self._dt, 0],
                             [0, self._dt]])


        self._Q = np.matrix([[(self._dt**4)/4, 0, (self._dt**3)/2, 0],
                             [0, (self._dt**4)/4, 0, (self._dt**3)/2],
                             [(self._dt**3)/2, 0, self._dt**2, 0],
                             [0, (self._dt**3)/2, 0, self._dt**2]]) * self._std_acc**2

        self._H = np.matrix([[1, 0, 0, 0], [0, 1, 0, 0]])

        self._R = np.matrix([[self._x_std_measurement**2, 0],
                             [0, self._y_std_measurement**2]])

        self._P = np.eye(self._A.shape[1])

    def predict(self) -> np.matrix:
        new_x = self._A.dot(self._x) + self._B.dot(self._control_acc_value)

        new_P = self._A.dot(self._P).dot(self._A.T) + self._Q

        self._x = new_x
        self._P = new_P

        converted_x = self._x[:2].tolist()
        #print("prediction set ", converted_x)

        return converted_x

    def update(self, measurement_value) -> np.matrix:
        z = measurement_value

        S = self._H.dot(self._P).dot(self._H.T) + self._R

        K = self._P.dot(self._H.T).dot(np.linalg.inv(S))

        y = z - self._H.dot(self._x)

        new_x = np.round(self._x + K.dot(y))

        identity_matrix = np.eye(self._H.shape[1])

        new_P = (identity_matrix - (K*self._H))*self._P

        self._x = new_x
        self._P = new_P

        # converting matrix to np array
        #converted_x = np.asarray(self._x[:1]).reshape(-1)

        converted_x = self._x[:2].tolist()
        #print("update set: ", converted_x)
        return converted_x

    @property
    def transformation_matrix(self) -> np.matrix:
        return self._H

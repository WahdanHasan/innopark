import numpy as np

class KF(object):
    # will return nothing as it will just modify the state over time
    # private variables are denoted by a pre _
    def __init__(self, dt, control_acc_value, std_acc, std_measurement, initial_x=0, initial_v=0) -> None:
        #mean of state GRV
        #self._x = np.array([initial_x, initial_v]) #intial values should be bbox

        # the other paper initializes x to this
        self._x = np.matrix([[0], [0]])

        self._dt = dt
        self._control_acc_value = control_acc_value #optional
        self._std_acc = std_acc
        self._std_measurement = std_measurement

        # values used for prediction
        self._A = np.matrix([[1, self._dt], [0, 1]])
        self._B = np.matrix([[(self._dt ** 2) / 2], [self._dt]])

        # calculate error covariance
        # self._Q = np.array([0.5 * dt**2, dt]).reshape((2, 1))
        # another paper calculating Q differently
        self._Q = np.matrix([[(self._dt ** 4) / 4, (self._dt ** 3) / 2],
                             [(self._dt ** 3) / 2, self._dt ** 2]]) * self._std_acc ** 2

        # values used for update
        self._H = np.matrix([[1, 0]])  # same as np.array([1, 0]).reshape((1, 2))

        # self._R = np.array([self._std_measurement])
        # on another paper
        self._R = self._std_measurement ** 2

        #covariance of state (the noise variable)
        self._P = np.eye(self._A.shape[1])

    # predict func = time update equation
    # projects forward current state and error covariance estimates to get next time step (prioro)
    # predict func should increase state uncertainty
    # dt: time for 1 cycle
    def predict(self) -> np.matrix:
        # update time state
        # x = A * x
        # new_x = self._A.dot(self._x)

        # another paper version of new_x, adding control to acc
        # and adds velocity to the calculation of the state vector x
        new_x = self._A.dot(self._x) + self._B.dot(self._control_acc_value)

        # At: A transposed/ Gt: G transposed
        # P = A * P * At + G * Gt * a
        # new_P = self._A.dot(self._P).dot(self._A.T) + self._Q.dot(self._Q.T) * self._std_acc

        #another paper calculating P differently
        new_P = self._A.dot(self._P).dot(self._A.T) + self._Q.T

        self._P = new_P
        self._x = new_x

        return self._x

    # update func = measurement update equation or the corrector equation
    # improves state and error covariance (posterioro) by incorporating a new measurement into the predicted estimates (prioro)
    # update func should not decrease the state's uncertainty
    def update(self, measurement_value) -> None:
        # y = z - H * x
        # S = H * P * Ht + R

        # x = x + K * y
        # P = (I - K * H) * P # note very stable find another

        z = measurement_value

        S = self._H.dot(self._P).dot(self._H.T) + self._R

        # Kalman Gain
        # K = P * Ht * S^-1
        K = self._P.dot(self._H.T).dot(np.linalg.inv(S)) #might be better to have sudo inverse instead

        y = z - self._H.dot(self._x)

        # new_x = self._x + K.dot(y)
        # another paper rounds new_x
        new_x = np.round(self._x + K.dot(y))

        identity_matrix = np.eye(self._H.shape[1])
        # new_P = (identity_matrix - K.dot(self._H)).dot(self._P)
        new_P = (identity_matrix - (K*self._H))*self._P

        self._P = new_P
        self._x = new_x

    @property
    def mean(self)-> np.matrix:
        return self._x

    @property
    def covariance(self)-> np.matrix:
        return self._P

    @property
    def position(self) -> float:
        return self._x[0]

    @property
    def velocity(self) -> float:
        return self._x[1]

    @property
    def transformation_matrix(self)->np.matrix:
        return self._H


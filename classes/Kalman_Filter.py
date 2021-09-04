import numpy as np

class KF:
    # will return nothing as it will just modify the state over time
    # private variables are denoted by a pre _
    def __init__(self, initial_x: float, initial_v: float, a: float) -> None:
        #mean of state GRV
        self._x = np.array([initial_x, initial_v])
        self._a = a

        #covariance of state GRV (the noise variable)
        # TO-DO: should find a way to calculate it
        self._P = np.eye(2)

    # predict func should increase state uncertainty
    # dt: change in time
    def predict(self, dt: float) -> None:
        # x = F * x
        # Ft: F transposed/ Gt: G transposed
        # P = F * P * Ft + G * Gt * a
        F = np.array([[1, dt], [0, 1]])
        new_x = F.dot(self._x)

        G = np.array([0.5 * dt**2, dt]).reshape((2, 1))
        new_P = F.dot(self._P).dot(F.T) + G.dot(G.T) * self._a

        self.P = new_P


    # update func should not decrease the state's uncertainty
    def update(self, measurement_value: float, measurement_variance: float) -> None:
        # y = z - H * x
        # S = H * P * Ht + R
        # K = P *Ht * S^-1
        # x = x + K * y
        # P = (I - K * H) * P # note very stable find another

        H = np.array([1, 0]).reshape((1, 2))

        # not necessary to convert to np array, but for the sake of consistency
        z = np.array([measurement_value])
        R = np.array([measurement_variance])

        y = z - H.dot(self._x)
        S = H.dot(self._P).dot(H.T) + R

        K = self._P.dot(H.T).dot(np.linalg.inv(S)) #might be better to have sudo inverse instead

        new_x = self._x + K.dot(y)
        new_P = (np.eye(2) - K.dot(H)).dot(self._P)

        self._P = new_P
        self._x = new_x

    @property
    def mean(self)-> np.array:
        return self._x

    @property
    def covariance(self)-> np.array:
        return self._P

    @property
    def position(self) -> float:
        return self._x[0]

    @property
    def velocity(self) -> float:
        return self._x[1]



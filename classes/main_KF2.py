import numpy as np
import matplotlib.pyplot as plt

from Kalman_Filter import KF

dt = 0.1
t = np.arange(0, 100, dt)
# Define a model track
real_track = 0.1 * ((t ** 2) - t)
u = 2
std_acc = 0.25  # we assume that the standard deviation of the acceleration is 0.25 (m/s^2)
std_meas = 1.2  # and standard deviation of the measurement is 1.2 (m)
# create KalmanFilter object
kf = KF(dt, u, std_acc, std_meas)
predictions = []
measurements = []
for x in real_track:
    # Mesurement
    z = kf.transformation_matrix * x + np.random.normal(0, 50)
    measurements.append(z.item(0))
    predictions.append(kf.predict()[0])
    kf.update(z.item(0))
fig = plt.figure()
fig.suptitle('Example of Kalman filter for tracking a moving object in 1-D', fontsize=20)
plt.plot(t, measurements, label='Measurements', color='b', linewidth=0.5)
plt.plot(t, np.array(real_track), label='Real Track', color='y', linewidth=1.5)
plt.plot(t, np.squeeze(predictions), label='Kalman Filter Prediction', color='r', linewidth=1.5)
plt.xlabel('Time (s)', fontsize=20)
plt.ylabel('Position (m)', fontsize=20)
plt.legend()
plt.show()


# real_x = 0.0
# meas_variance = 0.1 ** 2
# real_v = 0.5
#
# kf = KF(initial_x=0.0, initial_v=1.0, accel_variance=0.1)
#
# DT = 0.1
# NUM_STEPS = 1000
# MEAS_EVERY_STEPS = 20
#
# mus = []
# covs = []
# real_xs = []
# real_vs = []
#
# for step in range(NUM_STEPS):
#     if step > 500:
#         real_v *= 0.9
#
#     covs.append(kf.cov)
#     mus.append(kf.mean)
#
#     real_x = real_x + DT * real_v
#
#     kf.predict(dt=DT)
#     if step != 0 and step % MEAS_EVERY_STEPS == 0:
#         kf.update(meas_value=real_x + np.random.randn() * np.sqrt(meas_variance),
#                   meas_variance=meas_variance)
#
#     real_xs.append(real_x)
#     real_vs.append(real_v)
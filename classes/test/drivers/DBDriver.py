from datetime import datetime

# from classes.system_utilities.data_utilities import DatabaseUtilities as DU
from classes.system_utilities.data_utilities import Avenues

import time


start = datetime.now()

time.sleep(5)
end = datetime.now()

time_elapsed = end - start


print(type(time_elapsed.seconds))


# Avenues.AddSession(avenue="O8483qKcEoQc6SPTDp5e", vehicle="J71612", parking_id=188, start_datetime=datetime.now())


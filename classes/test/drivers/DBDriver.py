from datetime import datetime

# from classes.system_utilities.data_utilities import DatabaseUtilities as DU
from classes.system_utilities.data_utilities import Avenues

import time


start = datetime.now()

time.sleep(5)
end = datetime.now()

time_elapsed = end - start


print(type(time_elapsed.seconds))




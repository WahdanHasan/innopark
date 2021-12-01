from classes.system_utilities.helper_utilities.Enums import ImageResolution
from datetime import datetime

base_pool_size = 3
seconds_in_hour = 3600

# Don't delete me. Trackers will stop working :(
bb_shared_memory_manager_prefix = "tracked_object_bb_shared_memory_manager_"
tracked_process_ids_shared_memory_prefix = "tracked_object_ids_in_shared_memory_manager_"
frame_shared_memory_prefix = "frame_in_shared_memory_"
object_tracker_mask_shared_memory_prefix = "object_tracker_mask_in_shared_memory_"
parking_tariff_management_shared_memory_prefix = "parking_tariff_in_shared_memory_"
parking_space_shared_memory_prefix = "parking_space_shared_memory_"
parking_violation_management_shared_memory_prefix = "parking_violation_in_shared_memory_"

bb_example = [[-1, -1], [-1, -1]]
# idx0=tracker_id, idx1=camera_id, rest are the object_id
tracked_process_ids_example = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# idx0=parking space number, idx1= parking space occupancy status [1 is occupied], rest are object_id
ptm_debug_items_example = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


# [id, link]
ENTRANCE_CAMERA_DETAILS = [
                            [0, "data\\reference footage\\test journey\\Entrance_Top.mp4"],
                            [1, "data\\reference footage\\test journey\\Entrance_Bottom.mp4"]
                          ]

CAMERA_DETAILS = [
                    [2, "data\\reference footage\\test journey\\Leg_1.mp4"],
                    [3, "data\\reference footage\\test journey\\Leg_2.mp4"]
                 ]


default_camera_shape = (ImageResolution.SD.value[0], ImageResolution.SD.value[1], 3)


# Parking space file
parking_spaces_json = "config\\parking\\parking_spaces.txt"

gov_license_key = "licenseNumber"
gov_phone_number_key = "phoneNumber"

# Avenue information
avenue_id = "O8483qKcEoQc6SPTDp5e"
# avenue_id = "sXXjDt9IUyPBDaCmLTfF"
parking_due_in_hours = 48
fine_due_in_months = 1
max_parking_duration_in_hours = 4

# Fine Types
fine_type_double_parking = "Double Parking"
fine_type_exceeded_due_date = "Exceeded Due Date"
fine_type_exceeded_allowed_duration = "Exceeded Allowed Duration"

# Fine Amounts
fine_amount_double_parking = 500
fine_amount_exceeded_due_date = 350
fine_amount_exceeded_allowed_duration = 200


local_timezone = datetime.now().astimezone().tzinfo
# print("timezone: ", datetime.now(local_timezone))


# avenues doc
avenues_collection_name = "avenues"
fines_info_subcollection_name = "fines_info"
sessions_info_subcollection_name = "sessions_info"

# Fine_info doc
created_datetime_key = "created_datetime"
due_datetime_key = "due_datetime"
fine_amount_key = "fine_amount"
fine_description_key = "fine_description"
fine_type_key = "fine_type"
is_accepted_key = "is_accepted"
is_reviewed_key = "is_reviewed"
is_disputed_key = "is_disputed"
is_paid_key = "is_paid"
session_id_key = "session_id"
vehicle_key = "vehicle"

# Parking_info doc
bounding_box_key = "bounding_box"
camera_id_key = "camera_id"
is_occupied_key = "is_occupied"
parking_type_key = "parking_type"
rate_per_hour_key = "rate_per_hour"

# SMS
sms_enabled = True

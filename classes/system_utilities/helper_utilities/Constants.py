from classes.system_utilities.helper_utilities.Enums import ImageResolution

base_pool_size = 10
seconds_in_hour = 3600
ot_bb_area_difference_percentage_threshold = 10
ot_seconds_before_scan = 0.3
ot_seconds_before_scan_growth = 0.0
subtraction_model_learning_rate = 0.0001

INT_MAX = 999999

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

# idx0=parking space number, idx1= parking space occupancy status, rest are object_id
ptm_debug_items_example = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


# [id, link]
ENTRANCE_CAMERA_DETAILS = [
                            [0, "data\\journeys\\set_2l\\et.mp4"],
                            [1, "data\\journeys\\set_2l\\eb.mp4"]
                          ]

CAMERA_DETAILS = [
                    [2, "data\\journeys\\set_2l\\l1.mp4"],
                    [3, "data\\journeys\\set_2l\\l2.mp4"],
                    [4, "data\\journeys\\set_2l\\l3.mp4"]
                 ]


default_camera_shape = (ImageResolution.NTSC.value[0], ImageResolution.NTSC.value[1], 3)

# bb_movement_threshold =


# Parking space file
parking_spaces_json = "config\\parking\\parking_spaces.txt"

gov_license_key = "licenseNumber"
gov_phone_number_key = "phoneNumber"

# Avenue information
avenue_id = "O8483qKcEoQc6SPTDp5e"
# avenue_id = "sXXjDt9IUyPBDaCmLTfF"

# Parking_info doc
bounding_box_key = "bounding_box"
occupancy_box_key = "occupancy_box"
camera_id_key = "camera_id"
is_occupied_key = "is_occupied"
parking_type_key = "parking_type"
rate_per_hour_key = "rate_per_hour"

# SMS
sms_enabled = True

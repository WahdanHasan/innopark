from classes.system_utilities.helper_utilities.Enums import ImageResolution

base_pool_size = 3

# Don't delete me. Trackers will stop working :(
bb_shared_memory_manager_prefix = "tracked_object_bb_shared_memory_manager_"
tracked_process_ids_shared_memory_prefix = "tracked_object_ids_in_shared_memory_manager_"
frame_shared_memory_prefix = "frame_in_shared_memory_"
object_tracker_mask_shared_memory_prefix = "object_tracker_mask_in_shared_memory_"
parking_tariff_management_shared_memory_prefix = "parking_tariff_in_shared_memory_"

bb_example = [[-1, -1], [-1, -1]]
# idx0=tracker_id, idx1=camera_id, rest are the object_id
tracked_process_ids_example = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

# [id, link]
ENTRANCE_CAMERA_DETAILS = [
                            [0, "data\\reference footage\\test journey\\Entrance_Top.mp4"],
                            [1, "data\\reference footage\\test journey\\Entrance_Bottom_Simulated_2.mp4"]
                          ]

CAMERA_DETAILS = [
                    [2, "data\\reference footage\\test journey\\Leg_1.mp4"],
                    [3, "data\\reference footage\\test journey\\Leg_2.mp4"]
                 ]


default_camera_shape = (ImageResolution.SD.value[0], ImageResolution.SD.value[1], 3)


# Parking space file
parking_spaces_json = "config\\parking_spaces.txt"


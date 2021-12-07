import cv2
# import pixellib
# from pixellib.instance import instance_segmentation
# from pixellib.semantic import semantic_segmentation
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
# from classes.camera.CameraBuffered import Camera
# from classes.system_utilities.image_utilities import ObjectDetection as OD
from classes.system_utilities.image_utilities import ImageUtilities as IU
from classes.system_utilities.helper_utilities import Constants
from classes.system_utilities.helper_utilities import Enums
import time
#

parking_spaces =[
  {
    "camera_id": 4,
    "parking_id": "632",
    "parking_type": "a",
    "rate_per_hour": 5,
    "bounding_box": [
      [
        194,
        128
      ],
      [
        258,
        128
      ],
      [
        208,
        154
      ],
      [
        304,
        156
      ]
    ],
    "occupancy_box": [
      [
        201,
        91
      ],
      [
        300,
        91
      ],
      [
        201,
        157
      ],
      [
        300,
        157
      ]
    ]
  },
  {
    "camera_id": 4,
    "parking_id": "633",
    "parking_type": "a",
    "rate_per_hour": 5,
    "bounding_box": [
      [
        129,
        126
      ],
      [
        194,
        128
      ],
      [
        112,
        153
      ],
      [
        208,
        154
      ]
    ],
    "occupancy_box": [
      [
        125,
        90
      ],
      [
        196,
        90
      ],
      [
        125,
        151
      ],
      [
        196,
        151
      ]
    ]
  },
  {
    "camera_id": 4,
    "parking_id": "634",
    "parking_type": "a",
    "rate_per_hour": 5,
    "bounding_box": [
      [
        62,
        126
      ],
      [
        129,
        126
      ],
      [
        13,
        152
      ],
      [
        112,
        153
      ]
    ],
    "occupancy_box": [
      [
        32,
        89
      ],
      [
        111,
        89
      ],
      [
        32,
        151
      ],
      [
        111,
        151
      ]
    ]
  },
  {
    "camera_id": 3,
    "parking_id": "635",
    "parking_type": "b",
    "rate_per_hour": 10,
    "bounding_box": [
      [
        208,
        148
      ],
      [
        258,
        150
      ],
      [
        237,
        172
      ],
      [
        309,
        176
      ]
    ],
    "occupancy_box": [
      [
        223,
        117
      ],
      [
        304,
        117
      ],
      [
        223,
        178
      ],
      [
        304,
        178
      ]
    ]
  },
  {
    "camera_id": 3,
    "parking_id": "636",
    "parking_type": "b",
    "rate_per_hour": 10,
    "bounding_box": [
      [
        157,
        145
      ],
      [
        208,
        148
      ],
      [
        163,
        167
      ],
      [
        237,
        172
      ]
    ],
    "occupancy_box": [
      [
        161,
        116
      ],
      [
        236,
        116
      ],
      [
        161,
        165
      ],
      [
        236,
        165
      ]
    ]
  },
  {
    "camera_id": 3,
    "parking_id": "637",
    "parking_type": "b",
    "rate_per_hour": 10,
    "bounding_box": [
      [
        105,
        141
      ],
      [
        156,
        145
      ],
      [
        87,
        163
      ],
      [
        163,
        167
      ]
    ],
    "occupancy_box": [
      [
        100,
        111
      ],
      [
        158,
        111
      ],
      [
        100,
        164
      ],
      [
        158,
        164
      ]
    ]
  },
  {
    "camera_id": 3,
    "parking_id": "638",
    "parking_type": "b",
    "rate_per_hour": 10,
    "bounding_box": [
      [
        49,
        139
      ],
      [
        105,
        141
      ],
      [
        9,
        160
      ],
      [
        87,
        163
      ]
    ],
    "occupancy_box": [
      [
        36,
        108
      ],
      [
        90,
        108
      ],
      [
        36,
        165
      ],
      [
        90,
        165
      ]
    ]
  },
  {
    "camera_id": 2,
    "parking_id": "639",
    "parking_type": "c",
    "rate_per_hour": 20,
    "bounding_box": [
      [
        232,
        156
      ],
      [
        294,
        158
      ],
      [
        213,
        177
      ],
      [
        300,
        181
      ]
    ],
    "occupancy_box": [
      [
        223,
        124
      ],
      [
        287,
        124
      ],
      [
        223,
        175
      ],
      [
        287,
        175
      ]
    ]
  },
  {
    "camera_id": 2,
    "parking_id": "640",
    "parking_type": "c",
    "rate_per_hour": 20,
    "bounding_box": [
      [
        174,
        154
      ],
      [
        232,
        156
      ],
      [
        132,
        175
      ],
      [
        213,
        177
      ]
    ],
    "occupancy_box": [
      [
        163,
        122
      ],
      [
        224,
        122
      ],
      [
        163,
        176
      ],
      [
        224,
        176
      ]
    ]
  },
  {
    "camera_id": 2,
    "parking_id": "641",
    "parking_type": "c",
    "rate_per_hour": 20,
    "bounding_box": [
      [
        119,
        152
      ],
      [
        174,
        154
      ],
      [
        55,
        171
      ],
      [
        132,
        174
      ]
    ],
    "occupancy_box": [
      [
        82,
        122
      ],
      [
        168,
        122
      ],
      [
        82,
        168
      ],
      [
        168,
        168
      ]
    ]
  },
  {
    "camera_id": 2,
    "parking_id": "642",
    "parking_type": "c",
    "rate_per_hour": 20,
    "bounding_box": [
      [
        63,
        151
      ],
      [
        119,
        152
      ],
      [
        0,
        166
      ],
      [
        55,
        171
      ]
    ],
    "occupancy_box": [
      [
        19,
        120
      ],
      [
        96,
        120
      ],
      [
        19,
        163
      ],
      [
        96,
        163
      ]
    ]
  }
]

occupied_parking_ids = ["636", "635"]
parking_occupants = ["J71612", "W68133", "A12345"]

current_car = "W68133"

# TODO: ADD CAMERA CHECK WHEN CHECKING FOR CONSECUTIVE PARKING SPACES

def main():

    frame = cv2.imread("./data/reference footage/images/car_parked2_new.jpg")
    frame = IU.RescaleImageToResolution(img=frame, new_dimensions=(Constants.default_camera_shape[0], Constants.default_camera_shape[1]))
    cv2.imshow("rescaled", frame)

    # get occupied parking ids
    # get their occupants
    for i in range(len(occupied_parking_ids)):

        # get the parking spaces bboxes
        for parking_space in parking_spaces:
            if parking_space["parking_id"] == occupied_parking_ids[i]:
                parking_bbox = parking_space["bounding_box"]
                print(parking_bbox)

                # temp_img = IU.DrawParkingSideLines(image=frame, bounding_box=parking_bbox)

                temp_img = IU.DrawParkingBoxes(image=frame, bounding_boxes=[parking_bbox], are_occupied=[Enums.ParkingStatus.NOT_OCCUPIED])

                cv2.imshow("temp", temp_img)
                cv2.waitKey(0)


    # segment_image = semantic_segmentation()
    # segment_image.load_pascalvoc_model("./config/maskrcnn/deeplabv3_xception_tf_dim_ordering_tf_kernels.h5")
    # result = segment_image.segmentFrameAsPascalvoc(frame)
    # mask = result[1]

    # cv2.imshow("img", mask)





if __name__ == "__main__":
    main()

import classes.system_utilities.data_utilities.DatabaseUtilities as db
from datetime import datetime

now = datetime.now()

conn = db.GetDbConnection()

collection = "avenues"

avenue_id = "zFRQSZWp2gUm9avdWVPZ"

def GetAllAvenues():
    doc = db.GetDocuments(collection)
    print("Avenues: ", doc)

def GetParkingWithRequestedField(avenue_id, key, value):
    # avenues.GetParkingWithRequestedField(avenue_id="zFRQSZWp2gUm9avdWVPZ", key="camera_id", value=0)
    doc = db.GetFirstDocWithRequestedField("avenues/"+avenue_id+"/parkings_info", key, value)

    if not doc:
        print("Error: requested parking info is not found")
        return

    print("Parking Info: ", doc)

def GetAllParkingSessions():
    print("hi")

def AddParking(avenue, camera_id, bounding_box, is_occupied=False, parking_type=None):
    # avenues.AddParking(avenue="O8483qKcEoQc6SPTDp5e", camera_id=2,
    #                    bounding_box=[200, 100, 300, 150, 250, 100, 100, 150], is_occupied=None, parking_type=None)
    db.AddData(collection="avenues/"+avenue+"/parkings_info",
               data={"bounding_box": bounding_box,
                     "camera_id": camera_id,
                     "is_occupied": is_occupied,
                     "parking_type": parking_type})


def AddAvenue(gps_coordinate, name, parking_types=None):
    # avenues.AddAvenue("120.40.60", "Marina Mall", {"a":40, "b":60})
    db.AddData(collection="avenues",
               data={"gps_coordinate": gps_coordinate, "name": name, "parking_types": parking_types})

def AddSession(avenue, vehicle, start_datetime=now, end_datetime=None, tariff_amount=0):
    # avenues.AddSession(avenue="O8483qKcEoQc6SPTDp5e", vehicle="J71612",
    #                    start_datetime="20/11 20:00", end_datetime="20/11 15:00",
    #                    tariff_amount=80)
    db.AddData(collection="avenues/"+avenue+"/sessions_info",
               data={"end_datetime":end_datetime,
                     "start_datetime":start_datetime,
                     "tariff_amount": tariff_amount,
                     "vehicle": vehicle})

def GetAllParkingSession(avenue):
    docs_id, docs = db.GetAllDocuments("avenues/"+avenue+"/parkings_info")

    bbox_converted = []
    bbox = []

    for doc in docs:
        bbox = doc["bounding_box"]
        bbox_converted.append([bbox[0], bbox[1]])
        bbox_converted.append([bbox[2], bbox[3]])
        bbox_converted.append([bbox[4], bbox[5]])
        bbox_converted.append([bbox[6], bbox[7]])
        doc["bounding_box"] = bbox_converted

    return docs_id, docs

def GetParkingSession(avenue):
    docs_id, docs = db.GetAllDocuments("avenues/" + avenue + "/parkings_info")
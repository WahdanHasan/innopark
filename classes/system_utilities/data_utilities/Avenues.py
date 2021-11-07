import classes.system_utilities.data_utilities.DatabaseUtilities as db
from datetime import datetime, timedelta, timezone
from classes.system_utilities.helper_utilities.Constants import avenue_id

# now = datetime.now(timezone.utc).astimezone()

parking_due_in_hours = 48

conn = db.GetDbConnection()

collection = "avenues"

#below to be deleted afterwards
# avenue_id = "O8483qKcEoQc6SPTDp5e"
# avenue_id = "sXXjDt9IUyPBDaCmLTfF"

def GetAllAvenues():
    doc = db.GetDocuments(collection)
    print("Avenues: ", doc)

    return doc

def AddParking(avenue, camera_id, parking_id, bounding_box, parking_type, is_occupied=False):
    # avenues.AddParking(avenue="O8483qKcEoQc6SPTDp5e", camera_id=2,
    #                    bounding_box=[200, 100, 300, 150, 250, 100, 100, 150], parking_type="a")

    if len(bounding_box)!=8:
        print("ERROR: Couldn't add parking. Bounding box must contain 8 values.")
        return

    rate_per_hour = GetRatePerHourFromAvenueInfo(avenue, parking_type)

    db.AddData(collection=collection+"/"+avenue+"/parkings_info",
               document=str(parking_id),
               data={"bounding_box": bounding_box,
                     "camera_id": camera_id,
                     "is_occupied": is_occupied,
                     "parking_type": parking_type,
                     "rate_per_hour": rate_per_hour})


def AddAvenue(gps_coordinate, name, parking_types={"a":0}):
    # avenues.AddAvenue("120.40.60", "Marina Mall", {"a":40, "b":60})
    db.AddData(collection=collection,
               data={"gps_coordinate": gps_coordinate, "name": name, "parking_types": parking_types})

# def UpdateAvenueParkingTypes(avenue, parking_types):
#     # parking_types = {"a":40, "b":60}
#     db.UpdateData(collection, avenue, "parking_types", parking_types)

def UpdateAvenueParkingType(avenue, parking_type, rate_per_hour):
    # call when wanting to update avenue parking type
    # the rate per hour in every parking in parking_info will also be updated
    db.UpdateDataInMap(collection=collection, document=avenue,
                  field_key="parking_types", map_key=str(parking_type), new_value=rate_per_hour)

    UpdateParkingRatePerHour(avenue, parking_type, rate_per_hour)

def UpdateParkingRatePerHour(avenue, parking_type, rate_per_hour):
    # update the rate per hour field of parkings with the specified parking type
    docs_id_extracted, docs_extracted = db.GetAllDocsEqualToRequestedField(collection=collection+"/"+avenue+"/parkings_info",
                                          key="parking_type", value=str(parking_type))

    for parking_id in docs_id_extracted:
        db.UpdateData(collection=collection+"/"+avenue+"/parkings_info", document=parking_id,
                      field_to_edit="rate_per_hour", new_data=rate_per_hour)

def AddSession(avenue, vehicle, parking_id, start_datetime, end_datetime=None, due_datetime=None, tariff_amount=0, is_paid=False):
    # call this method when vehicle enters innopark parking
    # AddSession(avenue=avenue_id, vehicle="J71612", parking_id="tFBKRtIKxIaUfygXBXfw")

    rate_per_hour = GetRatePerHourFromParkingInfo(avenue, parking_id)

    document_ref =  db.AddData(collection=collection+"/"+avenue+"/sessions_info",
                      data={"end_datetime":end_datetime,
                            "start_datetime":start_datetime,
                            "due_datetime":due_datetime,
                            "tariff_amount": tariff_amount,
                            "vehicle": vehicle,
                            "is_paid": is_paid,
                            "parking_id": parking_id,
                            "rate_per_hour": rate_per_hour})

    return document_ref[1].path.split("/")[3]
# def UpdateSessionParkingId(avenue, vehicle, parking_id):
#     # call this method when vehicle parks
#
#     docs_id_extracted, docs_extracted = db.GetAllDocsBasedOnTwoFields(collection+"/" + avenue + "/sessions_info",
#                                                                       "vehicle", vehicle, "parking_id")
#
#     session = docs_id_extracted[0]
#
#     db.UpdateData(collection=collection+"/" + avenue + "/sessions_info", document=session,
#                   field_to_edit="parking_id", new_data=parking_id)
#
#     UpdateSessionTariffAmount(avenue, session)
#
#
# def UpdateSessionEndDateTime(avenue, vehicle, end_datetime=now):
#     # call this method when vehicle exits innopark parking
#     # UpdateSessionEndDateTime(avenue_id, "J71612")
#
#     docs_id_extracted, docs_extracted = db.GetAllDocsBasedOnTwoFields(collection+"/" + avenue + "/sessions_info",
#                                                                       "vehicle", vehicle, "end_datetime")
#
#     session_id = docs_id_extracted[0]
#
#     db.UpdateData(collection=collection+"/"+avenue+"/sessions_info", document=session_id,
#                   field_to_edit="end_datetime", new_data=end_datetime)
#
#     UpdateSessionTariffAmount(avenue=avenue, session_id=session_id)
#
#     UpdateSessionDueDateTime(avenue=avenue, session_id=session_id, end_datetime=end_datetime)

def UpdateSession(avenue, session_id, end_datetime, tariff_amount):
    due_datetime = end_datetime+timedelta(hours=48)

    db.UpdateData(collection=collection + "/" + avenue + "/sessions_info", document=session_id,
                  field_to_edit="due_datetime", new_data=due_datetime)

    db.UpdateData(collection=collection + "/" + avenue + "/sessions_info", document=session_id,
                  field_to_edit="end_datetime", new_data=end_datetime)


    db.UpdateData(collection=collection+"/"+avenue+"/sessions_info", document=session_id,
                  field_to_edit="tariff_amount", new_data=tariff_amount)


# def UpdateSessionTariffAmount(avenue, session_id):
#     session_data = db.GetAllDataUsingPath(collection=collection+"/"+avenue+"/sessions_info", document=session_id)
#
#     start_datetime = session_data["start_datetime"]
#     end_datetime = session_data["end_datetime"]
#     rate_per_hour = session_data["rate_per_hour"]
#
#     tariff_amount = CalculateSessionTariffAmount(start_datetime, end_datetime, rate_per_hour)
#
#     db.UpdateData(collection=collection+"/"+avenue+"/sessions_info", document=session_id,
#                   field_to_edit="tariff_amount", new_data=tariff_amount)


def GetAllParkings(avenue):
    docs_id, docs = db.GetAllDocuments(collection+"/"+avenue+"/parkings_info")

    for doc in docs:
        bbox_converted = []
        bbox = doc["bounding_box"]
        bbox_converted.append([bbox[0], bbox[1]])
        bbox_converted.append([bbox[2], bbox[3]])
        bbox_converted.append([bbox[4], bbox[5]])
        bbox_converted.append([bbox[6], bbox[7]])
        doc["bounding_box"] = bbox_converted

    return docs_id, docs

def GetParking(avenue, parking_id):
    parking_info = db.GetAllDataUsingPath(collection=collection+"/"+avenue+"/"+"parkings_info", document=parking_id)
    return parking_info

def GetRatePerHourFromAvenueInfo(avenue, parking_type):
    if parking_type is None:
        rate_per_hour = 0
    else:
        data = db.GetAllDataUsingDocument(collection=collection, document=avenue)
        rate_per_hour = (data["parking_types"])[str(parking_type)]

    return rate_per_hour

def GetRatePerHourFromParkingInfo(avenue, parking_id):
    if parking_id is None:
        rate_per_hour = 0
    else:
        parking_info = GetParking(avenue, parking_id)
        rate_per_hour = parking_info["rate_per_hour"]

    return rate_per_hour

# AddSession(avenue=avenue_id, vehicle="J71612", parking_id="4dkekG8hrOrJ1mpOpoO6")
# AddParking(avenue=avenue_id, camera_id=0, bounding_box=[100,320,300,150, 400, 320, 150, 600], parking_type="a")

# n=[{"a":0}, {"b":2}]
# print(type(n))
    # self.parking_spaces.append(ParkingSpace(*parking_doc))
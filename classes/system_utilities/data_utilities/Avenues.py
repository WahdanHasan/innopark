import sys

import classes.system_utilities.data_utilities.DatabaseUtilities as db
from datetime import datetime, timedelta, timezone
from classes.system_utilities.helper_utilities import Constants
from dateutil.relativedelta import relativedelta
from classes.system_utilities.data_utilities.Vehicles import VehicleExists, AddVehicle

# now = datetime.now(timezone.utc).astimezone()

conn = db.GetDbConnection()

collection = "avenues"

def GetAllAvenues():
    doc = db.GetDocuments(collection)
    print("Avenues: ", doc)

    return doc

def AddParking(avenue, camera_id, parking_id, bounding_box, occupancy_box, parking_type, is_occupied=False):
    # avenues.AddParking(avenue="O8483qKcEoQc6SPTDp5e", camera_id=2,
    #                    bounding_box=[200, 100, 300, 150, 250, 100, 100, 150], parking_type="a")

    if len(bounding_box)!=8:
        print("ERROR: Couldn't add parking. Bounding box must contain 8 values.")
        return

    rate_per_hour = GetRatePerHourFromAvenueInfo(avenue, parking_type)

    db.AddData(collection=collection+"/"+avenue+"/parkings_info",
               document=str(parking_id),
               data={"bounding_box": bounding_box,
                     "occupancy_box" : occupancy_box,
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

    vehicle_exists = VehicleExists(license_number=vehicle)

    if not vehicle_exists:
        print("vehicle doesn't exist in db, add new one")
        AddVehicle(license_number=vehicle, date=start_datetime)

    avenue_name = db.GetPartialDataUsingPath(collection=collection, document=avenue, requested_data="name")

    rate_per_hour = GetRatePerHourFromParkingInfo(avenue, parking_id)

    document_ref =  db.AddData(collection=collection+"/"+avenue+"/sessions_info",
                      data={"end_datetime":end_datetime,
                            "start_datetime":start_datetime,
                            "due_datetime":due_datetime,
                            "tariff_amount": tariff_amount,
                            "vehicle": vehicle,
                            "is_paid": is_paid,
                            "parking_id": parking_id,
                            "rate_per_hour": rate_per_hour,
                            "avenue_name": avenue_name,
                            "payment_link":""})

    return document_ref[1].path.split("/")[3]

def UpdateSession(avenue, session_id, end_datetime, tariff_amount):

    due_datetime = end_datetime+timedelta(hours=Constants.parking_due_in_hours)

    db.UpdateDataThreeFields(collection=collection + "/" + avenue + "/sessions_info", document=session_id,
                             field_to_edit1="due_datetime", new_data1=due_datetime,
                             field_to_edit2="end_datetime", new_data2=end_datetime,
                             field_to_edit3="tariff_amount", new_data3=tariff_amount
                             )

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
        occ_bb_converted = []
        occ_bb = doc["occupancy_box"]
        occ_bb_converted.append([occ_bb[0], occ_bb[1]])
        occ_bb_converted.append([occ_bb[2], occ_bb[3]])
        occ_bb_converted.append([occ_bb[4], occ_bb[5]])
        occ_bb_converted.append([occ_bb[6], occ_bb[7]])
        doc["occupancy_box"] = occ_bb_converted


    return docs_id, docs

def GetParking(avenue, parking_id):
    parking_info = db.GetAllDataUsingPath(collection=collection+"/"+avenue+"/"+"parkings_info", document=str(parking_id))
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

def CheckFineExists(avenue, session_id, fine_type):
    docs = db.db.collection(collection + "/" + avenue + "/" +Constants.fines_info_subcollection_name)\
        .where("session_id", "==", session_id)\
        .where("fine_type", "==",fine_type)\
        .get()

    if not docs or docs is None:
        print("fine doesnt exist")
        return False

    return True

def AddFine(avenue, avenue_name, session_id, vehicle, fine_type, created_datetime=datetime.now().astimezone()):
# add a fine to the database based on session info

    fine_amount, fine_description = GetFineInfo(fine_type, vehicle)
    due_datetime = created_datetime+relativedelta(months=Constants.fine_due_in_months)

    # avenue_name = db.GetPartialDataUsingPath(collection=collection, document=avenue, requested_data="name")

    fine_exists = CheckFineExists(avenue=avenue, session_id=session_id, fine_type=fine_type)

    if fine_exists:
        print("Couldn't add fine. Fine already exists", file=sys.stderr)
        return None

    if fine_type == Constants.fine_type_double_parking:
        is_accepted = False
    else:
        is_accepted = True

    document_ref = db.AddData(collection=collection + "/" + avenue + "/" +Constants.fines_info_subcollection_name,
                              data={"created_datetime": created_datetime,
                                    "due_datetime": due_datetime,
                                    "fine_amount": fine_amount,
                                    "fine_type": fine_type,
                                    "fine_description": fine_description,
                                    "vehicle": vehicle,
                                    "is_paid": False,
                                    "is_disputed": False,
                                    "is_reviewed": False,
                                    "is_accepted": is_accepted,
                                    "session_id": session_id,
                                    "avenue_name": avenue_name,
                                    "footage":""})

    print("doc_ref of fine: " + document_ref, file=sys.stderr)

    return document_ref[1].path.split("/")[3]

def GetFineInfo(fine_type, vehicle):
    fine_amount = 0
    fine_description = ""

    if fine_type == Constants.fine_type_exceeded_due_date:
        fine_amount = Constants.fine_amount_exceeded_due_date
        fine_description = "A parking session of your vehicle "+ vehicle +" has not been paid by the due date."\
                            +"\nKindly pay the session and the fine before the fine due date or legal action will be taken."

    elif fine_type == Constants.fine_type_double_parking:
        fine_amount = Constants.fine_amount_double_parking
        fine_description = "Your vehicle "+ vehicle +" is occupying more than one parking space."+ \
                           "\nKindly pay the fine before the due date or legal action will be taken."

    elif fine_type == Constants.fine_type_exceeded_allowed_duration:
        fine_amount == Constants.fine_amount_exceeded_allowed_duration
        fine_description = "Your vehicle "+vehicle +" has been parked for more than "+Constants.max_parking_duration_in_hours+" hours."+ \
                           "\nKindly pay the fine before the due date or legal action will be taken."

    return fine_amount, fine_description

def GetSessionsDueToday(collection, today_start_datetime, today_end_datetime):
    # get all docs whose key field value is greater than or equal to the value you're looking for

    docs = db.db.collection(collection).where("due_datetime", "<=", today_end_datetime)\
        .where("due_datetime", ">=", today_start_datetime)\
        .where("is_paid", "==", False).get()

    if not docs:
        print("No sessions are due today.", file=sys.stderr)
        return None, None

    sessions_id_extracted = []
    sessions_extracted = []

    for i in range(len(docs)):
        sessions_extracted.append(docs[i].to_dict())
        sessions_id_extracted.append(docs[i].id)

    return sessions_id_extracted, sessions_extracted

def GetFinesFromDb(avenue):
    fines_id_extracted, fines_extracted = db.GetAllDocsEqualToTwoFields(collection=collection+"/"+avenue+"/"+Constants.fines_info_subcollection_name,
                                              first_key=Constants.is_reviewed_key, first_value=False,
                                              second_key=Constants.is_accepted_key, second_value=False)

    if fines_id_extracted is None or not fines_id_extracted:
        print("Couldn't retrieve fines from Db")
        return None, None

    return fines_id_extracted, fines_extracted


def UpdateOccupancyStatus(avenue, parking_id, parking_occupancy_status):
    db.UpdateData(collection=collection+"/"+avenue+"/"+Constants.parking_info_subcollection_name,
                  document=parking_id, field_to_edit=Constants.is_occupied_key, new_data=parking_occupancy_status)

    print("Successfully Updated the Occupancy of the Parking")
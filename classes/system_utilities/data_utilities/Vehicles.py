import classes.system_utilities.data_utilities.DatabaseUtilities as db

conn = db.GetDbConnection()

collection = "vehicles"
documents = conn.collection(collection).get()

def AddVehicle(license_number, date, owner=None, drivers_array=None, manufacturer=None,
               model=None, year=None, city_of_registration=None):

    db.AddData(collection, license_number, {
        #"license_number": license_number,
        "manufacturer": manufacturer,
        "model": model,
        "year": year,
        "city_of_registration": city_of_registration,
        "added_on": date,
        "owned_by": owner,
        "driven_by": drivers_array
    })

def GetVehicleInfo(license_number):
    doc = conn.document(collection+"/"+license_number).get()

    doc_data = doc.to_dict()

    if doc_data is None or not doc_data:
        print("Vehicle does not exist")
        return

    return doc_data

def VehicleExists(license_number):
    doc = conn.document(collection+"/"+license_number).get()

    if doc.to_dict() is None or not doc.to_dict():
        return False

    return True

def GetPartialVehicleInfo(license_number, requested_data):
    doc = conn.document(collection + "/" + license_number).get()
    return (doc.to_dict())[str(requested_data)]

    # docs = conn.collection("users").order_by(
    #     'first_name', direction=db.firestore.Query.ASCENDING).where("first_name", '>', '').get()
    # print((docs[0].id))

def UpdateVehicleInfo(license_number, field_to_edit, new_data):
    db.UpdateData(collection, license_number, field_to_edit, new_data)

def GetAllVehicles():
    db.GetDocuments(collection)
import classes.system_utilities.data_utilities.DatabaseUtilities as db

conn = db.GetDbConnection()

collection = "users"

# gonna need to make the vehicle_owned an array as user can have many vehicles
def AddUser(email_address, password, phone_number, first_name, last_name, id_card_number, vehicle_owned=None):
    db.AddData(collection=collection, data={
        "email_address": email_address,
        "password": password,
        "phone_number": phone_number,
        "first_name": first_name,
        "last_name": last_name,
        "id_card_number": id_card_number,
        "vehicle_owned": vehicle_owned
    })

def GetAllUserInfo(email_address):
    doc = conn.collection(collection).where("email_address", "==", email_address).get()
    return doc[0].to_dict()

def GetPartialUserInfo(email_address, requested_data):
    doc = conn.collection(collection).where("email_address", "==", email_address).get()
    print((doc[0].to_dict())[requested_data])

def UpdateUser(email_address, field_to_edit, new_data):
    db.UpdateData(collection, email_address, field_to_edit, new_data)

def UpdateFirstName(email_address, new_first_name):
    db.UpdateData(collection, email_address, "first_name", new_first_name)

def UpdateLastName(email_address, new_last_name):
    db.UpdateData(collection, email_address, "last_name", new_last_name)

def UpdatePhoneNumber(email_address, new_phone_number):
    db.UpdateData(collection, email_address, "phone_number", new_phone_number)

def UpdateIdCardNumber(email_address, new_id_card_number):
    db.UpdateData(collection, email_address, "id_card_number", new_id_card_number)

def UpdatePassword(email_address, new_password):
    db.UpdateData(collection, email_address, "password", new_password)



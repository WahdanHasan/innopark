import classes.system_utilities.data_utilities.DatabaseUtilities as db
import classes.system_utilities.data_utilities.Users as users
import classes.system_utilities.data_utilities.Vehicles as vehicles
import classes.system_utilities.data_utilities.Avenues as avenues

from datetime import datetime

now = datetime.now

root_doc="root/root_doc"

def QueryUserVehicle():
    con = db.GetDbConnection()
    data = con.collection(root_doc+"/users").get()



    # user = None
    # for d in data:
    #     if(d.to_dict()["vehicle_owned"]=="J71612"):
    #         user = d.id
    #         break
    #
    # data = con.collection("vehicles").get()

    # for d in data:
    #     print(d.id, (d.to_dict())["password"])

#users.AddUser("hamad@gmail.com", "pass", "0551234567", "hamad", "qasim", "12345", "A555")

# users.UpdateUser("hkSbeQuYMnfkEApQeBsQ", "vehicle_owned", "A555")

#db.DeleteDocument(str(root_doc+"/users"), "TlTQewg8RFqnqcOoaF11")

# i think the owner should be identified by phone number, not email
#vehicles.AddVehicle("J71612", now, "0551111111", ["ahmed@gmail.com", "laila@gmail.com"], "Honda", "Accord", "2008", "Dubai")
# vehicles.AddVehicle("A12345", now)

# v = vehicles.GetPartialVehicleInfo("J71612", "manufacturer")
# print(v)

# users.GetPartialUserInfo("ahmed@gmail.com", "last_name")

# data = db.GetPartialDataUsingPath("vehicles", "J71612", "manufacturer")

# data = db.GetAllDataUsingEqualQuery("users", "email_address", "ahmed@gmail.com")

data = avenues.GetAllParkings()
#db.AddData("root/root_doc/users", data={"last_name":"qasim"})

print(data)
import classes.system_utilities.data_utilities.DatabaseUtilities as db

conn = db.GetDbConnection()

collection = "avenues"

avenue_id = "zFRQSZWp2gUm9avdWVPZ"

def GetParkingInfo(avenue_id, key, value):
    doc = db.GetAllDataUsingEqualQuery("avenues/"+avenue_id+"/parkings_info", key, value)
    print(doc)
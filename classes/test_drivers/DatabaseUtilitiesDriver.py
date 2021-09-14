import classes.system_utilities.data_utilities.DatabaseUtilities as db


data = db.GetDocuments('users')

print(data)
from DatabaseUtilities import DatabaseUtilities

db = DatabaseUtilities()


data = db.getDocuments('user')

print(data)
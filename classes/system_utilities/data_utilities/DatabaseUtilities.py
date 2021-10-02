import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Remember that the db hierarchy is Collection > Document > Data

db = 0
def OnLoad():
    global db
    # Initialize Google Cloud Platform using service account credentials
    cred = credentials.Certificate('modules\\Firebase\\ServiceAccount.json')
    firebase_admin.initialize_app(cred)

    db = firestore.client()


OnLoad()

def to_dict(document):

    doc = document.to_dict()

    print(f'Document: {doc}')

def GetDbConnection():
    return db

def AddData(collection, document=None, data=None):
    # collection and document are of type string
    # data is a json object, eg {'name':'John', 'age':20}
    if document is not None:
        document_ref = db.collection(collection).document(document)
        document_ref.set(data)
        # document_ref.set(data, merge=True)
    else:
        collection_ref = db.collection(collection)
        collection_ref.add(data)

    print ("Successfully added to "+collection)

def UpdateData(collection, document, field_to_edit, new_data):
    document_ref = db.collection(collection).document(document)

    document_ref.update({
        field_to_edit: new_data
    })

    print("Successfully updated "+collection)

def GetAllDataUsingDocument(collection, document):
    document_ref = db.collection(collection).document(document)

    data = document_ref.get()

    if not data:
        print(u'Collection or Document doesn\'t exist')
        return None

    return data.to_dict()

def GetAllDataUsingPath(collection, document):
    # grabs the document using path
    # use when the document id is known
    doc = db.document(collection + "/" + document).get()
    return doc.to_dict()

def GetPartialDataUsingPath(collection, document, requested_data):
    # grabs the document using path
    # use when the document id is known
    doc = db.document(collection + "/" + document).get()
    return (doc.to_dict())[str(requested_data)]

def GetAllDataUsingEqualQuery(collection, key, value):
    doc = db.collection(collection).where(key, "==", value).get()
    return doc[0].to_dict()

# def QueryData(collection):
#     user_doc_ref = db.collection('users')
#     vehicle_doc_ref = db.collection('vehicles')
#
#     owner="0551234567"
#     query = user_doc_ref.where('phone_number', '==', owner).get()
#
#     for data in query:
#         print(data.to_dict())
#     return 1

def GetDocuments(collection):
    collection_ref = db.collection(collection)

    documents = collection_ref.get()

    if not documents:
        print(u'Collection doesn\'t exist')
        return None
    else:
        documents_list = []
        for doc in documents:
            documents_list.append(doc.id)
        return documents_list

def GetDocumentsAndChildren(collection):
    collection_ref = db.collection(collection)

    documents = collection_ref.get()

    if not documents:
        print(u'Collection doesn\'t exist')
        return None
    else:
        documents_list = []
        for doc in documents:
            documents_list.append([doc.id, doc.to_dict()])
        return documents_list

def DeleteDocument(collection, document):
    document_ref = db.collection(collection).document(document)

    if not document_ref:
        print(u'Document doesn\'t exist')
        return None

    document_ref.delete()
    print(u'Successfully deleted document!')
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Remember that the db hierarchy is Collection > Document > Data

db = 0
def OnLoad():
    global db
    # Initialize Google Cloud Platform using service account credentials
    cred = credentials.Certificate('config\\firebase\\ServiceAccount.json')
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

    print("Successfully added to "+collection)

def UpdateData(collection, document, field_to_edit, new_data):
    document_ref = db.collection(collection).document(document)

    document_ref.update({
        field_to_edit: new_data
    })

    print("Successfully updated "+collection)

def GetAllDocuments(collection):
    docs_id=[]
    docs = []

    result = db.collection(collection).get()

    for doc in result:
        docs_id.append(doc.id)
        docs.append(doc.to_dict())

    return docs_id, docs

def GetAllSubcollectionsOfDocument(collection, document):
    subcollections = db.collection(collection).document(document).collections()

    docs_id = []
    docs = []
    for subcollection in subcollections:
        for doc in subcollection.get():
            docs_id.append(doc.id)
            docs.append(doc.to_dict())

    return docs_id, docs

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

    if not doc:
        print("collection or document does not exist")
        return None

    return (doc.to_dict())[str(requested_data)]

def GetFirstDocContainingRequestedField(collection, key, value):
    # get the first doc whose key field equals the value you're looking for
    doc = db.collection(collection).where(key, "==", value).get()

    if not doc:
        print("Error: requested field is not found")
        return None

    return doc[0].to_dict()


def GetAllDocsContainingRequestedField(collection, key, value):
    # get all docs whose key field equals the value you're looking for
    docs_id, docs = GetAllDocuments(collection)

    docs_extracted = []
    docs_id_extracted = []

    for i in range(len(docs_id)):
        if(docs[i])[key] == value:
            docs_extracted = (docs[i])[key]
            docs_id_extracted = i

    return docs_id_extracted, docs_extracted

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
    documents = db.collection(collection).get()

    if not documents:
        print(u'Collection doesn\'t exist')
        return None
    else:
        documents_list = []
        for doc in documents:
            documents_list.append([doc.id, doc.to_dict()])
            print("doc aaa:", doc.to_dict())
        return documents_list

def DeleteDocument(collection, document):
    document_ref = db.collection(collection).document(document)

    if not document_ref:
        print(u'Document doesn\'t exist')
        return None

    document_ref.delete()
    print(u'Successfully deleted document!')
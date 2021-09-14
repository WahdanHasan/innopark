import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

class DatabaseUtilities:
    # Remember that the db hierarchy is Collection > Document > Data
    def __init__(self):
        # Initialize Google Cloud Platform using service account credentials
        cred = credentials.Certificate('ServiceAccount.json')
        firebase_admin.initialize_app(cred)

        self._db = firestore.client()

    def to_dict(self, document):

        doc = document.to_dict()

        print(f'Document: {doc}')

    def AddData(self, collection, document=None, data=None):
        # collection and document are of type string
        # data is a json object, eg {'name':'John', 'age':20}
        if document is not None:
            document_ref = self._db.collection(collection).document(document)
            document_ref.set(data)
        else:
            collection_ref = self._db.collection(collection)
            collection_ref.add(data)

    def GetData(self, collection, document):
        document_ref = self._db.collection(collection).document(document)

        data = document_ref.get()

        if not data:
            print(u'Collection or Document doesn\'t exist')
            return None

        return data.to_dict()

    def GetDocuments(self, collection):
        collection_ref = self._db.collection(collection)

        documents = collection_ref.get()

        if not documents:
            print(u'Collection doesn\'t exist')
            return None
        else:
            documents_list = []
            for doc in documents:
                documents_list.append([doc.id, doc.to_dict()])
            return documents_list

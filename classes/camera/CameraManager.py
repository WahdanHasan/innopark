
class SingletonCameraManager:
    _instance = None

    def __init__(self):
        self.camera_list = []

    def AddCameraToList(self, camera):

        self.camera_list.append(camera)

    def GetCameraById(self, camera_id):

        for i in range(len(self.camera_list)):
            if self.camera_list[i].camera_id == camera_id:
                return self.camera_list[i]

    @property
    def instance(self):
        return self._instance


def GetSingletonCameraManager():
    if SingletonCameraManager.instance is None:
        SingletonCameraManager.instance = SingletonCameraManager

    return SingletonCameraManager.instance


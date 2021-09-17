from classes.system_utilities.tracking_utilities.EntranceLicenseDetector import EntranceLicenseDetector

licenseDetector = EntranceLicenseDetector()

licenseDetector.StartProcess(["D:\\DownloadsD\\License_Footage\\Entrance_Bottom_Simulated.mp4", 0],
                             ["D:\\DownloadsD\\License_Footage\\Entrance_Top.mp4", 1])


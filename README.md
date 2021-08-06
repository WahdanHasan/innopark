# InnoPark
 
*********************Required installations*********************

CUDA, CuDNN, required libraries, object detection:
- Follow video till 5:40 (Go for GPU installation): https://www.youtube.com/watch?v=hHWkvEcDBO0
- From this repository's SETUP folder, copy Script.bat onto your desktop.
- Open Anaconda prompt.
- Navigate to 'desktop'. (Command from user directory: 'cd desktop')
- Execute Script.bat. (Command from the same directory as file: 'Script.bat')
- Enter 'y' for every prompt of the installation.
- Follow video till 24:05: https://www.youtube.com/watch?v=dZh_ps8gKgs

Selecting the correct interpreter for the project:
- Launch the InnoPark project in PyCharm.
- Go to File>Settings>Project:InnoPark>Python Interpreter
- Click on the gear icon next to the 'Python Interpreter' drop down.
- Click on 'add'.
- Click 'Conda Environment' from the list on the left.
- Check 'Existing environment'
- Select the 'innopark/python.exe' environment from the interpreter list.
- Click ok, then click apply.

Installing and configuring Amazon DynamoDB:
- From this repository's SETUP folder, copy Script_DynamoDB.bat onto your desktop.
- Open Anaconda prompt.
- Navigate to 'desktop'. (Command from user directory: 'cd desktop')
- Execute Script_DynamoDB.bat. (Command from the same directory as file: 'Script_DynamoDB.bat')
- Enter 'AKIAYYMYAPJ7XZUTZXO5' for the AWS Access Key ID.
- Enter 'mHFkWNScaPugpcbdONNb17fcdZbD7dt+pFsvJWH1' for the AWS Secret Access Key.
- Enter 'eu-west-1' for the Default region name.
- Just hit enter on the Default output format.

*********************Optional installations*********************

OpenCV for GPU (This is required for running YOLOv3 on GPU mode. By default, the CPU mode is used):
- Follow this video: https://www.youtube.com/watch?v=YsmhKar8oOc
  - Here are the 2 downloads for OpenCV: 
    - https://github.com/opencv/opencv/archive/4.5.2.zip
    - https://github.com/opencv/opencv_contrib/archive/refs/tags/4.5.2.zip

# InnoPark
 *********************Test footage*********************
 Extract into the data folder
 Link: https://drive.google.com/file/d/1jbgASwJOOyX9mPLXurYEcyZvRZtAYja8/view?usp=sharing
 
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

*********************Optional installations*********************

OpenCV for GPU (This is required for running YOLOv3 on GPU mode. By default, the CPU mode is used):
- Follow this video: https://www.youtube.com/watch?v=YsmhKar8oOc
  - Here are the 2 downloads for OpenCV: 
    - https://github.com/opencv/opencv/archive/4.5.2.zip
    - https://github.com/opencv/opencv_contrib/archive/refs/tags/4.5.2.zip

# TeamProject
>This Respository contains the following codes and an STL file(Seeed Sensor and ESP32).

## ESP32 with LED's for the SEEED STUDIO 60GHz mmWave Sensor - Fall Detection Module Pro (MR60FDA1)
- The Human Presence detection is working and only gives visual feedback via the LED's.
- With the help of an ESP32, the presence detection information can be sent to the Care-Taker's devices via internet.
- The provided libraries from Seeed Studio help communicate with the sensor.
- The entire code is developed in **Arduino IDE**.
- Further development are currently halted with this sensor for the project.
## Python script for the Infenion XENSIV™ 60GHz radar sensor for advanced sensing BGT60TR13C module
- The **Infenion BGT60TR13C** module can send raw data for presence and activity sensing to the console.
- This is possible by using the libraries provided for the sensor from Infenion.
- Before running the code, the following needs to be done.
### Steps to install the library
- A **Python Version** of **3.8** or higher is required for the wrapper and is tested on **Windows 10 (64-bit)**.
- To install the **ifxradarsdk**, it is advisable to do it in a virtual environment.

		 python  -m  pip  install  /path/to/ifxradarsdk.whl

### Steps to display data from the sensor
- The **main_gui.py** with the help of the libraries is developed to show all the usecases in a single GUI.
- All the paths to the assets are local links and has to be replaced by the user.
- Start by connecting the Sensor to the pc.
- Then run the **main_gui.py**.
- The Fall Detection usecase requires a different sensor configuration and has to be set in the **radar_data_acquisition.py**


### Posture Detection
- I implemented a live sensing GUI for an Infineon 60 GHz radar, measured by presence and three posture states (Standing, Sitting, Sleeping) updating in real time, by developing Python/NumPy/SciPy signal processing (range FFT, moving averages, peak detection) and a Tkinter interface.
- The Python file PythonInfenion/BGT60TR13C/Posture_Detection_Usecase.py can be run individually as it has its own GUI integrated.
  
<img width="2036" height="1088" alt="Standing" src="https://github.com/user-attachments/assets/af48d91b-30ab-4804-a832-9d536290896f" />

<img width="2038" height="1082" alt="Sitting" src="https://github.com/user-attachments/assets/8c2744ac-c7c7-4207-9bb0-be5a77fa3da1" />

<img width="2032" height="1054" alt="Sleeping" src="https://github.com/user-attachments/assets/ddebdd34-7706-4f30-bd4d-90214a8d7cb4" />

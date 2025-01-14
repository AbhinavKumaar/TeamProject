import sys
import time
import numpy as np
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QDockWidget, QSizePolicy, QSlider)
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QFont
from helpers.DopplerAlgo import *
from radar_data_acquisition import initialize_radar, get_radar_data
import threading
from Fall_Detection_Usecase import FallDetectionAlgo
from People_Count_Usecase import PresenceAlgo
from Posture_Detection_Usecase import PostureDetectionAlgo
from Presence_Detection_Usecase import run_presence_detection

class RadarSignals(QObject):
    update_fall = pyqtSignal(bool)
    update_people_count = pyqtSignal(int) 
    update_gesture = pyqtSignal(str)
    update_posture = pyqtSignal(str)
    
class GestureDetectionAlgo:
    def __init__(self, num_samples, num_chirps, num_rx_antennas):
        self.num_samples = num_samples
        self.num_chirps = num_chirps
        self.num_rx_antennas = num_rx_antennas
        self.doppler = DopplerAlgo(num_samples, num_chirps, num_rx_antennas)

    def detect_gesture(self, frame_data):
        detection_occurred = False
        for i_ant in range(self.num_rx_antennas):
            if i_ant < frame_data.shape[0]:
                mat = frame_data[i_ant, :, :]
                try:
                    dfft_dbfs = linear_to_dB(self.doppler.compute_doppler_map(mat, i_ant))
                    if np.any(dfft_dbfs > -59):
                        detection_occurred = True
                        break
                except IndexError as e:
                    print(f"IndexError in compute_doppler_map: {e}")
                    print(f"Shape of mat: {mat.shape}")
                    print(f"i_ant: {i_ant}")
                    continue

        if detection_occurred:
            return "Gesture detected"
        else:
            return "No gesture detected"

def linear_to_dB(x):
    return 20 * np.log10(abs(x))

class ButtonDock(QDockWidget):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.setMinimumSize(600, 400)  

class RadarGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Radar Data Analysis")
        self.setGeometry(600, 500, 800, 600)
    
        self.setStyleSheet("background-color: #0d0f0f;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Button dock
        button_dock = ButtonDock("Controls", self)
        button_widget = QWidget()
        button_layout = QVBoxLayout(button_widget)
        
        button_style = """
        QPushButton {
            font-size: 28px;
            padding: 10px;
            border-radius: 10px;
            color: white;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #34495E;
        }
        """

        self.posture_detection_button = QPushButton("Run Posture Detection")
        self.posture_detection_button.setStyleSheet(button_style + "background-color: #3498DB;")
        self.posture_detection_button.clicked.connect(self.run_posture_detection)
        button_layout.addWidget(self.posture_detection_button)

        self.presence_detection_button = QPushButton("Run Presence Detection")
        self.presence_detection_button.setStyleSheet(button_style + "background-color: #2ECC71;")
        self.presence_detection_button.clicked.connect(self.run_presence_detection)
        button_layout.addWidget(self.presence_detection_button)

        self.fall_detection_button = QPushButton("Run Fall Detection")
        self.fall_detection_button.setStyleSheet(button_style + "background-color: #E74C3C;")
        self.fall_detection_button.clicked.connect(self.run_fall_detection)
        button_layout.addWidget(self.fall_detection_button)
        
        self.gesture_detection_button = QPushButton("Run Gesture Detection")
        self.gesture_detection_button.setStyleSheet(button_style + "background-color: #F39C12;")
        self.gesture_detection_button.clicked.connect(self.run_gesture_detection)
        button_layout.addWidget(self.gesture_detection_button)
        
        self.people_count_button = QPushButton("Run People Count")
        self.people_count_button.setStyleSheet(button_style + "background-color: #F39C12;")
        self.people_count_button.clicked.connect(self.run_people_count)
        button_layout.addWidget(self.people_count_button)

        self.reset_fall_button = QPushButton("Reset Fall Detection")
        self.reset_fall_button.setStyleSheet(button_style + "background-color: #9B59B6;")
        self.reset_fall_button.clicked.connect(self.reset_fall_flag)
        button_layout.addWidget(self.reset_fall_button)

        button_dock.setWidget(button_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, button_dock)

        # Posture detection dock
        self.posture_detection_dock = QDockWidget("Posture Detection", self)
        self.posture_detection_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.posture_detection_dock.setMinimumSize(200, 200)
        self.posture_detection_dock.setStyleSheet("QDockWidget { font-size: 28px; color: white; }")

        posture_widget = QWidget()
        posture_layout = QVBoxLayout(posture_widget)

        self.posture_icon_label = QLabel("", alignment=Qt.AlignCenter)
        self.posture_icon_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        posture_layout.addWidget(self.posture_icon_label)

        self.icon_size_slider = QSlider(Qt.Horizontal)
        self.icon_size_slider.setMinimum(50)
        self.icon_size_slider.setMaximum(200)
        self.icon_size_slider.setValue(100)
        self.icon_size_slider.valueChanged.connect(self.update_icon_size)
        self.icon_size_slider.setStyleSheet("QSlider::handle:horizontal { background-color: #3498DB; }")
        posture_layout.addWidget(self.icon_size_slider)

        self.posture_detection_dock.setWidget(posture_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.posture_detection_dock)

        # Presence detection dock
        self.presence_detection_dock = QDockWidget("Presence Detection", self)
        self.presence_detection_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.presence_detection_dock.setMinimumSize(1800, 500)
        self.presence_detection_dock.setStyleSheet("QDockWidget { font-size: 28px; color: white; }")
        self.presence_detection_widget = QLabel("Presence Detection: Not Running")
        self.presence_detection_widget.setAlignment(Qt.AlignCenter)
        self.presence_detection_widget.setStyleSheet("border: 1px solid white; font-size: 28px; color: white;")
        self.presence_detection_dock.setWidget(self.presence_detection_widget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.presence_detection_dock)

        # Fall detection dock
        self.fall_detection_dock = QDockWidget("Fall Detection", self)
        self.fall_detection_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.fall_detection_dock.setMinimumSize(200, 200)
        self.fall_detection_dock.setStyleSheet("QDockWidget { font-size: 28px; color: white; }")

        fall_detection_widget = QWidget()
        fall_detection_layout = QVBoxLayout(fall_detection_widget)

        self.fall_detection_label = QLabel("Fall Detection: Not Running")
        self.fall_detection_label.setAlignment(Qt.AlignCenter)
        self.fall_detection_label.setStyleSheet("border: 1px solid white; font-size: 28px; color: white;")
        fall_detection_layout.addWidget(self.fall_detection_label)

        self.fall_detection_led = QLabel()
        self.fall_detection_led.setFixedSize(50, 50)
        self.fall_detection_led.setStyleSheet("background-color: grey; border-radius: 25px;")
        fall_detection_layout.addWidget(self.fall_detection_led, alignment=Qt.AlignCenter)
        
        self.fall_detected_flag = False
        self.fall_detection_led_on = False

        self.fall_detection_dock.setWidget(fall_detection_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.fall_detection_dock)
        
# Gesture detection dock
        self.gesture_detection_dock = QDockWidget("Gesture Detection", self)
        self.gesture_detection_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.gesture_detection_dock.setMinimumSize(200, 200)
        self.gesture_detection_dock.setStyleSheet("QDockWidget { font-size: 28px; color: white; }")

        gesture_detection_widget = QWidget()
        gesture_detection_layout = QVBoxLayout(gesture_detection_widget)

        self.gesture_detection_label = QLabel("Gesture: Not Detected")
        self.gesture_detection_label.setAlignment(Qt.AlignCenter)
        self.gesture_detection_label.setStyleSheet("border: 1px solid white; font-size: 28px; color: white;")
        gesture_detection_layout.addWidget(self.gesture_detection_label)

        self.gesture_icon_label = QLabel()
        self.gesture_icon_label.setFixedSize(50, 50)
        self.gesture_icon_label.setStyleSheet("background-color: grey; border-radius: 25px;")
        gesture_detection_layout.addWidget(self.gesture_icon_label, alignment=Qt.AlignCenter)

        self.gesture_detection_dock.setWidget(gesture_detection_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.gesture_detection_dock)

        # People count dock
        self.people_count_dock = QDockWidget("People Count", self)
        self.people_count_dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.people_count_dock.setMinimumSize(200, 200)
        self.people_count_dock.setStyleSheet("QDockWidget { font-size: 28px; color: white; }")

        people_count_widget = QWidget()
        people_count_layout = QVBoxLayout(people_count_widget)

        self.people_count_label = QLabel("People Count: 0")
        self.people_count_label.setAlignment(Qt.AlignCenter)
        self.people_count_label.setStyleSheet("border: 1px solid white; font-size: 28px; color: white;")
        people_count_layout.addWidget(self.people_count_label)

        self.people_count_icon_label = QLabel("👤")
        self.people_count_icon_label.setAlignment(Qt.AlignCenter)
        self.people_count_icon_label.setStyleSheet("font-size: 40px;")
        people_count_layout.addWidget(self.people_count_icon_label)

        self.people_count_dock.setWidget(people_count_widget)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.people_count_dock)
        
        initialize_radar()
        self.radar_data = get_radar_data()

        self.presence_detection = None
        self.radar_signals = RadarSignals()
        self.radar_signals.update_fall.connect(self.update_fall_detection_status)
        self.radar_signals.update_gesture.connect(self.update_gesture_detection_status)
        self.radar_signals.update_people_count.connect(self.update_people_count_status)
        self.radar_signals.update_posture.connect(self.update_posture_detection_status)

        self.icons = {
            "standing": "🧍",
            "sitting": "🪑",
            "sleeping": "🛌",
            "no_presence": "❌",
            "unknown": "❓",
            "fall_detected": "🆘",
            "no_fall": "✅",
        }

        self.update_icon_size(100)

        # Initializing algorithms
        self.posture_algo = PostureDetectionAlgo(
            self.radar_data.config.chirp.num_samples,
            self.radar_data.config.num_chirps
        )
        self.fall_detection_algo = FallDetectionAlgo(
            self.radar_data.config.chirp.num_samples,
            self.radar_data.config.num_chirps,
            self.radar_data.config.chirp_repetition_time_s,
            self.radar_data.config.chirp.start_frequency_Hz
        )
        self.presence_algo = PresenceAlgo(
            self.radar_data.config.chirp.num_samples,
            self.radar_data.config.num_chirps
        )
        num_rx_antennas = bin(self.radar_data.config.chirp.rx_mask).count('1')
        self.gesture_algo = GestureDetectionAlgo(
            self.radar_data.config.chirp.num_samples,
            self.radar_data.config.num_chirps,
            num_rx_antennas
        )

        self.fall_detected_flag = False
        
        # Initializing DopplerAlgo
        num_rx_antennas = bin(self.radar_data.config.chirp.rx_mask).count('1')
        self.doppler = DopplerAlgo(self.radar_data.config.chirp.num_samples, 
                                   self.radar_data.config.num_chirps, 
                                   num_rx_antennas)

    def run_posture_detection(self):
        thread = threading.Thread(target=self._posture_detection_loop)
        thread.start()

    def _posture_detection_loop(self):
        while True:
            frame = self.radar_data.get_latest_frame()
            if frame is not None:
                mat = frame[0, :, :]
                state = self.posture_algo.posture(mat)
                
                if state.presence:
                    if len(state.peaks) > 0:
                        peak_idx = state.peaks[0]
                        max_range_m = self.radar_data.device.metrics_from_sequence(
                            self.radar_data.device.get_acquisition_sequence().loop.sub_sequence.contents
                        ).max_range_m
                        distance = (peak_idx / self.radar_data.config.chirp.num_samples) * max_range_m

                        if distance <= 0.50:
                            posture = "standing"
                        elif 0.50 < distance <= 0.70:
                            posture = "sitting"
                        elif 0.70 < distance <= 0.90:
                            posture = "sleeping"
                    else:
                        posture = "unknown"
                else:
                    posture = "no_presence"

                self.radar_signals.update_posture.emit(posture)

    def run_fall_detection(self):
        thread = threading.Thread(target=self._fall_detection)
        thread.start()

    def _fall_detection(self):
        while True:
            frame = self.radar_data.get_latest_frame()
            if frame is not None:
                mat = frame[0, :, :]  
                fall_detected = self.fall_detection_algo.detect_fall(mat)
                self.radar_signals.update_fall.emit(fall_detected)

    def update_fall_detection_status(self, fall_detected):
        if fall_detected:
            self.fall_detected_flag = True
            self.fall_detection_label.setText("Fall Detected!")
            self.fall_detection_label.setStyleSheet("background-color: red; color: white; font-weight: bold; font-size: 50px;")
            self.fall_detection_led.setStyleSheet("background-color: red; border-radius: 10px;")
            self.fall_detection_led_on = True

        else:
            self.fall_detected_flag = False
            self.fall_detection_label.setText("No Fall Detected")
            self.fall_detection_label.setStyleSheet("background-color: green; color: white; font-size: 50px;")
            if not self.fall_detection_led_on:
                self.fall_detection_led.setStyleSheet("background-color: grey; border-radius: 10px;")

    def reset_fall_flag(self):
        self.fall_detected_flag = False
        self.fall_detection_label.setText("Fall Detection: Not Running")
        self.fall_detection_label.setStyleSheet("border: 1px solid black;")
        self.fall_detection_led.setStyleSheet("background-color: grey; border-radius: 10px;")
        self.fall_detection_led_on = False

    def run_people_count(self):
        thread = threading.Thread(target=self._people_count)
        thread.start()

    def _people_count(self):
        while True:
            frame = self.radar_data.get_latest_frame()
            if frame is not None:
                mat = frame[0, :, :] 
                state = self.presence_algo.presence(mat)
                self.radar_signals.update_people_count.emit(state.num_persons)

    def run_presence_detection(self):
        if self.presence_detection is None:
            self.presence_detection = run_presence_detection()
            plot = self.presence_detection.initialize_plot()
            self.presence_detection_widget = plot
            self.presence_detection_dock.setWidget(plot)
            self.presence_detection.signals.update_plot.connect(plot.update_angle)

        thread = threading.Thread(target=self._presence_detection)
        thread.start()

    def _presence_detection(self):
        if self.presence_detection:
            self.presence_detection.run_presence_detection()

    def update_posture_detection_status(self, status):
        self.posture_icon_label.setText(self.icons.get(status.lower(), self.icons["unknown"]))

    def update_people_count_status(self, count):
        self.people_count_label.setText(f"People Count: {count}")
        self.people_count_icon_label.setText("👤" * count)

    def update_icon_size(self, size):
        font = QFont()
        font.setPointSize(size)
        self.posture_icon_label.setFont(font)
        
    def run_gesture_detection(self):
        thread = threading.Thread(target=self._gesture_detection_loop)
        thread.start()

    def _gesture_detection_loop(self):
        last_detection_time = 0
        detection_suppress_time = 1
        display_duration = 5
        gesture_detected = False

        while True:
            frame_data = self.radar_data.get_latest_frame()
            if frame_data is not None:
                gesture = self.gesture_algo.detect_gesture(frame_data)
                
                current_time = time.time()

                if gesture == "Gesture detected":
                    if current_time - last_detection_time > detection_suppress_time:
                        print("Gesture detected")
                        self.radar_signals.update_gesture.emit("Gesture detected")
                        last_detection_time = current_time
                        gesture_detected = True

                if gesture_detected and current_time - last_detection_time > display_duration:
                    print("No gesture detected")
                    self.radar_signals.update_gesture.emit("No gesture detected")
                    gesture_detected = False

            time.sleep(0.01)

    def update_gesture_detection_status(self, gesture):
        self.gesture_detection_label.setText(f"Gesture: {gesture}")
        if gesture != "No Gesture Detected":
            self.gesture_icon_label.setStyleSheet("background-color: green; border-radius: 25px;")
        else:
            self.gesture_icon_label.setStyleSheet("background-color: yellow; border-radius: 25px;")

    def closeEvent(self, event):
        if self.radar_data:
            self.radar_data.stop()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = RadarGUI()
    gui.show()
    sys.exit(app.exec_())

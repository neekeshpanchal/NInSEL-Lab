import sys
import os
import cv2
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QFileDialog, QLabel, QSlider,
    QTextEdit, QProgressBar, QHBoxLayout, QMessageBox, QStyle, QMainWindow, QSpinBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap


class ConverterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.increment_value = 5  # Initialize increment value here
        self.init_ui()
        self.files_to_convert = []
        self.output_dir = ''
        self.move_x = 0
        self.move_y = 0
        self.video_capture = None
        self.video_loaded = False
        self.pose_data = None  # To store the pose data for overlay
        self.current_frame_number = 0  # To keep track of current frame number
        self.is_paused = True
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_frame)
        self.fps = 0
        self.total_frames = 0


    def init_ui(self):
        self.setWindowTitle('Conversion Tool Omega - Pose Data to Video Alignment')
        self.resize(800, 600)

        layout = QVBoxLayout()

        # Buttons Layout
        btn_layout = QHBoxLayout()
        self.upload_button = QPushButton('Upload DLC Data')
        self.upload_button.clicked.connect(self.upload_files)
        btn_layout.addWidget(self.upload_button)

        self.convert_button = QPushButton('Convert and Adjust')
        self.convert_button.clicked.connect(self.convert_files)
        self.convert_button.setEnabled(False)
        btn_layout.addWidget(self.convert_button)

        self.upload_video_button = QPushButton('Upload Video')
        self.upload_video_button.clicked.connect(self.upload_video)
        btn_layout.addWidget(self.upload_video_button)

        layout.addLayout(btn_layout)

        # Video Display
        self.video_label = QLabel("Video will be displayed here")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setFixedSize(640, 480)
        layout.addWidget(self.video_label)

        # Playback controls
        playback_layout = QHBoxLayout()
        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play_video)
        playback_layout.addWidget(self.play_button)

        self.pause_button = QPushButton()
        self.pause_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        self.pause_button.clicked.connect(self.pause_video)
        playback_layout.addWidget(self.pause_button)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderMoved.connect(self.seek_video)
        playback_layout.addWidget(self.slider)

        layout.addLayout(playback_layout)

        # Add spinbox for increment value
        increment_layout = QHBoxLayout()
        increment_label = QLabel("Set Movement Increment:")
        self.increment_spinbox = QSpinBox()
        self.increment_spinbox.setMinimum(1)  # Minimum increment
        self.increment_spinbox.setMaximum(100)  # Maximum increment
        self.increment_spinbox.setValue(self.increment_value)  # Default value
        self.increment_spinbox.valueChanged.connect(self.update_increment_value)

        increment_layout.addWidget(increment_label)
        increment_layout.addWidget(self.increment_spinbox)
        layout.addLayout(increment_layout)

        # Arrow Buttons for Coordinate Adjustment
        arrow_layout = QHBoxLayout()
        self.left_button = QPushButton('←')
        self.left_button.clicked.connect(self.move_left)
        arrow_layout.addWidget(self.left_button)

        up_down_layout = QVBoxLayout()
        self.up_button = QPushButton('↑')
        self.up_button.clicked.connect(self.move_up)
        up_down_layout.addWidget(self.up_button)

        self.down_button = QPushButton('↓')
        self.down_button.clicked.connect(self.move_down)
        up_down_layout.addWidget(self.down_button)

        arrow_layout.addLayout(up_down_layout)

        self.right_button = QPushButton('→')
        self.right_button.clicked.connect(self.move_right)
        arrow_layout.addWidget(self.right_button)

        layout.addLayout(arrow_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status Text
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)

        self.setLayout(layout)

    def update_increment_value(self, value):
        """Update the increment value for movements"""
        self.increment_value = value
        self.status_text.append(f"Increment value set to: {self.increment_value}")

    def upload_video(self):
        options = QFileDialog.Options()
        video_path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi);;All Files (*)", options=options)
        if video_path:
            self.status_text.append(f"Selected video: {video_path}")
            self.video_capture = cv2.VideoCapture(video_path)
            self.total_frames = int(self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            self.slider.setRange(0, self.total_frames)
            self.video_loaded = True
            self.current_frame_number = 0

            # Read and display the first frame
            ret, frame = self.video_capture.read()
            if ret:
                self.display_frame(frame)
            else:
                self.status_text.append("Failed to read the first frame of the video.")
        else:
            self.status_text.append("No video selected.")

    def play_video(self):
        if self.video_loaded:
            self.is_paused = False
            self.timer.start(int(1000 / self.fps))

    def pause_video(self):
        if self.video_loaded:
            self.is_paused = True
            self.timer.stop()

    def seek_video(self, frame_number):
        if self.video_loaded:
            self.pause_video()
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.current_frame_number = frame_number
            ret, frame = self.video_capture.read()
            if ret:
                self.display_frame(frame)

    def next_frame(self):
        if not self.is_paused and self.video_loaded:
            ret, frame = self.video_capture.read()
            if ret:
                self.current_frame_number += 1
                self.slider.blockSignals(True)
                self.slider.setValue(self.current_frame_number)
                self.slider.blockSignals(False)
                self.display_frame(frame)
            else:
                self.timer.stop()

    def display_frame(self, frame):
        if self.pose_data is not None:
            frame_number = self.current_frame_number
            if frame_number in self.pose_data.index:
                frame_pose = self.pose_data.loc[frame_number]
                frame = self.draw_pose_on_frame(frame, frame_pose)
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg).scaled(self.video_label.width(), self.video_label.height(), Qt.KeepAspectRatio)
        self.video_label.setPixmap(pixmap)

    def draw_pose_on_frame(self, frame, frame_pose):
        frame_pose_df = frame_pose.unstack(level=-1)
        for (scorer, bp), coords in frame_pose_df.iterrows():
            try:
                x = coords['x'] + self.move_x
                y = coords['y'] + self.move_y
                x = int(x)
                y = int(y)
                cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)
            except KeyError:
                continue
        return frame

    def upload_files(self):
        options = QFileDialog.Options()
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select DLC Position Data Files", "", "CSV Files (*.csv);;All Files (*)", options=options
        )
        if files:
            self.files_to_convert = files
            # For displaying pose data, use the first file
            pose_file = files[0]
            self.pose_data = self.read_pose_data(pose_file)
            self.status_text.append(f"Selected {len(files)} file(s) for conversion.")
            self.status_text.append(f"Pose data loaded from {pose_file}")
            self.convert_button.setEnabled(True)
        else:
            self.status_text.append("No files selected.")

    def read_pose_data(self, pose_file):
        # Read pose data from CSV
        dlc_data = pd.read_csv(pose_file, header=[0, 1, 2], index_col=0, sep=',')
        return dlc_data

    def move_left(self):
        self.move_x -= self.increment_value
        self.status_text.append(f"Moving coordinates left by {self.increment_value}. Total offset: ({self.move_x}, {self.move_y})")

    def move_right(self):
        self.move_x += self.increment_value
        self.status_text.append(f"Moving coordinates right by {self.increment_value}. Total offset: ({self.move_x}, {self.move_y})")

    def move_up(self):
        self.move_y -= self.increment_value
        self.status_text.append(f"Moving coordinates up by {self.increment_value}. Total offset: ({self.move_x}, {self.move_y})")

    def move_down(self):
        self.move_y += self.increment_value
        self.status_text.append(f"Moving coordinates down by {self.increment_value}. Total offset: ({self.move_x}, {self.move_y})")

    def convert_files(self):
        if not self.video_loaded:
            QMessageBox.warning(self, "Warning", "Please upload a video first!")
            return

        default_output_dir = os.path.join(os.path.dirname(self.files_to_convert[0]), 'AdjustedPoseData')
        self.output_dir = default_output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        self.status_text.append(f"Converting files with offset ({self.move_x}, {self.move_y}) to '{self.output_dir}'")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.convert_button.setEnabled(False)
        self.upload_button.setEnabled(False)

        # Start the conversion in a separate thread
        self.thread = ConverterThread(self.files_to_convert, self.output_dir, self.move_x, self.move_y)
        self.thread.progress.connect(self.update_progress)
        self.thread.status_message.connect(self.update_status)
        self.thread.conversion_complete.connect(self.conversion_finished)
        self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_status(self, message):
        self.status_text.append(message)

    def conversion_finished(self):
        self.status_text.append("Conversion completed.")
        self.convert_button.setEnabled(True)
        self.upload_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "Conversion Complete", "All files have been converted successfully.")


class ConverterThread(QThread):
    progress = pyqtSignal(int)
    status_message = pyqtSignal(str)
    conversion_complete = pyqtSignal()

    def __init__(self, files, output_dir, move_x, move_y):
        super().__init__()
        self.files = files
        self.output_dir = output_dir
        self.move_x = move_x
        self.move_y = move_y

    def run(self):
        total_files = len(self.files)
        for index, dlc_file in enumerate(self.files, start=1):
            try:
                self.status_message.emit(f"Processing file {index}/{total_files}: {os.path.basename(dlc_file)}")
                filename = os.path.basename(dlc_file)
                base_name, ext = os.path.splitext(filename)
                output_file = os.path.join(self.output_dir, f"{base_name}_adjusted{ext}")
                self.convert_file(dlc_file, output_file)
                progress_percent = int((index / total_files) * 100)
                self.progress.emit(progress_percent)
            except Exception as e:
                self.status_message.emit(f"Error processing {os.path.basename(dlc_file)}: {str(e)}")
        self.conversion_complete.emit()

    def convert_file(self, dlc_file, output_file):
        try:
            # Read the DLC data with multi-level headers, ignoring the frame number (index_col=0)
            dlc_data = pd.read_csv(dlc_file, header=[0, 1, 2], index_col=0, sep=',')

            # Flatten multi-level columns
            flat_columns = [f"{bodypart}_{coord}" for scorer, bodypart, coord in dlc_data.columns]
            dlc_data.columns = flat_columns

            # Filter for nose, head (to be renamed centerbody), and tail (to be renamed tailbase)
            filtered_columns = []
            for col in dlc_data.columns:
                if 'nose' in col or 'head' in col or 'tail' in col:
                    filtered_columns.append(col)

            dlc_data = dlc_data[filtered_columns]

            # Rename columns: 'head' --> 'centerbody', 'tail' --> 'tailbase'
            renamed_columns = []
            for col in dlc_data.columns:
                if 'head' in col:
                    renamed_columns.append(col.replace('head', 'centerbody'))
                elif 'tail' in col:
                    renamed_columns.append(col.replace('tail', 'tailbase'))
                else:
                    renamed_columns.append(col)  # 'nose' remains unchanged

            dlc_data.columns = renamed_columns

            # Apply adjustments to the x and y coordinates
            for col in dlc_data.columns:
                if col.endswith('_x'):
                    dlc_data[col] += self.move_x
                elif col.endswith('_y'):
                    dlc_data[col] += self.move_y

            # Create multi-level headers for the final output, skipping the frame number
            header1 = []
            header2 = []
            header3 = []

            for col in dlc_data.columns:
                body_part, coord = col.rsplit('_', 1)
                header1.append('Body1')  # Adjust this based on the desired DLC scorer
                header2.append(body_part)
                header3.append(coord)

            # Convert to the formatted CSV format (3 header rows)
            formatted_data = pd.DataFrame(dlc_data.values, columns=pd.MultiIndex.from_arrays([header1, header2, header3]))

            # Save the adjusted file without the frame number (index=False)
            formatted_data.to_csv(output_file, index=False)

        except pd.errors.ParserError as e:
            self.status_message.emit(f"Parsing error in file {dlc_file}: {str(e)}")
        except Exception as e:
            self.status_message.emit(f"Error processing file {dlc_file}: {str(e)}")


def main():
    app = QApplication(sys.argv)
    converter_app = ConverterApp()
    converter_app.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()

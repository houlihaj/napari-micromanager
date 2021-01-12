import sys
import os
import time
from PyQt5 import QtWidgets as QtW
from qtpy import uic
from pathlib import Path
import pymmcore
from qtpy.QtWidgets import QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5 import QtCore
import numpy as np
from napari.qt import thread_worker
from pyfirmata2 import Arduino, util
import concurrent.futures
import threading#

from mmcore_pymmcore import MMCore
from multid_widget import MultiDWidget
from optocamp_widget import OptocampWidget 

#dir_path = Path(__file__).parent
icon_path = Path(__file__).parent/'icons'

UI_FILE = str(Path(__file__).parent / "micromanager_gui.ui")
DEFAULT_CFG_FILE = str((Path(__file__).parent / "demo_config.cfg").absolute())#look for the 'demo_config.cfg' in the parent folder 
DEFAULT_CFG_NAME = 'demo.cfg'

mmcore = MMCore()

class MainWindow(QtW.QMainWindow):
    # The UI_FILE above contains these objects:
    cfg_LineEdit: QtW.QLineEdit
    browse_cfg_Button: QtW.QPushButton
    load_cgf_Button: QtW.QPushButton

    objective_groupBox: QtW.QGroupBox
    objective_comboBox: QtW.QComboBox
    
    camera_groupBox: QtW.QGroupBox
    bin_comboBox: QtW.QComboBox
    bit_comboBox: QtW.QComboBox

    position_groupBox: QtW.QGroupBox
    x_lineEdit: QtW.QLineEdit
    y_lineEdit: QtW.QLineEdit
    z_lineEdit: QtW.QLineEdit
    pos_update_Button: QtW.QPushButton

    stage_groupBox: QtW.QGroupBox
    XY_groupBox: QtW.QGroupBox
    Z_groupBox: QtW.QGroupBox
    left_Button: QtW.QPushButton
    right_Button: QtW.QPushButton
    y_up_Button: QtW.QPushButton
    y_down_Button: QtW.QPushButton
    up_Button: QtW.QPushButton
    down_Button: QtW.QPushButton
    xy_step_size_SpinBox: QtW.QSpinBox
    z_step_size_doubleSpinBox: QtW.QDoubleSpinBox

    tabWidget: QtW.QTabWidget
    snap_live_tab: QtW.QWidget
    multid_tab: QtW.QWidget
    optocamp_tab: QtW.QWidget

    snap_channel_groupBox: QtW.QGroupBox
    snap_channel_comboBox: QtW.QComboBox
    exp_spinBox: QtW.QSpinBox
    snap_Button: QtW.QPushButton
    live_Button: QtW.QPushButton

    max_val_lineEdit: QtW.QLineEdit
    min_val_lineEdit: QtW.QLineEdit

    def enable(self):#Enable the gui (when .cfg is loaded)
        self.objective_groupBox.setEnabled(True)
        self.camera_groupBox.setEnabled(True)
        self.stage_groupBox.setEnabled(True)
        self.position_groupBox.setEnabled(True)
        self.XY_groupBox.setEnabled(True)
        self.Z_groupBox.setEnabled(True)
        self.pos_update_Button.setEnabled(True)
        self.xy_step_size_SpinBox.setEnabled(True)
        self.z_step_size_doubleSpinBox.setEnabled(True)
        self.left_Button.setEnabled(True)
        self.right_Button.setEnabled(True)
        self.y_up_Button.setEnabled(True)
        self.y_down_Button.setEnabled(True)
        self.up_Button.setEnabled(True)
        self.down_Button.setEnabled(True)
        self.snap_channel_comboBox.setEnabled(True)
        self.exp_spinBox.setEnabled(True)
        self.snap_Button.setEnabled(True)
        self.live_Button.setEnabled(True)

    def disable(self):#Disable the gui (if .cfg is not loaded)
        self.objective_groupBox.setEnabled(False)
        self.camera_groupBox.setEnabled(False)
        self.stage_groupBox.setEnabled(False)
        self.position_groupBox.setEnabled(False)
        self.XY_groupBox.setEnabled(False)
        self.Z_groupBox.setEnabled(False)
        self.pos_update_Button.setEnabled(False)
        self.xy_step_size_SpinBox.setEnabled(False)
        self.z_step_size_doubleSpinBox.setEnabled(False)
        self.left_Button.setEnabled(False)
        self.right_Button.setEnabled(False)
        self.y_up_Button.setEnabled(False)
        self.y_down_Button.setEnabled(False)
        self.up_Button.setEnabled(False)
        self.down_Button.setEnabled(False)
        self.snap_channel_comboBox.setEnabled(False)
        self.exp_spinBox.setEnabled(False)
        self.snap_Button.setEnabled(False)
        self.live_Button.setEnabled(False)
        
        
    def __init__(self, viewer):
        super().__init__()

        self.viewer = viewer
        self.worker = None

        uic.loadUi(UI_FILE, self)#load QtDesigner .ui file

        self.cfg_LineEdit.setText(DEFAULT_CFG_NAME)#fill cfg line with DEFAULT_CFG_NAME ('demo.cfg')

        #connect buttons
        self.load_cgf_Button.clicked.connect(self.load_cfg)
        self.browse_cfg_Button.clicked.connect(self.browse_cfg)

        self.pos_update_Button.clicked.connect(self.update_stage_position)
        self.left_Button.clicked.connect(self.stage_x_left)
        self.right_Button.clicked.connect(self.stage_x_right)
        self.y_up_Button.clicked.connect(self.stage_y_up)
        self.y_down_Button.clicked.connect(self.stage_y_down)
        self.up_Button.clicked.connect(self.stage_z_up)
        self.down_Button.clicked.connect(self.stage_z_down)

        self.snap_Button.clicked.connect(self.snap)
        self.live_Button.clicked.connect(self.toggle_live)

        #button's icon
        #arrows icons
        self.left_Button.setIcon(QIcon(str(icon_path/'left_arrow_1.svg')))
        self.left_Button.setIconSize(QtCore.QSize(30,30)) 
        self.right_Button.setIcon(QIcon(str(icon_path/'right_arrow_1.svg')))
        self.right_Button.setIconSize(QtCore.QSize(30,30)) 
        self.y_up_Button.setIcon(QIcon(str(icon_path/'up_arrow_1.svg')))
        self.y_up_Button.setIconSize(QtCore.QSize(30,30)) 
        self.y_down_Button.setIcon(QIcon(str(icon_path/'down_arrow_1.svg')))
        self.y_down_Button.setIconSize(QtCore.QSize(30,30))
        self.up_Button.setIcon(QIcon(str(icon_path/'up_arrow.svg')))
        self.up_Button.setIconSize(QtCore.QSize(30,30)) 
        self.down_Button.setIcon(QIcon(str(icon_path/'down_arrow.svg')))
        self.down_Button.setIconSize(QtCore.QSize(30,30)) 
        #snap/live icons
        self.snap_Button.setIcon(QIcon(str(icon_path/'cam.svg')))
        self.snap_Button.setIconSize(QtCore.QSize(30,30))
        self.live_Button.setIcon(QIcon(str(icon_path/'vcam.svg')))
        self.live_Button.setIconSize(QtCore.QSize(40,40)) 

        #connect comboBox
        self.objective_comboBox.currentIndexChanged.connect(self.change_objective)
        self.bit_comboBox.currentIndexChanged.connect(self.bit_changed)
        self.bin_comboBox.currentIndexChanged.connect(self.bin_changed)

        #connect spinBox
        # self.delay_spinBox.valueChanged.connect(self.frame_values_changed)
        # self.interval_spinBox_1.valueChanged.connect(self.frame_values_changed)
        # self.Pulses_spinBox.valueChanged.connect(self.frame_values_changed)
        # self.exp_spinBox_1.valueChanged.connect(self.frame_values_changed)

        # self.led_start_pwr_spinBox.valueChanged.connect(self.led_values_changed)
        # self.led_pwr_inc_spinBox.valueChanged.connect(self.led_values_changed)
        # self.Pulses_spinBox.valueChanged.connect(self.led_values_changed)

    def browse_cfg(self):
        file_dir = QFileDialog.getOpenFileName(self, '', '⁩', 'cfg(*.cfg)')
        self.new_cfg_file = file_dir[0]
        cfg_name=os.path.basename(str(self.new_cfg_file))
        self.cfg_LineEdit.setText(str(cfg_name))
        self.disable()
        self.max_val_lineEdit.setText("None")
        self.min_val_lineEdit.setText("None")

    def load_cfg(self):
        self.enable()

        #reset combo boxes from previous .cfg settings
        self.objective_comboBox.clear()
        self.bin_comboBox.clear()
        self.bit_comboBox.clear()
        self.snap_channel_comboBox.clear()
        #self.oc_channel_comboBox.clear()

        cfg_file = self.cfg_LineEdit.text()
        if cfg_file == DEFAULT_CFG_NAME:
            self.new_cfg_file = DEFAULT_CFG_FILE

        try:
            mmcore.loadSystemConfiguration(self.new_cfg_file) #load the configuration file
        except KeyError:
            print('Select a valid .cfg file.')
    
        # Get Camera Options
        self.cam_device = mmcore.getCameraDevice()
        cam_props = mmcore.getDevicePropertyNames(self.cam_device)
        print(cam_props)
        if "Binning" in cam_props:
            bin_opts = mmcore.getAllowedPropertyValues(self.cam_device, "Binning")
            self.bin_comboBox.addItems(bin_opts)
            self.bin_comboBox.setCurrentText(mmcore.getProperty(self.cam_device, "Binning"))
            mmcore.setProperty(self.cam_device, "Binning", "1")

        if "PixelType" in cam_props:
            px_t = mmcore.getAllowedPropertyValues(self.cam_device, "PixelType")
            self.bit_comboBox.addItems(px_t)
            if '16' in px_t:
                self.bit_comboBox.setCurrentText("16bit")
                mmcore.setProperty(self.cam_device, "PixelType", "16bit")
        
        # Get Objective Options
        if "Objective" in mmcore.getLoadedDevices():
            mmcore.setPosition("Z_Stage", 50)#just to test, should be removed
            obj_opts = mmcore.getStateLabels("Objective")
            self.objective_comboBox.addItems(obj_opts)
            self.objective_comboBox.setCurrentText(obj_opts[0])
            
        # Get Channel List
        if "Channel" in mmcore.getAvailableConfigGroups():
            channel_list = list(mmcore.getAvailableConfigs("Channel"))
            self.snap_channel_comboBox.addItems(channel_list)
        else:
            print("Could not find 'Channel' in the ConfigGroups")

        self.update_stage_position()

        self.max_val_lineEdit.setText("None")
        self.min_val_lineEdit.setText("None")

#–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––
#set (and print) properties when value/string change
# def cam_changed(self):
    def bit_changed(self):
        mmcore.setProperty(self.cam_device, "PixelType", self.bit_comboBox.currentText())
        print(mmcore.getProperty(mmcore.getCameraDevice(), "PixelType"))
    
    def bin_changed(self):
        mmcore.setProperty(self.cam_device, "Binning", self.bin_comboBox.currentText())
        print(mmcore.getProperty(mmcore.getCameraDevice(), "Binning"))

    # def cam_changed(self):
#–––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––

    def update_stage_position(self):
        x = int(mmcore.getXPosition())
        y = int(mmcore.getYPosition())
        z = int(mmcore.getPosition("Z_Stage"))
        self.x_lineEdit.setText(str('%.0f'%x))
        self.y_lineEdit.setText(str('%.0f'%y))
        self.z_lineEdit.setText(str('%.1f'%z))

    def stage_x_left(self):
        xpos = mmcore.getXPosition()
        ypos = mmcore.getYPosition()
        val = int(self.xy_step_size_SpinBox.value())
        mmcore.setXYPosition((xpos + (- val)),ypos) 
        x_new = int(mmcore.getXPosition())
        self.x_lineEdit.setText((str('%.0f'%x_new)))
        mmcore.waitForDevice("XY_Stage")
    
    def stage_x_right(self):
        xpos = mmcore.getXPosition()
        ypos = mmcore.getYPosition()
        val = int(self.xy_step_size_SpinBox.value())
        mmcore.setXYPosition((xpos + val),ypos) 
        x_new = int(mmcore.getXPosition())
        self.x_lineEdit.setText((str('%.0f'%x_new)))
        mmcore.waitForDevice("XY_Stage")

    def stage_y_up(self):
        xpos = mmcore.getXPosition()
        ypos = mmcore.getYPosition()
        val = int(self.xy_step_size_SpinBox.value())
        mmcore.setXYPosition(xpos,(ypos + val)) 
        y_new = int(mmcore.getYPosition())
        self.y_lineEdit.setText((str('%.0f'%y_new)))
        mmcore.waitForDevice("XY_Stage")

    def stage_y_down(self):
        xpos = mmcore.getXPosition()
        ypos = mmcore.getYPosition()
        val = int(self.xy_step_size_SpinBox.value())
        mmcore.setXYPosition(xpos,(ypos + (- val))) 
        y_new = int(mmcore.getYPosition())
        self.y_lineEdit.setText((str('%.0f'%y_new)))
        mmcore.waitForDevice("XY_Stage")
        
    def stage_z_up(self):
        zpos = mmcore.getPosition("Z_Stage")
        z_val = float(self.z_step_size_doubleSpinBox.value())
        mmcore.setPosition("Z_Stage", zpos + z_val) 
        z_new = float(mmcore.getPosition("Z_Stage"))
        self.z_lineEdit.setText((str('%.1f'%z_new)))
        mmcore.waitForDevice("Z_Stage")
    
    def stage_z_down(self):
        zpos = mmcore.getPosition("Z_Stage")
        z_val = float(self.z_step_size_doubleSpinBox.value())
        mmcore.setPosition("Z_Stage", zpos + (-z_val)) 
        z_new = float(mmcore.getPosition("Z_Stage"))
        self.z_lineEdit.setText((str('%.1f'%z_new)))
        mmcore.waitForDevice("Z_Stage")

    def change_objective(self):
        print('changeing objective...')
        currentZ = mmcore.getPosition("Z_Stage")
        print(f"currentZ: {currentZ}")
        mmcore.setPosition("Z_Stage", 0)#set low z position
        mmcore.waitForDevice("Z_Stage")
        self.update_stage_position()
        print(self.objective_comboBox.currentText())
        mmcore.setProperty("Objective", "Label", self.objective_comboBox.currentText())
        mmcore.waitForDevice("Objective")
        print(f"downpos: {mmcore.getPosition('Z_Stage')}")
        mmcore.setPosition("Z_Stage", currentZ)
        mmcore.waitForDevice("Z_Stage")
        print(f"upagain: {mmcore.getPosition('Z_Stage')}")
        print(f"OBJECTIVE: {mmcore.getProperty('Objective', 'Label')}")
        self.update_stage_position()

    def update_viewer(self, data):
        try:
            self.viewer.layers["preview"].data = data
        except KeyError:
            self.viewer.add_image(data, name="preview")

    def snap(self):
        self.stop_live()
        mmcore.setExposure(int(self.exp_spinBox.value()))
        mmcore.setProperty("Cam", "Binning", self.bin_comboBox.currentText())
        mmcore.setProperty("Cam", "PixelType", self.bit_comboBox.currentText())
        mmcore.setConfig("Channel", self.snap_channel_comboBox.currentText())
        #mmcore.waitForDevice('')
        mmcore.snapImage()
        self.update_viewer(mmcore.getImage())
        
        try:#display max and min gray values
            min_v = np.min(self.viewer.layers["preview"].data)
            self.min_val_lineEdit.setText(str(min_v))
            max_v = np.max(self.viewer.layers["preview"].data)
            self.max_val_lineEdit.setText(str(max_v))
        except KeyError:
            pass
        
    def start_live(self):
        
        @thread_worker(connect={"yielded": self.update_viewer})
        def live_mode():
            import time

            while True:
                mmcore.setExposure(int(self.exp_spinBox.value()))
                mmcore.setProperty("Cam", "Binning", self.bin_comboBox.currentText())
                mmcore.setProperty("Cam", "PixelType", self.bit_comboBox.currentText())
                mmcore.setConfig("Channel", self.snap_channel_comboBox.currentText())
                mmcore.snapImage()
                yield mmcore.getImage()

                try:
                    min_v = np.min(self.viewer.layers["preview"].data)
                    self.min_val_lineEdit.setText(str(min_v))
                    max_v = np.max(self.viewer.layers["preview"].data)
                    self.max_val_lineEdit.setText(str(max_v))
                except KeyError:
                    pass

                time.sleep(0.03)

        self.live_Button.setText("Stop")
        self.worker = live_mode()

    def stop_live(self):
        if self.worker:
            self.worker.quit()
            self.worker = None
            self.live_Button.setText("Live")
            self.live_Button.setIcon(QIcon(str(icon_path/'vcam.svg')))
            self.live_Button.setIconSize(QtCore.QSize(40,40)) 
            
    def toggle_live(self, event=None):
        #same as writing: self.stop_live() if self.worker is not None else self.start_live()
        if self.worker == None:
            self.start_live()
            self.live_Button.setIcon(QIcon(str(icon_path/'cam_stop.svg')))
            self.live_Button.setIconSize(QtCore.QSize(40,40)) 
        else:
            self.stop_live()
            self.live_Button.setIcon(QIcon(str(icon_path/'vcam.svg')))
        self.live_Button.setIconSize(QtCore.QSize(40,40)) 

#     def detect_arduino(self):
#         try:
#             self.arduino_board_comboBox.clear()
#             self.board = Arduino(Arduino.AUTODETECT)
#             board_port = [str(self.board)]
#             self.arduino_board_comboBox.addItems(board_port)
#             it = util.Iterator(self.board)
#             it.start()
#             self.led = self.board.get_pin('d:3:p')#set led pin of arduino
#             self.exp_groupBox_1.setEnabled(True)
#             self.exp_spinBox_1.setEnabled(True)
#             self.frames_groupBox.setEnabled(True)
#             self.led_groupBox.setEnabled(True)
#             self.save_groupBox_rec.setEnabled(True)
#             self.rec_Button.setEnabled(True)
#         except KeyError:
#             print('No Arduino Found')

#     def frame_values_changed(self):
#         self.n_frames = (self.delay_spinBox.value() + (self.interval_spinBox_1.value()*self.Pulses_spinBox.value()))-1
#         self.tot_frames_lineEdit.setText(str(self.n_frames))
#         self.rec_time_lineEdit.setText(str((self.n_frames*self.exp_spinBox_1.value()/1000)))
#         frames_stim = []
#         fr = self.delay_spinBox.value()
#         for i in range (self.Pulses_spinBox.value()):
#             frames_stim.append(fr)
#             fr = fr + self.interval_spinBox_1.value()
#         self.frame_w_pulses_lineEdit.setText(str(frames_stim))


#     def led_values_changed(self):
#         led_power_used = []
#         pwr = self.led_start_pwr_spinBox.value()
#         for i in range (self.Pulses_spinBox.value()):
#             led_power_used.append(pwr)
#             pwr = pwr + self.led_pwr_inc_spinBox.value()
        
#         self.led_pwrs_lineEdit.setText(str(led_power_used))

#         power_max = (self.led_start_pwr_spinBox.value()+(self.led_pwr_inc_spinBox.value()*(self.Pulses_spinBox.value()-1)))
#         self.led_max_pwr_lineEdit.setText(str(power_max))
        
#         if power_max > 100:
#             self.rec_Button.setEnabled(False)
#             print('LED max power exceded!!!')
#         else:
#             self.rec_Button.setEnabled(True)

#         led_power_used.clear()

#     def save_recordongs(self):
#         save_groupBox_rec: QtW.QGroupBox
#         dir_rec_lineEdit: QtW.QLineEdit
#         browse_rec_save_Button: QtW.QPushButton
#         fname_rec_lineEdit: QtW.QLineEdit

    
#     def snap_optocamp(self, exp_t):
#         time.sleep(0.001)
#         mmcore.setExposure(exp_t)
#         #print('  snap')
#         s_cam = time.perf_counter()
#         mmcore.snapImage()
#         e_cam = time.perf_counter()
#         print(f'   cam on for {round(e_cam - s_cam, 4)} second(s)')################################################
#         #self.update_viewer(mmcore.getImage())#?????

#     def led_on(self, power, on_for):
#         self.led.write(power)
#         s = time.perf_counter()
#         time.sleep(on_for)
#         self.led.write(0.0)
#         e = time.perf_counter()
#         print(f'    led on for {round(e-s, 4)} second(s)')################################################
#         #print(f'  led_power = {power}')
        
#     def start_recordings(self):
#         self.stop_live()
#         time_stamp = []
        
#         #self.n_frames = (self.delay_spinBox.value() + (self.interval_spinBox_1.value()*self.Pulses_spinBox.value()))-1

#         stim_frame = self.delay_spinBox.value()
#         start_led_power = self.led_start_pwr_spinBox.value()
#         #print(f'start led power (%): {start_led_power}')
#         #print(f'start led power (float): {float(start_led_power/100)}')

#         for i in range (1,(self.n_frames+1)):
            
#             #print(f'frame: {i}')

#             mmcore.setProperty("Cam", "Binning", self.bin_comboBox.currentText())
#             mmcore.setProperty("Cam", "PixelType", self.bit_comboBox.currentText() + "bit")
#             mmcore.setConfig("Channel", self.oc_channel_comboBox.currentText())
            
#             if i == stim_frame:

#                 tm = time.time()
#                 time_stamp.append(tm)

#                 start = time.perf_counter()

#                 ########
#                 # self.snap_optocamp(int(self.exp_spinBox_1.value()))
#                 # self.led_on((start_led_power/100), (int(self.exp_spinBox_1.value())/1000))
#                 # ########

#                 # ########
#                 # t_snap = threading.Thread(target=self.snap_optocamp, args = [int(self.exp_spinBox_1.value())])
#                 # t_led = threading.Thread(target=self.led_on, args = [(start_led_power/100),(int(self.exp_spinBox_1.value())/1000)])
                
#                 # t_snap.start()
#                 # t_led.start()

#                 # t_snap.join()
#                 # t_led.join()
#                 ########

#                 #######
#                 with concurrent.futures.ThreadPoolExecutor() as executor:
#                     t1 = executor.submit(self.snap_optocamp, int(self.exp_spinBox_1.value()))
#                     t2 = executor.submit(self.led_on, float(start_led_power/100), (int(self.exp_spinBox_1.value())/1000))
#                 #######

#                 finish = time.perf_counter()
#                 print(f'Finished in {round(finish-start, 4)} second(s)')

#                 stim_frame = stim_frame + self.interval_spinBox_1.value()
#                 start_led_power = start_led_power + self.led_pwr_inc_spinBox.value()
#                 #print(f'start_led_power: {start_led_power}, interval: {self.led_pwr_inc_spinBox.value()}')
#                 #print(f'new_power: {start_led_power}')
            
#             else:
#                 self.snap_optocamp(int(self.exp_spinBox_1.value()))
#                 tm = time.time()
#                 time_stamp.append(tm)
                
#         print('***END***')       
    
#         #self.board.exit()

#         #print('SUMMARY \n**********')
#         #print(f'Recordings lenght: {n_frames} frames')
#         #print(f'Number of Stimulations: {n_stimulations}')
#         #print(f'Frames when Stimulation occurred: {frames_stim}')
#         #print(f'Led Power: {led_power_used} percent')
#         #print('**********')

#         #gap_list = []
#         #for i in range (len(time_stamp)):
#         #    val1 = time_stamp[i]
#         #    if i<len(time_stamp)-1:
#         #        val2 = time_stamp[i+1]
#         #    else:
#         #        break
#         #    gap = (val2-val1)*1000
#         #    gap_list.append(gap)
#         #print(f'Timestamp: {gap_list[0]}, {gap_list[1]}, {gap_list[len(gap_list)-1]}')










# #self.objective_comboBox.currentIndexChanged.connect(self.change_objective)


        




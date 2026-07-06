import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QWidget, QLabel ,QStackedLayout ,QPushButton ,QSlider, QSpinBox, QComboBox ,QCheckBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt, QUrl ,QEvent
from PyQt6 import uic
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget




# 🌟 匯入你寫好的硬體大腦
from main import DLP_function
from engineering import EngineeringWindow
# ==========================================
# 🌟 新增：專屬的無邊框投影布幕與輪播引擎
# ==========================================
class ProjectionWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: black;")
        # 🌟 使用 QStackedLayout 把圖片和影片疊在一起
        self.layout = QStackedLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0) # 確保全螢幕無邊距
        # 1. 圖片顯示器 (底層)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.image_label)

        # 2. 影片播放器 (頂層)
        self.video_widget = QVideoWidget()
        self.layout.addWidget(self.video_widget)

        # 3. 初始化解碼大腦 (QMediaPlayer)
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput() # PyQt6 必須要掛音訊輸出，否則沒聲音
        self.player.setAudioOutput(self.audio_output)
        self.player.setVideoOutput(self.video_widget)
        
        # 設定影片無限輪迴播放 (測試 Pattern 必備)
        self.player.setLoops(-1)

        self.media_list = []      
        self.current_index = 0    
        

        


    def load_folder(self, folder_path):
        """讀取資料夾，支援圖片與影片，回傳 (是否成功, 第一張圖/影片的路徑)"""
        # 🌟 擴增支援的副檔名，把影片加進去
        valid_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.mp4', '.avi', '.mov', '.mkv'}
        self.media_list = []
        
        for file_name in os.listdir(folder_path):
            ext = os.path.splitext(file_name)[1].lower()
            if ext in valid_exts:
                self.media_list.append(os.path.join(folder_path, file_name))

        if not self.media_list:
            return False, ""

        self.current_index = 0
        self.show_current_media()
        return True, self.media_list[self.current_index]

    def prev_image(self):
        """切換上一個檔案"""
        if not self.media_list: return ""
        self.current_index = (self.current_index - 1) % len(self.media_list)
        self.show_current_media()
        return self.media_list[self.current_index]

    def next_image(self):
        """切換下一個檔案"""
        if not self.media_list: return ""
        self.current_index = (self.current_index + 1) % len(self.media_list)
        self.show_current_media()
        return self.media_list[self.current_index]

    def show_current_media(self):
        """核心邏輯：判斷是圖片還是影片，並自動切換圖層"""
        path = self.media_list[self.current_index]
        ext = os.path.splitext(path)[1].lower()
        
        # 分類：這是不是影片？
        if ext in {'.mp4', '.avi', '.mov', '.mkv'}:
            # 🎬 切換到影片圖層
            self.layout.setCurrentWidget(self.video_widget)
            
            # PyQt6 讀取本機檔案必須用 QUrl.fromLocalFile 轉換
            self.player.setSource(QUrl.fromLocalFile(path))
            self.player.play()
        else:
            # 🖼️ 切換到圖片圖層
            self.player.stop() # 確保如果上一張是影片，先把它停掉
            self.layout.setCurrentWidget(self.image_label)
            
            pixmap = QPixmap(path)
            scaled_pixmap = pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)

    # ==========================================
    # ⌨️ 保留鍵盤防呆控制 (以備不時之需)
    # ==========================================
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            print("🛑 收到 ESC 指令，關閉投影畫面")
            self.close()

    def closeEvent(self, event):
        """關閉視窗時，確保影片停止播放，釋放記憶體"""
        self.player.stop()
        event.accept()

# ==========================================
# 🌟 主控台介面
# ==========================================
class DLP_GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        uic.loadUi("test (2).ui", self)
        
        # 圖片載入
        ShortAxisFlip = QPixmap("ShortAxisFlip.png")
        LongAxisFlip = QPixmap("LongAxisFlip.png")
        self.ShortAxisFlip.setPixmap(ShortAxisFlip)
        self.LongAxisFlip.setPixmap(LongAxisFlip)
        
        # 2. 初始化底層硬體
        self.dlp = DLP_function()
        
        # 宣告投影視窗變數
        self.proj_window = None
        self.is_powered_on = True
        # system mode mapping
        self.system_mode_map = {
            0: 0x00, 
            1: 0x01,
            2: 0x03,
            3: 0x02,
        }

        self.execute_batch_command_set_map = {
            0: 0x07, 1: 0x08, 2: 0x09, 3: 0x0A,
            4: 0x0B, 5: 0x0C, 6: 0x0D, 7: 0x16,
            8: 0x10, 9: 0x12, 10: 0x15, 11: 0x17,
        }

        self.degamma_select_map = {
            0: 0x00, 
            1: 0x01,
        }

        # 3. 綁定按鈕與硬體指令
        self.last_sent_time = 0
        self.current_x = 0
        self.current_y = 0
        self.setup_connections()
        #self.horizontal_slider.valueChanged.connect(self.on_x_slider_moving)
        #self.vertical_slider.valueChanged.connect(self.on_y_slider_moving)
        #self.dimminglevel_slider.valueChanged.connect(self.on_dimminglevel_slider_moving)
        self.secret_buffer = ""
        self.EngineeringWindow = None
        self.x = 0x00

    def setup_connections(self):
        self.btn_r.clicked.connect(lambda: self.dlp.execute_batch_command_set(0x13))
        self.btn_g.clicked.connect(lambda: self.dlp.execute_batch_command_set(0x11))
        self.btn_b.clicked.connect(lambda: self.dlp.execute_batch_command_set(0x0F))
        self.btn_bk.clicked.connect(lambda: self.dlp.execute_batch_command_set(0x0E))
        self.btn_w.clicked.connect(lambda: self.dlp.execute_batch_command_set(0x14))
        self.btn_windows.clicked.connect(self.close_projection)

        self.system_mode_select.currentIndexChanged.connect(lambda index: self.on_system_mode_changed(index))
        self.execute_batch_command_set.currentIndexChanged.connect(lambda index: self.on_execute_batch_command_set_changed(index))
        self.degamma_select.currentIndexChanged.connect(lambda index: self.on_degamma_select_changed(index))
        self.ShortAxisFlip_checkBox.stateChanged.connect(self.on_flip_changed)
        self.LongAxisFlip_checkBox.stateChanged.connect(self.on_flip_changed)

        self.x_spinBox.setKeyboardTracking(False)
        self.y_spinBox.setKeyboardTracking(False)
        self.dimming_spinBox.setKeyboardTracking(False)

        # 雙向綁定
        self.horizontal_slider.valueChanged.connect(self.x_spinBox.setValue)
        self.vertical_slider.valueChanged.connect(self.y_spinBox.setValue)
        self.dimminglevel_slider.valueChanged.connect(self.dimming_spinBox.setValue)

        self.x_spinBox.valueChanged.connect(self.horizontal_slider.setValue)
        self.y_spinBox.valueChanged.connect(self.vertical_slider.setValue)
        self.dimming_spinBox.valueChanged.connect(self.dimminglevel_slider.setValue)

        self.x_spinBox.valueChanged.connect(self.on_x_slider_moving)
        self.y_spinBox.valueChanged.connect(self.on_y_slider_moving)
        self.dimming_spinBox.valueChanged.connect(self.on_dimminglevel_slider_moving)
        self.btn_off.toggled.connect(self.on_power_toggle)

        #self.btn_power.clicked.connect(self.on_power_button_clicked)

        #self.horizontal_slider.sliderMoved.connect(self.on_x_slider_moving)
        #self.vertical_slider.sliderMoved.connect(self.on_y_slider_moving)
        #self.dimminglevel_slider.sliderMoved.connect(self.on_dimminglevel_slider_moving)

        # 硬體觸發
        #self.horizontal_slider.sliderReleased.connect(self.on_x_slider_moving)
        #self.vertical_slider.sliderReleased.connect(self.on_y_slider_moving)
        #self.dimminglevel_slider.sliderReleased.connect(self.on_dimminglevel_slider_moving)

        #self.x_spinBox.editingFinished.connect(self.on_x_slider_moving)
        #self.y_spinBox.editingFinished.connect(self.on_y_slider_moving)
        #self.dimming_spinBox.editingFinished.connect(self.on_dimminglevel_slider_moving)

        self.btn_choose_folder.clicked.connect(self.on_choose_folder_clicked)
        self.btn_prev.clicked.connect(self.on_prev_image_clicked)
        self.btn_next.clicked.connect(self.on_next_image_clicked)


        for btn in self.findChildren(QPushButton):
            if btn.objectName() != "btn_off": 
                btn.installEventFilter(self)
                
        # 鎖定所有滑桿
        for slider in self.findChildren(QSlider):
            slider.installEventFilter(self)
            
        # 鎖定所有數字框
        for spin in self.findChildren(QSpinBox):
            spin.installEventFilter(self)
            
        # 鎖定所有下拉選單
        for combo in self.findChildren(QComboBox):
            combo.installEventFilter(self)

        for checkbox in self.findChildren(QCheckBox):
            checkbox.installEventFilter(self)


    # ==========================================
    # 🔌 硬體發送轉接頭
    # ==========================================
    def on_system_mode_changed(self, index):
        real_hex_cmd = self.system_mode_map.get(index)
        self.dlp.system_mode_select(real_hex_cmd)

    def on_execute_batch_command_set_changed(self, index):
        real_hex_cmd = self.execute_batch_command_set_map.get(index)
        self.dlp.execute_batch_command_set(real_hex_cmd)

    def on_degamma_select_changed(self, index):
        real_hex_cmd = self.degamma_select_map.get(index)
        self.dlp.degamma_select(real_hex_cmd)

    def on_flip_changed(self):
        is_v_checked = self.LongAxisFlip_checkBox.isChecked()
        is_h_checked = self.ShortAxisFlip_checkBox.isChecked()
        
        mode_val = 0x00
        if is_h_checked: mode_val |= 0x01  
        if is_v_checked: mode_val |= 0x02  
            
        print(f"🔄 翻轉狀態改變: 水平={is_h_checked}, 垂直={is_v_checked} -> 發送指令: 0x{mode_val:02X}")
        self.dlp.display_image_orientation(mode_val)

    def on_x_slider_moving(self, *args):
        final_value = self.x_spinBox.value()
        hardware_value = final_value * 2
        self.current_x = hardware_value
        self.send_bezel_command()

    def on_y_slider_moving(self, *args):
        final_value = self.y_spinBox.value()
        hardware_value = final_value * 4
        self.current_y = hardware_value
        self.send_bezel_command()

    def send_bezel_command(self):
        print(f"X={self.current_x}, Y={self.current_y}")
        self.dlp.bezel_adjustment(self.current_x, self.current_y)

    def on_dimminglevel_slider_moving(self, *args):
        final_value = self.dimming_spinBox.value()
        self.dlp.dimming_level(final_value)

    def on_power_toggle(self, checked):
        self.is_powered_on = not checked
        if checked:
            self.btn_off.setText("Power On")
            self.dlp.operating_mode(0x00)
        else:
            self.btn_off.setText("Power Off")
            self.dlp.operating_mode(0x01)

    def eventFilter(self, obj, event):
        # 偵測是否發生了「滑鼠左鍵點擊」的事件
        if event.type() == QEvent.Type.MouseButtonPress:
            
            # 如果目前是「斷電狀態 (False)」
            if  not self.is_powered_on:
                # 跳出你指定的英文警告彈窗
                QMessageBox.warning(self, "Warning", "Warning! Please power on before executing.")
                
                # 🌟 關鍵：回傳 True 代表「這個點擊事件我已經沒收處理了」
                # 底層的按鈕就不會收到訊號，原本的發送/紀錄/刪除功能就不會被執行！
                return True
                
        # 如果有通電，或者是其他的事件 (例如滑鼠移動)，就正常放行
        return super().eventFilter(obj, event)


    # ==========================================
    # 🚀 投影系統邏輯
    # ==========================================
    def on_choose_folder_clicked(self):
        """彈出選擇資料夾視窗，並啟動投影"""
        folder_path = QFileDialog.getExistingDirectory(self, "請選擇要投影的圖片資料夾")
        self.dlp.execute_batch_command_set(0x00)
        if not folder_path:
            return # 使用者按了取消
            
        print(f"✅ 使用者選擇了資料夾: {folder_path}")
        self.start_auto_projection(folder_path)


    def close_projection(self):
        """關閉無邊框投影視窗，讓 DLP 顯示原本的 Windows 桌面"""
        
        # 檢查投影視窗是否存在，且正在顯示中
        if self.proj_window and self.proj_window.isVisible():
            # 1. 停止影片播放 (確保記憶體與音效被釋放)
            self.proj_window.player.stop()
            
            # 2. 關閉視窗
            self.proj_window.close()
            
            # 3. 徹底清空變數，下次點擊資料夾時會重新生成一個乾淨的
            self.proj_window = None 
            
            # 4. 更新主控台的狀態文字
            self.windows_path.setText("📂 Display Status: \n🖥️ Projection Disabled (Desktop Mode)")
            print("🛑 投影已關閉，返回 Windows 桌面")
            
            # (選擇性防呆) 確保 DLP 確實處於外部影像源模式
            self.dlp.execute_batch_command_set(0x00)
            
        else:
            self.dlp.execute_batch_command_set(0x00)
            print("投放桌面")
            


            
    def find_dlp_screen(self):
        """掃描尋找 1152x576 的那一個螢幕"""
        screens = QApplication.screens()
        for screen in screens:
            geom = screen.geometry()
            if geom.width() == 1152 and geom.height() == 576:
                return screen
        return None

    def start_auto_projection(self, folder_path):
        dlp_screen = self.find_dlp_screen()

        if dlp_screen is None:
            QMessageBox.critical(self, "連線錯誤", "找不到 1152x576 的投影設備！\n請檢查 Windows 顯示設定。")
            return

        if self.proj_window is None:
            self.proj_window = ProjectionWindow()
            
        self.proj_window.setGeometry(dlp_screen.geometry())
        self.proj_window.showFullScreen()
        
        # 🌟 呼叫 load_folder，它現在會回傳是否成功，以及第一張圖的路徑
        success, first_image_path = self.proj_window.load_folder(folder_path)
        
        if success:
            # 成功讀取！更新主控台的文字
            self.windows_path.setText(f"📂 Display Status: \n{first_image_path}")
        else:
            QMessageBox.warning(self, "警告", "選擇的資料夾內沒有支援的圖片檔！")
            self.proj_window.close()
            self.windows_path.setText("❌ 無圖片")

    def on_prev_image_clicked(self):
        # 防呆：確保投影視窗已經打開，才允許切換
        if self.proj_window and self.proj_window.isVisible():
            # 呼叫投影視窗切換上一張，並拿回新的路徑
            current_path = self.proj_window.prev_image()
            filename = os.path.basename(current_path)
            self.windows_path.setText(f"📂 Display Status: \n{filename}")

    def on_next_image_clicked(self):
        if self.proj_window and self.proj_window.isVisible():
            # 呼叫投影視窗切換下一張，並拿回新的路徑
            current_path = self.proj_window.next_image()
            filename = os.path.basename(current_path)
            self.windows_path.setText(f"📂 Display Status: \n{filename}")

    # ==========================================
    # 🕵️‍♂️ 隱藏密碼偵測系統 (g -> i -> s -> Enter)
    # ==========================================
    def keyPressEvent(self, event):
        """攔截主視窗的鍵盤輸入，偵測工程密碼"""
        
        # 1. 如果按下的是 Enter 鍵 (包含大鍵盤跟數字鍵盤的 Enter)
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            # 檢查記憶體最後三個字是不是 "gis"
            if self.secret_buffer.endswith("gis"):
                self.unlock_engineering_mode()
                self.dlp.operating_mode(0x02)
            # 不管密碼對不對，按下 Enter 後就清空記憶體，重新來過
            self.secret_buffer = ""
            
        # 2. 如果按下的是一般字母，就記錄下來
        elif event.text():
            # 轉成小寫加到緩衝區，這樣使用者開著大寫鎖定打 "GIS" 也能通
            self.secret_buffer += event.text().lower()
            
            # 防呆：避免使用者亂打一通導致記憶體爆掉，我們永遠只留最後 10 個字元
            self.secret_buffer = self.secret_buffer[-10:]

        # 3. 確保 Qt 原本的鍵盤功能（如 Esc 關閉視窗）還能正常運作
        super().keyPressEvent(event)

    def unlock_engineering_mode(self):
        print("🔓 密碼正確！開啟工程模式視窗！")
        
        # 跳出提示框給個回饋
        QMessageBox.information(self, "解鎖成功", "權限已提升：進入工程模式")
        
        # 顯示你另外寫好的工程視窗 (假設你建了一個 EngineeringWindow 類別)
        if self.EngineeringWindow is None:
            self.EngineeringWindow = EngineeringWindow(self.dlp)
            #self.EngineeringWindow.dlp = self.dlp 
            
        # 🌟 3. 顯示視窗
        self.EngineeringWindow.show()
        self.EngineeringWindow.raise_()
        self.EngineeringWindow.activateWindow()

    def closeEvent(self, event):
        """關閉 GUI，安全釋放硬體與投影視窗"""
        print("\n🛑 關閉 GUI，安全釋放設備...")
        if self.proj_window:
            self.proj_window.close()
        self.dlp.close()
        event.accept()

# ==========================================
# 🚀 啟動程式
# ==========================================
if __name__ == '__main__':
    app = QApplication(sys.argv)
  
   
    
    window = DLP_GUI()
    window.show()
    sys.exit(app.exec())
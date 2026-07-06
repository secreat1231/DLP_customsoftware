import sys
from PyQt6.QtWidgets import QApplication, QMainWindow ,QToolTip
from PyQt6.QtGui import QPixmap ,QCursor
from PyQt6.QtCore import Qt
from PyQt6 import uic


import time

# 🌟 匯入你寫好的硬體大腦
from main import DLP_function

# 注意：因為你在 Designer 建立的是 QMainWindow，所以這裡要繼承 QMainWindow
class DLP_GUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 1. 載入你剛剛畫好的 UI 檔案
        # 這行會施展魔法：自動幫你把 btn_r, btn_g 變成 self.btn_r, self.btn_g！
        uic.loadUi("test.ui", self)
        ShortAxisFlip = QPixmap("ShortAxisFlip.png")
        LongAxisFlip = QPixmap("LongAxisFlip.png")
        #pixmap = pixmap.scaled(200, 100, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
        self.ShortAxisFlip.setPixmap(ShortAxisFlip)
        self.LongAxisFlip.setPixmap(LongAxisFlip)
        # 2. 初始化底層硬體
        self.dlp = DLP_function()
        
        #system mode mapping
        self.system_mode_map = {
            0: 0x00, 
            1: 0x01,
            2: 0x03,
            3: 0x02,
        }

        self.execute_batch_command_set_map= {
            0: 0x07,
            1: 0x08,
            2: 0x09,
            3: 0x0A,
            4: 0x0B,
            5: 0x0C,        
            6: 0x0D,
            7: 0x16,
            8: 0x10,
            9: 0x12,
            10: 0x15,
            11: 0x17,
        }

        self.degamma_select_map = {
            0: 0x00, 
            1: 0x01,
        }



        # 3. 綁定按鈕與硬體指令
        self.setup_connections()
        self.last_sent_time = 0
        self.current_x = 0
        self.current_y = 0
        self.horizontal_slider.valueChanged.connect(self.on_x_slider_moving)
        self.vertical_slider.valueChanged.connect(self.on_y_slider_moving)
        self.dimminglevel_slider.valueChanged.connect(self.on_dimminglevel_slider_moving)




    def setup_connections(self):
        """
        這就是 PyQt 的靈魂：Signals & Slots (信號與槽)
        把按鈕的「點擊(clicked)」連接(connect)到底層硬體的「發送指令」
        """
        self.btn_r.clicked.connect(lambda: self.dlp.execute_batch_command_set(0x13))
        self.btn_g.clicked.connect(lambda: self.dlp.execute_batch_command_set(0x11))
        self.btn_b.clicked.connect(lambda: self.dlp.execute_batch_command_set(0x0F))
        self.btn_bk.clicked.connect(lambda: self.dlp.execute_batch_command_set(0x0E))
        self.btn_w.clicked.connect(lambda: self.dlp.execute_batch_command_set(0x14))
        self.btn_windows.clicked.connect(lambda: self.dlp.execute_batch_command_set(0x00))


        self.system_mode_select.currentIndexChanged.connect(lambda index: self.on_system_mode_changed(index))
        self.execute_batch_command_set.currentIndexChanged.connect(lambda index: self.on_execute_batch_command_set_changed(index))
        self.degamma_select.currentIndexChanged.connect(lambda index: self.on_degamma_select_changed(index))
        self.ShortAxisFlip_checkBox.stateChanged.connect(self.on_flip_changed)
        self.LongAxisFlip_checkBox.stateChanged.connect(self.on_flip_changed)

        self.horizontal_slider.valueChanged.connect(self.x_spinBox.setValue)
        self.vertical_slider.valueChanged.connect(self.y_spinBox.setValue)
        self.dimminglevel_slider.valueChanged.connect(self.dimming_spinBox.setValue)

        self.x_spinBox.valueChanged.connect(self.horizontal_slider.setValue)
        self.y_spinBox.valueChanged.connect(self.vertical_slider.setValue)
        self.dimming_spinBox.valueChanged.connect(self.dimming_spinBox.setValue)

        self.horizontal_slider.sliderReleased.connect(self.on_x_slider_moving)
        self.vertical_slider.sliderReleased.connect(self.on_y_slider_moving)
        self.dimminglevel_slider.sliderReleased.connect(self.on_dimminglevel_slider_moving)


        self.x_spinBox.editingFinished.connect(self.on_x_slider_moving)
        self.y_spinBox.editingFinished.connect(self.on_y_slider_moving)
        self.dimming_spinBox.editingFinished.connect(self.on_dimminglevel_slider_moving)


    def on_system_mode_changed(self, index):
        #查上面system mode mapping
        real_hex_cmd = self.system_mode_map.get(index)
        self.dlp.system_mode_select(real_hex_cmd)

    def on_execute_batch_command_set_changed(self, index):
        #查上面execute batch command set mapping
        real_hex_cmd = self.execute_batch_command_set_map.get(index)
        self.dlp.execute_batch_command_set(real_hex_cmd)

    def on_degamma_select_changed(self, index):
        #查上面degamma select mapping
        real_hex_cmd = self.degamma_select_map.get(index)
        self.dlp.degamma_select(real_hex_cmd)


    def on_flip_changed(self):
        """
        當水平或垂直任何一個 CheckBox 被點擊時，都會觸發這裡
        """
        is_h_checked = self.LongAxisFlip_checkBox.isChecked()
        is_v_checked = self.ShortAxisFlip_checkBox.isChecked()
        
        mode_val = 0x00
        if is_h_checked:
            mode_val |= 0x01  # 把 Bit 0 設為 1 (加 1)
        if is_v_checked:
            mode_val |= 0x02  # 把 Bit 1 設為 1 (加 2)
            
        print(f"🔄 翻轉狀態改變: 水平={is_h_checked}, 垂直={is_v_checked} -> 發送指令: 0x{mode_val:02X}")
        # 4. 直接呼叫你的硬體大腦 (發送 0x18 指令)
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


    def find_dlp_screen(self):
        """掃描系統中所有的螢幕，尋找解析度剛好是 1152x576 的那一個"""
        screens = QApplication.screens()
        for screen in screens:
            geom = screen.geometry()
            # 利用解析度特徵來鎖定硬體
            if geom.width() == 1152 and geom.height() == 576:
                return screen
        
        # 如果找了一圈都沒找到，回傳 None
        return None

    # ==========================================
    # 🚀 一鍵投影執行流程
    # ==========================================
    def start_auto_projection(self):
        # 1. 自動偵測螢幕
        dlp_screen = self.find_dlp_screen()

        # 2. 防呆：如果沒接線，或是解析度跑掉
        if dlp_screen is None:
            print("❌ 找不到 1152x576 的投影設備！")
            QMessageBox.critical(self, "連線錯誤", "找不到 DLP 投影設備！\n請檢查 HDMI 連線，並確認 Windows 顯示設定中該螢幕解析度為 1152x576。")
            return

        print(f"✅ 成功鎖定 DLP 設備，實體座標位於: {dlp_screen.geometry()}")

        # 3. 建立並發射投影視窗
        if self.proj_window is None:
            self.proj_window = ProjectionWindow()
            
        # 🌟 直接將視窗搬到該螢幕的座標上，並強制全螢幕
        self.proj_window.setGeometry(dlp_screen.geometry())
        self.proj_window.showFullScreen()
        
        # 4. 指示投影視窗載入指定路徑的圖片 (這裡換成你的實際路徑)
        target_file_path = "D:/Desktop/DLP_customsoftware/test_pattern.png"
        self.proj_window.show_image(target_file_path)




    def closeEvent(self, event):
        """當你按下右上角 X 關閉視窗時，自動觸發這裡，安全釋放硬體"""
        print("\n🛑 關閉 GUI，安全釋放 Cheetah 設備...")
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
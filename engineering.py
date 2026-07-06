from PyQt6.QtWidgets import QWidget ,QTableWidgetItem ,QHeaderView ,QMessageBox, QFileDialog
from PyQt6.QtCore import Qt
from PyQt6 import uic
from main import DLP_function
import csv
class EngineeringWindow(QWidget): # ⚠️ 記得確認你的 .ui 是 Widget 還是 Dialog
    def __init__(self,dlp_instance):
        super().__init__()
        
        # 載入工程模式的 UI 檔案
        uic.loadUi("EngineeringWindow (3).ui", self)
        self.tableWidget.setRowCount(0)
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents) # 均分寬度
        self.tableWidget.horizontalHeader().setStretchLastSection(True)
        # 設定視窗屬性
        self.setWindowTitle("工程模式控制台 (高權限)")
        self.setWindowFlags(Qt.WindowType.Window)
        self.dlp = dlp_instance

        self.dac_R_value = 4095
        self.dac_G_value = 4095
        self.dac_B_value = 4095
        self.limit_R_value = 1023
        self.limit_G_value = 1023
        self.limit_B_value = 1023
        self.blank_R_value = 0
        self.blank_G_value = 0
        self.blank_B_value = 0
        self.feedback_val = 0
        self.cmode_val = 0
        self.real_hex_cmd = 0x00

        self.illumination_bin_select_map = {
            0: 0x00, 
            1: 0x01,
            2: 0x02,
            3: 0x03,
            4: 0x04,
            5: 0x05,
            6: 0x06, 
            7: 0x07,
            8: 0x08,
            9: 0x09,
            10: 0x0A,
            11: 0x0B,
        }

        self.operating_mode_select_map = {
            0: 0x00, 
            1: 0x01,
            2: 0x02,
        }
        
        # 如果工程模式裡面有按鈕，可以在這裡綁定
        self.setup_eng_connections()

    def setup_eng_connections(self):
        
        
        self.illumination_bin_select.currentIndexChanged.connect(lambda index: self.on_illumination_bin_select(index))
        self.operating_mode_select.currentIndexChanged.connect(lambda index: self.on_operating_mode_select(index))

        self.daclevels_R.valueChanged.connect(self.on_daclevels_SpinBox)
        self.daclevels_G.valueChanged.connect(self.on_daclevels_SpinBox)
        self.daclevels_B.valueChanged.connect(self.on_daclevels_SpinBox)


        self.daclimits_R.valueChanged.connect(self.on_daclimits_SpinBox)
        self.daclimits_G.valueChanged.connect(self.on_daclimits_SpinBox)
        self.daclimits_B.valueChanged.connect(self.on_daclimits_SpinBox)

        self.dacblanks_R.valueChanged.connect(self.on_dacblanks_SpinBox)
        self.dacblanks_G.valueChanged.connect(self.on_dacblanks_SpinBox)
        self.dacblanks_B.valueChanged.connect(self.on_dacblanks_SpinBox)


        self.drive_mode_feedback.stateChanged.connect(self.on_tps99000_Q1_drive_mode)
        self.drive_mode_CMODE.stateChanged.connect(self.on_tps99000_Q1_drive_mode)

        self.btn_record.clicked.connect(self.add_record_to_table)
        self.btn_delete.clicked.connect(self.delete_selected_row)
        self.btn_send.clicked.connect(self.send_command)

        self.dimmingSlider.valueChanged.connect(self.sync_record_to_ui)

        self.btn_save.clicked.connect(self.save_table_data)
        self.btn_import.clicked.connect(self.import_table_data)


    def on_illumination_bin_select(self , index):
        self.real_hex_cmd = self.illumination_bin_select_map.get(index)
        self.dlp.illumination_bin_select(self.real_hex_cmd)    
        
    def on_operating_mode_select(self , index):
        self.real_hex_cmd = self.operating_mode_select_map.get(index)
        self.dlp.operating_mode(self.real_hex_cmd)


    def on_daclevels_SpinBox(self, *args):
        self.dac_R_value = self.daclevels_R.value()
        self.dac_G_value = self.daclevels_G.value()
        self.dac_B_value = self.daclevels_B.value()
        self.dlp.rgb_dac_levels(0x00,self.dac_R_value,self.dac_G_value,self.dac_B_value)

    def on_daclimits_SpinBox(self, *args):
        self.limit_R_value = self.daclimits_R.value()
        self.limit_G_value = self.daclimits_G.value()
        self.limit_B_value = self.daclimits_B.value()
        self.dlp.rgb_limits(self.limit_R_value,self.limit_G_value,self.limit_B_value)  

    def on_dacblanks_SpinBox(self, *args):
        self.blank_R_value = self.dacblanks_R.value()
        self.blank_G_value = self.dacblanks_G.value()
        self.blank_B_value = self.dacblanks_B.value()
        self.dlp.blanking_levels(self.blank_R_value,self.blank_G_value,self.blank_B_value)

    def on_tps99000_Q1_drive_mode(self, *args):
        self.feedback_val = self.drive_mode_feedback.isChecked()
        self.cmode_val = self.drive_mode_CMODE.isChecked()
        self.dlp.tps99000_Q1_drive_mode(self.feedback_val, self.cmode_val)

    def send_command(self):
        self.dlp.illumination_bin_select(self.real_hex_cmd) 
        self.dlp.rgb_dac_levels(0x00,self.dac_R_value,self.dac_G_value,self.dac_B_value)
        self.dlp.rgb_limits(self.limit_R_value,self.limit_G_value,self.limit_B_value)
        self.dlp.blanking_levels(self.blank_R_value,self.blank_G_value,self.blank_B_value)
        self.dlp.tps99000_Q1_drive_mode(self.feedback_val, self.cmode_val)




    def add_record_to_table(self):
        """抓取目前畫面上所有的參數，並新增一行到表格中"""
        
        # ------------------------------------------------
        # 1. 抓取所有上面元件的目前數值 (請依照你實際的 objectName 修改)
        # ------------------------------------------------
        
        # A(分階): 通常是看現在有幾行，就當作第幾階 (0, 1, 2...)
        step_index = str(self.tableWidget.rowCount())
        
        # B(流明): 圖片裡沒看到輸入框，通常是外接輝度計，這裡先留空
        lumens_val = "" 
        
        # C(CM/DM): 假設你用的是一個紀錄狀態的變數，或是 CheckBox
        # 這裡用假字串示範，你可以替換成 self.drive_mode_CMODE 轉換的字串
        is_cmode = self.drive_mode_CMODE.isChecked()
        is_feedback = self.drive_mode_feedback.isChecked()

        cmdm_val = "1" if is_cmode else "0"
        feedback_val = "1" if is_feedback else "0"

        # D(DAC) & E(Limit): 假設是從 Label 或某些變數抓取
        dac_val = f"{self.dac_R_value}, {self.dac_G_value}, {self.dac_B_value}"
        limit_val = f"{self.limit_R_value}, {self.limit_G_value}, {self.limit_B_value}"
        blank_val = f"{self.blank_R_value}, {self.blank_G_value}, {self.blank_B_value}"
        driver_val = f"{feedback_val}, {cmdm_val}"
        duty_val = self.illumination_bin_select.currentText() 
        
        # G(Dimming): 圖片說是輸入框，抓取 value() 並轉成字串
        #dimming_val = str(self.input_dimming.value()) 

        # ------------------------------------------------
        # 2. 在表格最後面「新增一列 (Row)」
        # ------------------------------------------------
        current_row_count = self.tableWidget.rowCount()
        self.tableWidget.insertRow(current_row_count)

        # ------------------------------------------------
        # 3. 把資料一格一格填入 (Column 0 ~ 6)
        # ------------------------------------------------
        # 語法：setItem(第幾列, 第幾欄, QTableWidgetItem("文字"))
        row_data = [
            step_index, 
            lumens_val, 
            driver_val, 
            dac_val, 
            limit_val, 
            blank_val, 
            duty_val,
            #dimming_val
        ]
        
        # 🌟 用迴圈一次跑完 7 個欄位
        for col_index, text_val in enumerate(row_data):
            item = QTableWidgetItem(text_val)
            # 設定文字對齊方式：水平置中 + 垂直置中
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter) 
            self.tableWidget.setItem(current_row_count, col_index, item)
        
        # ------------------------------------------------
        # 4. 貼心 UX：讓表格自動捲動到最下面，方便查看最新紀錄
        # ------------------------------------------------
        self.tableWidget.scrollToBottom()
        self.update_slider_range()
        
        print(f"✅ 已紀錄第 {step_index} 階資料！")

    def delete_selected_row(self):
        """刪除使用者目前用滑鼠點選的那一列"""
        # 取得目前選取的行號 (如果是 -1 代表沒有選取任何東西)
        current_row = self.tableWidget.currentRow() 
        
        if current_row >= 0:
            # 執行刪除
            self.tableWidget.removeRow(current_row)
            print(f"🗑️ 已刪除第 {current_row} 列資料")
            
            # 🌟 刪除後，重新整理 A(分階) 的序號，確保它永遠是 0, 1, 2, 3...
            self.renumber_steps()
        else:
            # 防呆：如果沒點選半個格子就按刪除，跳出警告
            QMessageBox.warning(self, "提示", "請先用滑鼠點選要刪除的資料列！")

    def renumber_steps(self):
        """重新編排表格第 0 欄的 A(分階) 序號"""
        # 跑一個迴圈，把每一列的第 0 欄重新寫入正確的數字
        for row in range(self.tableWidget.rowCount()):
            self.tableWidget.setItem(row, 0, QTableWidgetItem(str(row)))
        self.update_slider_range()

    def update_slider_range(self):
        """根據表格目前的資料筆數，自動調整 Slider 的最大值"""
        row_count = self.tableWidget.rowCount()
        
        if row_count == 0:
            self.dimmingSlider.setMaximum(0)
            self.dimmingSlider.setEnabled(False) # 沒資料時先反灰禁用
        else:
            self.dimmingSlider.setEnabled(True)
            # 依照你的需求：預設最少 10 階，超過就跟著表格長大
            # row_count - 1 是因為索引是從 0 開始
            dynamic_max = max(7, row_count - 1) 
            self.dimmingSlider.setMaximum(dynamic_max)

    def sync_record_to_ui(self, index):
        """當 Slider 拖動時，抓取對應階層的資料並套用到 UI 與硬體"""
        
        # 防呆：如果拉到的階層超過目前表格真實有的資料（例如表格只有 5 筆，但 slider 刻度在 8）
        if index >= self.tableWidget.rowCount():
            return
            
        print(f"⏪ 正在同步回放第 {index} 階的參數...")

        # ------------------------------------------------
        # 1. 從表格抓取字串，並拆解回數字 (以 DAC Levels 為例)
        # ------------------------------------------------

        driver_str = self.tableWidget.item(index, 2).text()
        feedback_val, cmode_val = map(int, driver_str.replace(" ", "").split(","))
        feedback_int, cmode_int = int(feedback_val), int(cmode_val)
        self.dlp.tps99000_Q1_drive_mode(feedback_int,cmode_int) 


        dac_str = self.tableWidget.item(index, 3).text()        
        r_val, g_val, b_val = map(int, dac_str.replace(" ", "").split(","))
        self.dlp.rgb_dac_levels(0x00,r_val,g_val,b_val)
        

        limit_str = self.tableWidget.item(index, 4).text()
        lr, lg, lb = map(int, limit_str.replace(" ", "").split(","))
        self.dlp.rgb_limits(lr, lg, lb)
        
        blank_str = self.tableWidget.item(index, 5).text()
        br, bg, bb = map(int, blank_str.replace(" ", "").split(","))
        self.dlp.blanking_levels(br, bg, bb)

        duty_str = self.tableWidget.item(index, 6).text()
        combo_index = self.illumination_bin_select.findText(duty_str)
        real_hex_cmd = self.illumination_bin_select_map.get(combo_index)
        self.dlp.illumination_bin_select(real_hex_cmd) 

        

    def save_table_data(self):
        """將目前 QTableWidget 裡的資料儲存至 CSV 檔案"""
        row_count = self.tableWidget.rowCount()
        col_count = self.tableWidget.columnCount()

        if row_count == 0:
            QMessageBox.warning(self, "提示", "目前表格內沒有任何資料可以儲存！")
            return

        # 1. 讓使用者選擇儲存位置與檔名
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "儲存參數紀錄表", 
            "DLP_Parameter_Log.csv",  # 預設檔名
            "CSV 檔案 (*.csv);;所有檔案 (*.*)"
        )

        if not file_path:
            return  # 使用者按了取消

        try:
            # 🌟 關鍵：編碼必須用 'utf-8-sig'，用微軟 Excel 打開中文與特殊符號才不會亂碼！
            with open(file_path, mode="w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)

                # 2. 抓取標題欄 (Header) 並寫入第一行
                headers = []
                for col in range(col_count):
                    header_item = self.tableWidget.horizontalHeaderItem(col)
                    headers.append(header_item.text() if header_item else f"Col_{col}")
                writer.writerow(headers)

                # 3. 逐列抓取表格內容並寫入
                for row in range(row_count):
                    row_data = []
                    for col in range(col_count):
                        item = self.tableWidget.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)

            QMessageBox.information(self, "成功", f"表格資料已成功儲存至：\n{file_path}")
            print(f"💾 表格已儲存: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"儲存檔案時發生錯誤：\n{str(e)}")

    # ==========================================
    # 📂 匯入表格功能 (從 CSV 載入資料並重建 UI)
    # ==========================================
    def import_table_data(self):
        """從 CSV 讀取資料並填回 QTableWidget"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "選擇要匯入的參數紀錄表", 
            "", 
            "CSV 檔案 (*.csv);;所有檔案 (*.*)"
        )

        if not file_path:
            return

        try:
            with open(file_path, mode="r", encoding="utf-8-sig") as file:
                reader = csv.reader(file)
                rows = list(reader)

            if len(rows) <= 1:
                QMessageBox.warning(self, "警告", "選取的檔案為空，或只有標題列！")
                return

            # 1. 清空目前表格所有舊資料
            self.tableWidget.setRowCount(0)

            # 2. 從第二列開始讀取 (跳過第一列的 Header)
            data_rows = rows[1:]

            # 🌟 專業防護：在大量填入資料時，先暫時關閉表格的重繪與 Slider 連動，提升效能防當機
            self.tableWidget.blockSignals(True)

            for row_index, row_data in enumerate(data_rows):
                self.tableWidget.insertRow(row_index)
                
                # 將每一欄的資料塞入表格
                for col_index, text_val in enumerate(row_data):
                    # 避免 CSV 的欄位數超過我們表格現有的欄位數
                    if col_index < self.tableWidget.columnCount():
                        item = QTableWidgetItem(str(text_val))
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)  # 維持置中對齊
                        self.tableWidget.setItem(row_index, col_index, item)

            self.tableWidget.blockSignals(False)

            # 3. 🌟 匯入完成後，自動更新 Slider 的上限，並捲動到最上面
            self.update_slider_range()
            self.tableWidget.scrollToTop()

            QMessageBox.information(self, "成功", f"成功匯入 {len(data_rows)} 筆測試參數！")
            print(f"📂 成功匯入檔案: {file_path}")

        except Exception as e:
            self.tableWidget.blockSignals(False)
            QMessageBox.critical(self, "匯入失敗", f"讀取檔案失敗，請確認檔案格式正確：\n{str(e)}")
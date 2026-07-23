import cheetah_py as api
from array import array
import time
import re

class DLP_Init:
    def __init__(self):
        self.tag = 0x01
        self.x = 0x00
        self.handle = self.get_cheetah()

        if self.handle > 0:
            api.ch_spi_bitrate(self.handle, 10000)
            api.ch_spi_configure(self.handle, 0, 0, 0, 0)
            print("🟢 DLP 控制器連線成功！\n")
            # 這裡可以決定要不要開啟自動對齊 TAG
            self.resync_hardware()

    def get_cheetah(self):
        """尋找並連線未被佔用的 Cheetah"""
        num_found, ports = api.ch_find_devices(16)
        if num_found <= 0:
            print("❌ 找不到任何 Cheetah 設備")
            return -1

        for i in range(num_found):
            if not (ports[i] & api.CH_PORT_NOT_FREE):
                port_num = ports[i] & ~api.CH_PORT_NOT_FREE
                handle = api.ch_open(port_num)
                if handle > 0:
                    return handle
        print("⚠️ 設備全部被佔用中")
        return -1

    def calculate_crc(self, data_bytes):
        """計算 TI DLP 專用 CRC-8"""
        crc = 0xFF
        for b in data_bytes:
            crc ^= b
            for _ in range(8):
                if crc & 0x80:
                    crc = (crc << 1) ^ 0x07
                else:
                    crc = (crc << 1)
                crc &= 0xFF
        return crc

    def write_command(self, cmd_code, payload):
        if self.handle <= 0:
            return False

        if isinstance(payload, int):
            payload = [payload & 0xFF]

        length = len(payload)

        # ==========================================
        # 🥊 第一回合：發送主要指令
        # ==========================================
        write_tag = self.tag
        write_packet = [cmd_code, write_tag, length, *payload]
        write_crc = self.calculate_crc(write_packet)
        write_packet.append(write_crc)

        tx_write = array('B', write_packet)
        rx_write = array('B', [0] * len(tx_write))

        api.ch_spi_queue_clear(self.handle)
        api.ch_spi_queue_oe(self.handle, 1)
        api.ch_spi_queue_ss(self.handle, 0x01)
        api.ch_spi_queue_array(self.handle, tx_write)
        api.ch_spi_queue_ss(self.handle, 0x00)

        api.ch_spi_batch_shift(self.handle, rx_write)

        self.tag += 1
        if self.tag > 0xCF:
            self.tag = 0x01

        time.sleep(0.01)

        # 🌟 格式化第一回合：將 MOSI (發送) 與 MISO (接收) 轉成長條字串
        tx_write_str = " ".join([f"{x:02X}" for x in tx_write])
        rx_write_str = " ".join([f"{x:02X}" for x in rx_write])

        print(f"  └─ 📤 [發送寫入] MOSI: {tx_write_str}")
        print(f"  └─ 📥 [硬體回音] MISO: {rx_write_str[0:15]}")

        # ==========================================
        # 🥊 第二回合：輪詢 (Polling) 0xC0 直到硬體不忙碌
        # ==========================================
        retry_count = 0
        while True:
            read_tag = self.tag
            read_header = [0xC0, read_tag, 0x00]
            read_crc = self.calculate_crc(read_header)

            # 準備 9 Bytes: C0(位置) TAG(隨機碼) 00(長度) CRC + 5個0x00
            tx_read = array('B', read_header + [read_crc] + [0x00] * 5)
            # 準備接收 9 Bytes
            rx_read = array('B', [0] * 9)

            api.ch_spi_queue_clear(self.handle)
            api.ch_spi_queue_ss(self.handle, 0x01)
            api.ch_spi_queue_array(self.handle, tx_read)
            api.ch_spi_queue_ss(self.handle, 0x00)

            api.ch_spi_batch_shift(self.handle, rx_read)

            self.tag += 1
            if self.tag > 0xCF:
                self.tag = 0x01

            # 取出第 5 個 Byte (陣列 Index 4)，也就是狀態位
            status_byte = rx_read[4]
            returned_last_tag = rx_read[5]

            # 🌟 格式化第二回合：將 MOSI 與 MISO 轉成長條字串
            tx_read_str = " ".join([f"{x:02X}" for x in tx_read])
            rx_read_str = " ".join([f"{x:02X}" for x in rx_read])

            if (status_byte & 0x0F) == 0x03:
                retry_count += 1
                print(f"     ⏳ C0檢測忙碌中 [{rx_read_str}] (第 {retry_count} 次詢問)")
                time.sleep(0.05)
                continue
            else:
                # 尾數不是 3，代表硬體處理完畢
                print(f"  └─ 📥 C0已檢測完成 [{rx_read_str}]")

                if returned_last_tag == write_tag:
                    print(f"     ✅ 確認完成 cmd:{cmd_code:02X}h \n")
                break

        return True

    def read_command(self, cmd_code, read_len):

        if self.handle <= 0: return None

        header = [cmd_code, self.tag, 0x00]
        header_crc = self.calculate_crc(header)

        tx_packet = header + [header_crc] + [0x00] * (read_len + 1)
        tx_data = array('B', tx_packet)
        rx_data = array('B', [0] * len(tx_data))

        api.ch_spi_queue_clear(self.handle)
        api.ch_spi_queue_oe(self.handle, 1)
        api.ch_spi_queue_ss(self.handle, 0x01)
        api.ch_spi_queue_array(self.handle, tx_data)
        api.ch_spi_queue_ss(self.handle, 0x00)
        api.ch_spi_queue_oe(self.handle, 0)

        status, _ = api.ch_spi_batch_shift(self.handle, rx_data)

        if status > 0:
            if len(rx_data) >= (4 + read_len):
                actual_data = rx_data[4 : 4 + read_len]
                return list(actual_data)
        return None

    def resync_hardware(self):

        print("🔄 正在向硬體詢問目前的 TAG 進度...")
        self.tag = 0x01
        data = self.read_command(0xC0, 4)

        if data and len(data) >= 2:
            last_hardware_tag = data[1]
            next_tag = last_hardware_tag + 1
            if next_tag > 0xCF or next_tag < 0x01:
                next_tag = 0x01

            self.tag = next_tag
            print(f"✅ 硬體停在 0x{last_hardware_tag:02X}，將從 0x{self.tag:02X} 繼續發送。\n")
        else:
            print("⚠️ 無法讀取硬體狀態，強制從 0x01 開始。\n")
            self.tag = 0x01

    def close(self):

        if self.handle > 0:
            api.ch_close(self.handle)
            self.handle = -1
            print("🔌 Cheetah 設備已安全關閉")

class DLP_function(DLP_Init):
    def execute_batch_command_set(self, pattern_val):

        if pattern_val < 0x07:
            self.write_command(0x21, pattern_val)
            self.source_select(0x00)
            self.x = 0x00
        elif 0x07 <= pattern_val < 0x17:
            self.write_command(0x21, pattern_val)
            self.source_select(0x01)
            self.x = 0x01
        else:
            self.write_command(0x21, pattern_val)
            self.source_select(0x02)
            self.x = 0x02

    def source_select(self, source_val):

        self.write_command(0x05, source_val)

    def operating_mode(self, mode_val):

        self.write_command(0x03, mode_val)

    def rgb_dac_levels(self, x, r, g, b):

        r_lsb, r_msb = r & 0xFF, (r >> 8) & 0xFF
        g_lsb, g_msb = g & 0xFF, (g >> 8) & 0xFF
        b_lsb, b_msb = b & 0xFF, (b >> 8) & 0xFF
        payload = [x, r_lsb, r_msb, g_lsb, g_msb, b_lsb, b_msb]
        self.write_command(0x80, payload)

    def rgb_limits(self, r, g, b):

        r_lsb, r_msb = r & 0xFF, (r >> 8) & 0xFF
        g_lsb, g_msb = g & 0xFF, (g >> 8) & 0xFF
        b_lsb, b_msb = b & 0xFF, (b >> 8) & 0xFF
        payload = [r_lsb, r_msb, g_lsb, g_msb, b_lsb, b_msb]
        self.write_command(0x82, payload)

    def blanking_levels(self, r, g, b):

        r_lsb, r_msb = r & 0xFF, (r >> 8) & 0xFF
        g_lsb, g_msb = g & 0xFF, (g >> 8) & 0xFF
        b_lsb, b_msb = b & 0xFF, (b >> 8) & 0xFF
        payload = [r_lsb, r_msb, g_lsb, g_msb, b_lsb, b_msb]
        self.write_command(0x84, payload)

    def system_mode_select(self,mode_val):

        self.write_command(0x1c, mode_val)
        self.source_select(self.x) #更新需重點畫面

    def degamma_select(self,mode_val):

        self.write_command(0x54, mode_val)
        self.source_select(self.x)

    def bezel_adjustment(self,x_shift_val,y_shift_val):

        if (x_shift_val % 2 != 0) or (y_shift_val % 4 != 0):
            print("❌ 錯誤：X 偏移量必須是偶數，Y 偏移量必須是 4 的倍數！")
            return False

        if x_shift_val >=0 :
            pass #右
        else :
            x_shift_val = 0x10000 + x_shift_val #左
        if y_shift_val >=0 :
            pass #下
        else :
            y_shift_val = 0x10000 + y_shift_val        #上

        payload = [x_shift_val & 0xFF, (x_shift_val >> 8) & 0xFF, y_shift_val & 0xFF, (y_shift_val >> 8) & 0xFF]
        self.write_command(0x1F, payload)
        #self.source_select(self.x) #更新需重點畫面

    def display_image_orientation(self,mode_val):

        self.write_command(0x18, mode_val)
        self.source_select(self.x) #更新需重點畫面

    def tps99000_Q1_drive_mode(self,photo__feedback,CMODE_signal):

        payload = [photo__feedback, 0x23 ,CMODE_signal]
        self.write_command(0x92, payload)
        #self.source_select(self.x) #更新需重點畫面

    def illumination_bin_select(self,mode_val):

        self.write_command(0x70, mode_val)
        #self.source_select(self.x) #更新需重點畫面

    def dimming_level(self,dimming_level_val):
        val = dimming_level_val & 0xFF, (dimming_level_val >> 8) & 0xFF
        self.write_command(0x50, val)
        #self.source_select(self.x) #更新需重點畫面


#========================================
# 主程式 (命令列互動測試區)
# ==========================================
if __name__ == "__main__":
    dlp = DLP_function()
    dlp.operating_mode(0x02)
    dlp.execute_batch_command_set(0x0A)
    dlp.rgb_dac_levels(0,4095,4095,4095)
    dlp.rgb_limits(1023,1023,1023)
    dlp.blanking_levels(0,0,0)

    while True:
        user_input = input("DLP_CMD >>> ").strip()

        if user_input.lower() == 'q':
            break
        if not user_input:
            continue

        try:
            for method in dir(dlp):
                if not method.startswith("__") and callable(getattr(dlp, method)):
                    user_input = re.sub(rf"(?<!dlp\.)\b{method}\b", f"dlp.{method}", user_input)

            # 將使用者的字串直接轉換為 Python 程式碼執行
            exec(user_input)

        except Exception as e:
            print(f" ❌ 指令執行錯誤: {e}")
            print(" ⚠️ 請檢查語法是否正確！\n")

    dlp.close()
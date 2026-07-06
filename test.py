import re

# 1. 🌟 把你從 Excel 複製出來的所有欄位，直接貼到這對三引號中間！
# (不用管換行或空白，直接貼純文字就好)
raw_excel_dump = """
FF 02 4C 02 00 01 5F 3C 2F 50 69 6E 3E 0D 0A 3C 50 69 6E 3E 0D 0A 3C 52 65 73 65 72 76 65 64 3E 74 72 75 65 3C 2F 52 65 73 65 72 76 65 64 3E 0D 0A 3C 43 6F 6E 66 69 67 75 72 61 74 69 6F 6E 3E 54 49 20 46 75 6E 63 74 69 6F 6E 3C 2F 43 6F 6E 66 69 67 75 72 61 74 69 6F 6E 3E 0D 0A 3C 49 6E 69 74 69 61 6C 56 61 6C 75 65 3E 30 3C 2F 49 6E 69 74 69 61 6C 56 61 6C 75 65 3E 0D 0A 3C 2F 50 69 6E 3E 0D 0A 3C 50 69 6E 3E 0D 0A 3C 52 65 73 65 72 76 65 64 3E 66 61 6C 73 65 3C 2F 52 65 73 65 72 76 65 64 3E 0D 0A 3C 43 6F 6E 66 69 67 75 72 61 74 69 6F 6E 3E 49 6E 70 75 74 3C 2F 43 6F 6E 66 69 67 75 72 61 74 69 6F 6E 3E 0D 0A 3C 49 6E 69 74 69 61 6C 56 61 6C 75 65 3E 30 3C 2F 49 6E 69 74 69 61 6C 56 61 6C 75 65 3E 0D 0A 3C 2F 50 69 6E 3E 0D 0A 3C 50 69 6E 3E 0D 0A 3C 52 65 73 65 72 76 65 64 3E ED
"""

# 2. 清理字串：把換行、多餘的空白、或者是偶爾出現的 FF 同步碼去掉
# (這裡我簡單去掉空白和換行)
clean_hex = raw_excel_dump.replace("\n", "").replace(" ", "")


# 3. 轉換成 Python 認得的真實 Byte Array
try:
    binary_data = bytes.fromhex(clean_hex)

except ValueError as e:
    print("❌ 轉換失敗，請檢查裡面是不是有混到非十六進位的英文字母(如 CMD, RX 等標題)")
    exit()

# 4. 暴力翻譯成人類文字！
decoded_text = binary_data.decode('ascii', errors='ignore')



print("📜 --- 破解出的 XML 明文內容 --- 📜\n")
print(decoded_text)
print("\n-------------------------------------")

# 5. 用正規表達式抓出所有的名字 (尋找像是 name="XXX" 的標籤)
print("🔍 自動萃取下拉選單名稱：")
names = re.findall(r'name="([^"]+)"', decoded_text)


if names:
    for idx, name in enumerate(names):
        print(f"找到選項: Index {idx} -> {name}")
else:
    print("目前貼上的片段中還沒看到 name 標籤，請去 Excel 複製更多行貼進來！")
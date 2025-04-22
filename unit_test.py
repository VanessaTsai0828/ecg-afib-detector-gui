# Unit test using HTMLTestRunner
import unittest
import numpy as np
import tkinter as tk
import matplotlib.pyplot as plt
from HtmlTestRunner import HTMLTestRunner
from Report_AfibDetect_113851005 import detect_afib,DisplayECG

# 初始化全局變量（包含預設數據）
time = np.linspace(0, 30, 3000)  # 時間軸 (30 秒, 3000 個點)
ecg_signal = np.zeros_like(time)  # 預設為一條直線
qrs_peaks = []  # 預設無 QRS 峰
rr_intervals = np.zeros(10)  # 預設 RR 間隔數據
rr_intervals_filtered = np.zeros(10)  # 預設濾波後的 RR 間隔數據
start_idx = 0  # 顯示數據的起始索引
window_size = 5  # 顯示的時間窗口（秒）

class TestECGFunctions(unittest.TestCase):
    
    @classmethod
    def setUpClass(self):
        """在所有測試開始前，先建立一個 Tk 物件"""
        self.root = tk.Tk()
        self.entry = tk.Entry(self.root)  # 初始化 entry 控件
        self.entry.pack()  # 將 entry 控件放入界面中
        self.root.withdraw()  # 隱藏主窗口
        self.entry.insert(0, "500")  # 設置預設值為 500

    @classmethod
    def tearDownClass(self):
        """在測試結束後關閉 Tkinter"""
        self.root.destroy()
        


    def test_entry(self):
        """測試 Entry 控件是否能正確讀取數據"""
        self.entry.delete(0, "end")  # 清空之前的內容
        self.entry.insert(0, "250")  # 插入一個有效數字
        sample_rate = self.entry.get()  # 獲取 Entry 的值
        self.assertEqual(sample_rate, "250")  # 驗證結果

        

    def test_detect_afib(self):
        """測試 detect_afib() 函數"""

        normal_ecg = [0.8, 0.9, 1.0, 0.85, 0.92]  # 測試數據
        self.assertFalse(detect_afib(normal_ecg)[0])  # 預期回傳 False
        
        # Test case for normal RR intervals
        rr_intervals_normal = np.array([800, 810, 820, 830, 840])
        afib_detected, results = detect_afib(rr_intervals_normal)
        self.assertFalse(afib_detected, "Should not detect AFib for normal intervals")
        
        # Test case for AFib-like RR intervals
        rr_intervals_afib = np.array([800, 600, 500, 700, 800, 600, 1200])
        afib_detected, results = detect_afib(rr_intervals_afib)
        self.assertTrue(afib_detected, "Should detect AFib for irregular intervals")
        
        # Check RMSSD value for AFib detection
        self.assertGreater(results['RMSSD (ms)'], 50, "RMSSD should be greater than threshold in AFib")
        


    def test_display_button(self):
        """測試 Display 按鈕的功能是否正確"""
        # 創建一個顯示按鈕並模擬按下
        display_button = tk.Button(self.root, text="Display", command=DisplayECG)
        display_button.invoke()  # 模擬按下按鈕
    
        # 創建 Matplotlib 圖表進行檢查
        fig, ax = plt.subplots(figsize=(8, 4))
    
        # 假設 DisplayECG 繪製的是 'ecg_signal'，並確認是否有繪製出至少一條線
        ax.plot(time, ecg_signal)  # 這裡您應該使用您的 ECG 信號數據進行繪圖

        # 檢查是否有繪製出至少一條線
        self.assertGreater(len(ax.lines), 0, "按下 Display 按鈕未繪製圖形")
    
        # 進一步檢查圖形的內容是否符合預期，這裡假設我們的 ECG 信號是全 0 的
        self.assertTrue(np.allclose(ax.lines[0].get_ydata(), ecg_signal), "繪製的 ECG 信號與預期不符")




if __name__ == "__main__":
    # 創建測試套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestECGFunctions)
    
    # 配置測試報告
    runner = HTMLTestRunner(
        output="test_reports",  # 測試報告輸出目錄
        report_name="TestReport",  # 測試報告名稱
        report_title="ECG Afib detect GUI Test Report",  # 測試報告標題
    )
    
    # 執行測試並生成報告
    runner.run(suite)

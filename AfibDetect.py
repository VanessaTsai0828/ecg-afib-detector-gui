# Main GUI and AFib detection logic (threshold-based)
import tkinter as tk  # 用於建立圖形化使用者介面
from tkinter import filedialog  # 用於選擇檔案的對話框
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # 嵌入 Matplotlib 圖表到 Tkinter
import matplotlib.pyplot as plt  # 繪製圖表
import numpy as np  # 用於數值運算
import wfdb  # 用於讀取 PhysioNet 的心電圖數據
import os  # 用於檔案路徑操作

# 建立 Tkinter 主視窗
win = tk.Tk()
win.title("ECG心房顫動(AFib)偵測系統")  # 設定視窗標題
win.geometry('1050x520')  # 設定視窗大小
win.resizable(True, True)  # 允許視窗大小調整
win.config(bg='#FFF8D7')  # 設定背景顏色


# 設置表格行高
for i in range(5):
    win.grid_rowconfigure(i, minsize=60)
    
win.grid_columnconfigure(0, minsize=200)  # 設定第一列寬度


# 初始化全局變量（包含預設數據）
time = np.linspace(0, 30, 3000)  # 時間軸 (30 秒, 3000 個點)
ecg_signal = np.zeros_like(time)  # 預設為一條直線
qrs_peaks = []  # 預設無 QRS 峰
rr_intervals = np.zeros(10)  # 預設 RR 間隔數據
rr_intervals_filtered = np.zeros(10)  # 預設濾波後的 RR 間隔數據
start_idx = 0  # 顯示數據的起始索引
window_size = 5  # 顯示的時間窗口（秒）
sample_rate = 500


def plot_ecg_with_slider():
    """
    繪製 ECG 信號和 RR 間隔圖表，並嵌入到 Tkinter 視窗中。
    """
    global time, ecg_signal, qrs_peaks, rr_intervals, rr_intervals_filtered, start_idx
    
    try:
        sample_rate = float(entry.get())
        print(f"輸入的採樣率是: {sample_rate}")
    except ValueError:
        print("無效的 sample rate，請輸入數字!")
    

    # 計算顯示範圍
    end_idx = min(start_idx + int(window_size * sample_rate), len(ecg_signal))

    
    # 建立 Matplotlib 圖表
    fig, axs = plt.subplots(2, 1, figsize=(8, 4), sharex=True)

    # 圖1: ECG 信號
    axs[0].plot(time[start_idx:end_idx], ecg_signal[start_idx:end_idx], label="ECG Data")
    visible_peaks = [p for p in qrs_peaks if start_idx <= p < end_idx]
    
    if visible_peaks:
        axs[0].scatter(time[visible_peaks], ecg_signal[visible_peaks], color='red', marker='x', label="QRS Peaks")
        
    axs[0].set_title(f"ECG Signal (Sample Rate: {sample_rate} Hz)")
    axs[0].set_ylabel("Amplitude")
    axs[0].legend()

    # 圖2: RR 間隔
    if len(rr_intervals) > 0:
        axs[1].plot(np.cumsum(rr_intervals) / 1000, rr_intervals, label="RRI", color="blue")
        
    if len(rr_intervals_filtered) > 0:
        axs[1].plot(np.cumsum(rr_intervals_filtered) / 1000, rr_intervals_filtered, label="RRI filter", color="orange")
    
    axs[1].set_title("RR Intervals")
    axs[1].set_xlabel("Time (s)")
    axs[1].set_ylabel("RRI (ms)")
    axs[1].legend()

    # 設定 x 軸範圍
    axs[0].set_xlim(time[start_idx], time[end_idx - 1])
    plt.tight_layout()

    # 將圖表嵌入 Tkinter 視窗
    canvas = FigureCanvasTkAgg(fig, master=win)
    canvas.draw()

    # 使用 place() 方法來設置 canvas 的位置和大小
    canvas.get_tk_widget().place(x=200, y=50, width=800, height=400)



def update_start_idx(val):
    global start_idx
    start_idx = int(float(val))
    start_idx = max(0, min(start_idx, len(ecg_signal) - int(window_size * sample_rate)))  # 確保索引不超範圍
    plot_ecg_with_slider()


def LoadECGFile(filename=None):
    """
    加載 ECG 檔案，並更新數據到全局變量。
    """
    global time, ecg_signal, qrs_peaks, rr_intervals, rr_intervals_filtered, slider

    if filename is None:  # 如果沒有提供 filename，就打開檔案選擇視窗
        filename = filedialog.askopenfilename(title="選擇檔案", filetypes=[("PhysioNet Data Files", "*.dat")])

    if not filename:
        print("未選擇檔案")
        return

    reset_plot()

    try:
        sample_rate = float(entry.get())  # 獲取採樣率
    except ValueError:
        print("無效的 sample rate，請輸入數字!")
        return

    try:
        record_name = filename.rsplit('.', 1)[0]
        if not os.path.exists(record_name + '.dat') or not os.path.exists(record_name + '.hea'):
            print("相關文件 (.dat 或 .hea) 未找到。")
            return

        # 使用 wfdb 讀取數據
        record = wfdb.rdrecord(record_name)
        annotation = wfdb.rdann(record_name, 'qrs')
        ecg_signal = record.p_signal[:, 0]
        time = np.arange(len(ecg_signal)) / sample_rate
        qrs_peaks = annotation.sample

        if len(qrs_peaks) >= 2:
            rr_intervals = np.diff(qrs_peaks) * (1 / sample_rate) * 1000
            rr_intervals_filtered = np.convolve(rr_intervals, np.ones(3) / 3, mode='same')

        # 初始化滑桿範圍
        slider.config(from_=0, to=len(ecg_signal) - int(window_size * sample_rate), resolution=int(sample_rate))
        plot_ecg_with_slider()

        # 更新 filename 標籤的文本為文件名稱
        filename_label.config(text=os.path.basename(filename))
        print("文件加載成功！")
    except Exception as e:
        print("加載文件時出錯", e)


# 檢測心房顫動的函數
def detect_afib(rr_intervals):
    """
    基於 RR 間隔數據檢測心房顫動。
    :param rr_intervals: RR 間隔數據（單位：ms）
    :return: 布爾值表示是否檢測到 AFib，及相關指標
    """
    if len(rr_intervals) < 2:
        print("RR 間隔數據不足，無法檢測 AFib")
        return False, {}

    # 計算指標
    rr_mean = np.mean(rr_intervals)  # RR 平均值
    rr_std = np.std(rr_intervals)  # RR 標準差
    rr_diff = np.diff(rr_intervals)  # RR 間隔的差分
    rmssd = np.sqrt(np.mean(rr_diff ** 2))  # RMSSD 指標
    pnn50 = np.sum(np.abs(rr_diff) > 50) / len(rr_diff) * 100  # PNN50 指標
    cvrr = rr_std / rr_mean  # CVRR 指標

    # 判斷是否可能存在 AFib 的閾值
    afib_threshold_rmssd = 50  # RMSSD > 50 ms
    afib_threshold_pnn50 = 20  # PNN50 > 20%
    afib_threshold_cvrr = 0.1  # CVRR > 0.1

    # 是否檢測到 AFib
    afib_detected = (
        rmssd > afib_threshold_rmssd or
        pnn50 > afib_threshold_pnn50 or
        cvrr > afib_threshold_cvrr
    )

    # 返回結果和指標
    results = {
        "RR Mean (ms)": rr_mean,
        "RR Std (ms)": rr_std,
        "RMSSD (ms)": rmssd,
        "PNN50 (%)": pnn50,
        "CVRR": cvrr,
        "AFib Detected": afib_detected
    }

    return afib_detected, results


# GUI 中檢測心房顫動的功能
def DetectAfib():
    """
    使用 RR 間隔數據檢測 AFib，並將結果顯示在介面上。
    """
    global rr_intervals, result_labels

    if len(rr_intervals) < 2:
        print("RR 間隔數據不足，無法檢測 AFib")
        return

    # 調用 AFib 檢測函數
    afib_detected, results = detect_afib(rr_intervals)

    # 將結果更新到 GUI
    result_values = [
        f"{results['RR Mean (ms)']:.2f}",
        f"{results['RR Std (ms)']:.2f}",
        f"{results['RMSSD (ms)']:.2f}",
        f"{results['PNN50 (%)']:.2f}",
        f"{results['CVRR']:.2f}",
        "Yes" if afib_detected else "No"
    ]

    for i, value in enumerate(result_values):
        result_labels[i].config(text=value)  # 更新對應 Label 的內容

    # 根據 AFib 檢測結果設定背景顏色
    if afib_detected:
        result_labels[5].config(bg='#FF7575')  # 紅色背景表示 AFib 檢測
    else:
        result_labels[5].config(bg='#A6FFA6')  # 綠色背景表示正常


def reset_plot():
    global ecg_signal, qrs_peaks, rr_intervals, rr_intervals_filtered, time, start_idx

    # 清除文件相關資訊
    if filename_label and hasattr(filename_label, "config"):
        filename_label.config(text='N/A')  # 使用傳入的 Label 更新文本

    # 清除結果顯示
    if result_labels and isinstance(result_labels, list):
        for i, label in enumerate(result_labels):
            if label and hasattr(label, "config"):
                label.config(text='N/A')  # 更新對應 Label 的內容
                if i == 5:  # 第 6 個 Label 恢復背景顏色
                    label.config(bg='#FFF8D7')

    # 清除圖表顯示
    ecg_signal = np.zeros_like(time)  # 重置 ECG 信號為空的數據
    qrs_peaks = []  # 清除 QRS 峰
    rr_intervals = np.zeros(10)  # 重置 RR 間隔數據
    rr_intervals_filtered = np.zeros(10)  # 重置濾波後的 RR 間隔數據
    start_idx = 0  # 重置顯示的起始索引

    # 重置採樣率輸入框
    if "entry_value" in globals() and isinstance(entry_value, tk.StringVar):
        entry_value.set("500")  # 恢復預設值為 500

    # 重新繪製清空後的圖表
    plot_ecg_with_slider()
    
    slider.set(0)  # 重置滑桿的值
    


        
        
# 顯示 ECG 圖表的按鈕功能
def DisplayECG():
    """
    確保數據已加載，然後調用繪圖函數。
    """
    if ecg_signal is None or time is None:
        print("請先加載數據！")
        return
    plot_ecg_with_slider()



            

# 新增滑桿，用於控制顯示的數據範圍
slider = tk.Scale(win, from_=0, to=100, orient="horizontal",length=795,
                  command=update_start_idx,tickinterval=0)
slider.config(from_=0, to=len(ecg_signal) - 1, resolution=1)
slider.place(x=200, y=450)
slider.set(0)  # 設定滑桿初始值為 0




#UI

# 建立按鈕，用於加載 ECG 檔案
btn_Loadfile = tk.Button(win, text="Load ECG File", command=LoadECGFile, font=("Arial", 12), width=15,bg="#FFDCB9")
btn_Loadfile.grid(row=0, column=0, columnspan=1, padx=10, pady=10, sticky=tk.W)


# Frame 讓佈局更靈活
frame = tk.Frame(win, bg="#FFF8D7")
frame.grid(row=1, column=0, columnspan=1, padx=10, pady=10, sticky=tk.W)

# 標籤和輸入框放在同一格
tk.Label(frame, text='Sample Rate：', bg='#FFF8D7', fg='black', font="Arial 12", 
         anchor="w", justify="left").pack(side=tk.TOP, fill=tk.X, pady=(0, 5))

entry_value = tk.StringVar(value="500")  # 預設採樣率為 500 Hz
entry = tk.Entry(
    frame, textvariable=entry_value, width=15, 
    font=("Arial", 12), fg="#000000", bg="#FFFFFF")
entry.pack(side=tk.TOP)


# 建立按鈕，用於顯示 ECG 圖表
btn_Display = tk.Button(win, text="Display ECG", command=DisplayECG, font=("Arial", 12), width=15,bg="#FFDCB9")
btn_Display.grid(row=2, column=0, columnspan=1, padx=10, pady=10, sticky=tk.W)


# 建立按鈕，用於檢測 AFib
btn_Detect = tk.Button(win, text="Detect Afib", command=DetectAfib, font=("Arial", 12), width=15,bg="#FFDCB9")
btn_Detect.grid(row=3, column=0, columnspan=1, padx=10, pady=10, sticky=tk.W)


# 建立 Frame 並放在合併儲存格位置 
frame = tk.Frame(win, bg="#FFF8D7")
frame.grid(row=4, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)

# 標題和結果
titles = [
    "RR Mean (ms):", "RR Std (ms):", "RMSSD (ms):",
    "PNN50 (%):", "CVRR:", "AFib Detected:"
]
result_labels = []

for title in titles:
    # 每組標題和結果
    sub_frame = tk.Frame(frame, bg="#FFF8D7")
    sub_frame.pack(fill=tk.X, pady=2, anchor="w")

    tk.Label(
        sub_frame, text=title, bg='#FFF8D7', fg='black',
        font="Calibri 12"
    ).pack(side=tk.LEFT, padx=(0, 10))

    result_label = tk.Label(
        sub_frame, text="N/A", bg='#FFF8D7', fg='black',
        font="Calibri 12"
    )
    result_label.pack(side=tk.LEFT)
    result_labels.append(result_label)
    


# 建立按鈕，用於重設，並放在 frame 中
btn_reset = tk.Button(win, text="Reset", command=reset_plot, font=("Arial", 12), width=15,bg="#FFDCB9")
btn_reset.grid(row=5, column=0, columnspan=1, padx=10, pady=10, sticky=tk.W)



# Frame 讓佈局更靈活
frame = tk.Frame(win, bg="#FFF8D7")
frame.grid(row=0, column=1, columnspan=1, padx=0, pady=0, sticky=tk.W)

# 標籤和輸入框放在同一格
tk.Label(frame, text='File Name:', bg='#FFF8D7', fg='black', font="Arial 12", anchor="w",
    justify="left").grid(row=0, column=0, sticky=tk.W)

# 固定寬度的 Label
filename_label = tk.Label(frame, text='N/A', bg='#FFF8D7', fg='black', font="Arial 12", 
                    anchor="w", justify="left", width=60)
filename_label.grid(row=0, column=1,padx=10, sticky=tk.W)



# 預設繪圖
plot_ecg_with_slider()

# 主程序循環
win.mainloop()




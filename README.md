# 🫀 ECG Afib Detector GUI

A Python-based GUI application to visualize ECG signals and detect atrial fibrillation (AFib) using threshold-based RR interval analysis.

## 🧠 Features
- Tkinter GUI with ECG waveform viewer
- RR interval analysis (RMSSD, PNN50, CVRR)
- Basic QRS detection
- Unit testing with HTMLTestRunner
- Ready for AI model expansion

## ⚡ Quick Start
```
pip install -r requirements.txt
python Report_AfibDetect.py
```

## 📌 Future
Machine Learning version planned in `ml_model.py`

## 🖥️ System Interface Preview
Below is the GUI interface of the atrial fibrillation (AFib) detection system.

- The top panel displays the ECG signal along with detected QRS peaks
- The bottom panel shows RR intervals (RRI) and a smoothed curve
- The sidebar calculates HRV parameters (RMSSD / PNN50 / CVRR) in real time and displays the detection result


![image](https://github.com/user-attachments/assets/7bfe1d17-7e39-40a6-a2dc-edaf90992669)
▲ After the user loads an ECG file, AFib detection can be initiated with one click.
The system performs a preliminary judgment based on HRV parameters and provides a result indication.

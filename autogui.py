import pyautogui
import time

print("请将鼠标移动到目标位置，5秒后开始检测...")
time.sleep(5)  # 给你时间将鼠标移动到目标位置

while True:
    x, y = pyautogui.position()  # 获取鼠标当前位置
    print(f"鼠标当前位置: x={x}, y={y}", end="\r")  # 实时显示坐标
    time.sleep(0.1)  # 每0.1秒刷新一次


# 文件助手 x 1080 y 1040 发送 x 1190 y 1135
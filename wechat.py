import pyautogui
import time
import pyperclip  # 用于更可靠的文本输入

def send_file_via_wechat(file_path):
    # 1. 打开微信（确保已登录）
    print("正在尝试打开微信...")
    pyautogui.hotkey('ctrl', 'alt', 'w')  # 假设微信快捷键是 Ctrl+Alt+W
    time.sleep(2)  # 等待微信窗口完全打开
    print("微信已打开。")

    # 2. 搜索 "文件传输助手"
    print("正在搜索 '文件传输助手'...")
    pyautogui.hotkey('ctrl', 'f')  # 打开搜索框
    time.sleep(1)  # 等待搜索框出现

    # 使用 pyperclip 复制文本并检查是否成功
    search_text = "薛俊智"
    pyperclip.copy(search_text)
    if pyperclip.paste() == search_text:
        print(f"成功将 '{search_text}' 复制到剪贴板。")
    else:
        print(f"复制到剪贴板失败，当前剪贴板内容为: {pyperclip.paste()}")
        return  # 如果复制失败，终止程序

    pyautogui.hotkey('ctrl', 'v')  # 粘贴内容
    time.sleep(0.5)
    pyautogui.press('enter')  # 确认选择
    time.sleep(1)
    print("'文件传输助手' 已打开。")

    # 3. 发送文件
    print("正在准备发送文件...")
    pyautogui.click(x=1080, y=1040)  # 点击文件按钮
    time.sleep(1)

    # 复制文件路径并检查是否成功
    pyperclip.copy(file_path)
    if pyperclip.paste() == file_path:
        print(f"成功将文件路径 '{file_path}' 复制到剪贴板。")
    else:
        print(f"复制文件路径失败，当前剪贴板内容为: {pyperclip.paste()}")
        return  # 如果复制失败，终止程序

    pyautogui.hotkey('ctrl', 'v')  # 粘贴文件路径
    time.sleep(0.5)
    pyautogui.press('enter')  # 确认发送
    time.sleep(2)
    print(f"文件 '{file_path}' 已发送。")

    pyautogui.press('enter')  # 确认发送

    time.sleep(0.5)

    pyautogui.click(x=1190, y=1135)  # 点击发送按钮
    # 4. 关闭微信
    print("正在关闭微信...")
    # pyautogui.hotkey('ctrl', 'alt', 'w')  # 假设快捷键可以关闭微信
    print("微信已关闭。")

# 使用示例
send_file_via_wechat("version.txt")
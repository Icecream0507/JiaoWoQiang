import sys
import time
import pytesseract
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QHBoxLayout
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import pyautogui
import pyperclip

pytesseract.pytesseract.tesseract_cmd = r'D:\Application\Tesseract-ocr\tesseract.exe'  # 直接指定路径


# --- 账户信息加载 ---
# 尝试从 account.txt 文件中读取学号和密码。
# 如果文件不存在或格式不正确，则使用占位符，并打印警告。
try:
    with open("account.txt", "r", encoding="utf-8") as f:
        lines = f.readlines()
        jaccount = lines[0].split("=")[1].strip()  # 学号
        mima = lines[1].split("=")[1].strip()      # 密码
except FileNotFoundError:
    jaccount = "your_account" # 替换为你的学号
    mima = "your_password"   # 替换为你的密码
    print("警告: account.txt 文件未找到。请创建该文件并按 'jaccount=你的学号' 和 'mima=你的密码' 格式填写。")
except IndexError:
    jaccount = "your_account" # 替换为你的学号
    mima = "your_password"   # 替换为你的密码
    print("警告: account.txt 文件格式不正确。请确保每行包含 'key=value' 格式。")

# 设置等待时间间隔，用于Selenium操作后的短暂暂停
time_to_sleep = 0.5
# 定义预约页面的URL，以便在需要时返回
BOOKING_URL = "https://sports.sjtu.edu.cn/pc#/"

class BookingThread(QThread):
    """
    负责执行健身房场馆预约逻辑的独立线程。
    它会持续扫描可用场地并在找到时尝试预订。
    """
    log_signal = pyqtSignal(str)      # 用于向UI发送日志消息的信号
    success_signal = pyqtSignal(str)  # 用于在成功预订后发送消息的信号

    def __init__(self, start_time, end_time, loop_time=15.00):
        super().__init__()
        self.start_time = start_time
        self.end_time = end_time
        self.loop_time = loop_time  # 扫描间隔时间（分钟）

        self.running = True    # 控制线程运行状态的标志
        self.browser = None    # Selenium WebDriver实例，用于在停止时关闭

    def stop(self):
        """
        设置停止标志为False，并尝试关闭浏览器实例。
        """
        self.running = False
        # 尝试关闭浏览器，确保没有残留的WebDriver进程
        if self.browser:
            try:
                self.browser.quit()
                self.log("浏览器已关闭。")
            except WebDriverException as e:
                self.log(f"关闭浏览器时发生错误: {e}")
            self.browser = None # 清除浏览器引用

    def send_wechat_message(self, file_path):
        """
        通过模拟键盘和鼠标操作，将截图发送到微信。
        注意: 此功能依赖于微信客户端的UI布局和快捷键，可能不稳定。
        """
        try:
            self.log("尝试通过微信发送截图...")
            # 1. 打开微信 (Ctrl+Alt+W 是微信默认快捷键)
            pyautogui.hotkey('ctrl', 'alt', 'w')
            time.sleep(2)

            # 2. 搜索指定联系人 (这里是 "薛俊智"，建议将其配置化)
            pyautogui.hotkey('ctrl', 'f')
            time.sleep(1)

            search_text = "薛俊智" # 可以考虑将此设置为可配置项
            pyperclip.copy(search_text)
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(1)

            # 3. 点击文件按钮并发送文件
            # 这些坐标 (x=1080, y=1040, x=1190, y=1135) 是高度依赖于屏幕分辨率和微信UI的，非常脆弱。
            # 在不同环境下可能需要调整。
            pyautogui.click(x=1080, y=1040)  # 点击文件按钮 (可能需要根据你的屏幕调整)
            time.sleep(1)

            pyperclip.copy(file_path)
            time.sleep(0.5)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)
            pyautogui.press('enter')
            time.sleep(2)

            pyautogui.press('enter') # 确认发送文件对话框
            time.sleep(0.5)
            pyautogui.click(x=1190, y=1135)  # 点击发送按钮 (可能需要根据你的屏幕调整)
            self.log("微信发送截图成功!")

            # 提取日期和时间段信息，用于生成消息
            meg = file_path.replace(".png", "")
            split_meg = meg.split("-")
            date_str = f"{split_meg[0]}-{split_meg[1]}-{split_meg[2]}"
            time_slot = int(split_meg[3])

            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            day_of_week = date_obj.weekday() # 0=星期一, 6=星期日

            weekday_map = {
                0: "星期一", 1: "星期二", 2: "星期三", 3: "星期四",
                4: "星期五", 5: "星期六", 6: "星期日"
            }
            send_message = f"健身房预约成功！{weekday_map[day_of_week]}, {time_slot}-{time_slot + 1} "
            pyperclip.copy(send_message)
            pyautogui.hotkey('ctrl', 'v')
            pyautogui.press('enter')
            time.sleep(0.1)

        except Exception as e:
            self.log(f"微信发送失败: {e}")


    def clean_captcha_text(self, text):
        for char in text:
            if char.isalpha():
                continue
            text = text.replace(char, "")
        return text.strip()
    


    def run(self):
        """
        线程的主执行函数，包含Selenium自动化预约流程。
        增加自动恢复机制，在Timeout时重新启动流程。
        """
        max_retries = 3  # 最大重试次数
        retry_count = 0
        
        while self.running and retry_count < max_retries:
            try:
                self.log("初始化浏览器...")
                options = webdriver.ChromeOptions()
                options.add_argument("--disable-gpu")
                options.add_argument("--disable-blink-features=AutomationControlled")
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("useAutomationExtension", False)
                options.add_argument("--ignore-certificate-errors")

                self.browser = webdriver.Chrome(options=options)
                self.browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

                self._main_booking_loop()  # 将主逻辑提取到单独方法中

            except TimeoutException as te:
                retry_count += 1
                self.log(f"⚠️ 发生超时异常 (尝试 {retry_count}/{max_retries}): {str(te)}")
                if self.browser:
                    try:
                        self.browser.quit()
                    except:
                        pass
                time.sleep(5)  # 等待一段时间再重试
                
            except Exception as e:
                self.log(f"⚠️ 发生意外错误: {str(e)}")
                break  # 非Timeout异常直接退出循环
                
        if retry_count >= max_retries:
            self.log("❌ 达到最大重试次数，停止扫描")
        self._cleanup()

    def _main_booking_loop(self):

        try:
            self.log("正在打开预约页面...")
            self.browser.get(BOOKING_URL)
            wait = WebDriverWait(self.browser, 15) # 增加等待时间，提高稳定性

            self.log("开始登录流程...")
            self.browser.refresh()
            time.sleep(time_to_sleep)

            # 等待并点击登录按钮
            login_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="logoin"]/div[1]/div/div[2]/button[1]')
            ))
            ActionChains(self.browser).move_to_element(login_element).click().perform()

            # 输入学号
            account_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="input-login-user"]')
            ))
            account_element.send_keys(jaccount)

            # 输入密码
            mima_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="input-login-pass"]')
            ))
            mima_element.send_keys(mima)

            while 'jaccount' in self.browser.current_url:
                captcha_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="captcha-img"]')
                ))
                ActionChains(self.browser).move_to_element(captcha_element).click().perform()
                time.sleep(time_to_sleep)
                # 直接对元素截图（保存为PNG二进制数据）
                image_data = captcha_element.screenshot_as_png

                # 保存到文件
                with open("captcha.png", "wb") as f:
                    f.write(image_data)

                verify_code = pytesseract.image_to_string("captcha.png", config='--psm 8') # 使用OCR识别验证码
                verify_code = self.clean_captcha_text(verify_code)  # 去除可能的空格或换行

                input_captcha_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="input-login-captcha"]')
                ))
                input_captcha_element.clear()

                input_captcha_element.send_keys(verify_code)  # 输入识别的验证码

                time.sleep(time_to_sleep)

                self.log(f"识别的验证码: {verify_code}")

                login_button = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="submit-password-button"]')
                ))
                ActionChains(self.browser).move_to_element(login_button).click().perform()
                time.sleep(time_to_sleep)



            # 在等待验证码结束后，再次检查是否已停止，以防用户在最后时刻点击停止
            if not self.running:
                self.log("线程在验证码等待后停止。")
                return

            self.log("等待登录成功...")
            # 假设登录成功后页面会跳转或出现特定元素

            # --- 主扫描循环 ---
            while self.running: # 检查停止标志
                try:
                    # 确保在每次扫描循环开始时，浏览器处于正确的健身房预约页面
                    # 如果页面不是预期的，尝试重新导航

                    # 重新点击“学生服务中心”以进入健身房预约界面
                    xuefu_element = wait.until(EC.presence_of_element_located(
                        (By.XPATH, "//h3[contains(text(), '学生中心')]/ancestor::div[1]")
                    ))
                    self.log("已进入场馆选择页面。")

                    time.sleep(time_to_sleep)
                    ActionChains(self.browser).move_to_element(xuefu_element).click().perform()

                    time.sleep(time_to_sleep)
                    self.log("切换到健身房预约页面...")
                    # 切换到健身房具体预约界面 (根据gymgui.py的XPath)
                    xuefu_element2 = wait.until(EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="tab-7d46c0a4-3ae6-4398-822b-d4b7b37085fa"]')
                    ))
                    time.sleep(time_to_sleep)
                    ActionChains(self.browser).move_to_element(xuefu_element2).click().perform()
                    self.log("开始扫描可用时间段和座位...")
                except TimeoutException:
                    self.log("无法找到场馆选择或预约页面元素，可能需要重新导航或登录。")
                    try:
                        self.browser.get(BOOKING_URL) # 尝试返回初始页面
                        self.log("已尝试返回初始页面。")
                        continue # 跳过当前循环的剩余部分，进入下一轮扫描
                    except WebDriverException as nav_e:
                        self.log(f"返回初始页面失败: {nav_e}. 终止扫描。")
                        break # 无法恢复，终止线程
                except Exception as e:
                    self.log(f"进入场馆页面时发生错误: {e}. 终止扫描。")
                    break # 致命错误，终止线程

                dates = []
                now = datetime.now()

                # 根据当前时间决定扫描的日期范围 (当天12点前扫描7天，12点后扫描8天)
                if now.hour < 12:
                    day_range = range(7)
                else:
                    day_range = range(8)

                for i in day_range:
                    expected_date = (now + timedelta(days=i)).strftime("%Y-%m-%d")
                    dates.append(expected_date)

                booking_successful_this_cycle = False # 标记本轮是否有成功预订

                for expected_date in dates:
                    if not self.running: # 在每次日期扫描前检查停止标志
                        break
                    self.log(f"扫描日期: {expected_date}")
                    try:
                        # 选择日期
                        days_element = wait.until(EC.presence_of_element_located(
                            (By.XPATH, f"//div[contains(@id, '{expected_date}')]")
                        ))
                        time.sleep(time_to_sleep)
                        ActionChains(self.browser).move_to_element(days_element).click().perform()
                    except TimeoutException:
                        self.log(f"未能找到日期 {expected_date} 的元素，跳过。")
                        self.browser.refresh() # 刷新页面尝试恢复
                        time.sleep(1) # 等待页面刷新
                        continue # 如果日期元素未找到，跳过当前日期
                    except Exception as e:
                        self.log(f"选择日期 {expected_date} 时发生错误: {e}")
                        self.browser.refresh() # 刷新页面尝试恢复
                        time.sleep(1) # 等待页面刷新
                        continue

                    # 扫描所有指定时间段
                    for time_slot in range(self.start_time, self.end_time + 1):
                        if not self.running: # 在每次时间段扫描前检查停止标志
                            break

                        self.log(f"扫描时间段: {time_slot}:00 - {time_slot + 1}:00")

                        # 扫描所有座位 (假设有5个座位，根据gymgui.py的逻辑)
                        for seat in range(1, 6): # gymgui.py中是range(1, 6)
                            if not self.running: # 在每次座位扫描前检查停止标志
                                break

                            # 构建座位元素的XPath
                            # gymgui.py中是 self.need_time - 6
                            seat_xpath = f'//*[@id="apointmentDetails"]/div[2]/div[2]/div[2]/div/div[1]/div[1]/div/div[1]/div[{time_slot - 6}]/div[{seat}]/div'

                            try:
                                # 检查座位是否可用 ("unselected" 类表示可用)
                                whether_element = wait.until(EC.presence_of_element_located(
                                    (By.XPATH, seat_xpath)
                                ))
                                flag = whether_element.get_attribute("class")

                                if "unselected" in flag:
                                    self.log(f"发现可用座位! 日期: {expected_date}, 时间段: {time_slot}:00, 座位: {seat}")
                                    # 尝试预订
                                    seat_element = whether_element # 已找到的元素可以直接使用
                                    ActionChains(self.browser).move_to_element(seat_element).click().perform()
                                    time.sleep(time_to_sleep)

                                    # 点击“立即预约”按钮
                                    order_element = wait.until(EC.presence_of_element_located(
                                        (By.XPATH, '//*[@id="apointmentDetails"]/div[2]/div[2]/div[2]/div/div[1]/div[2]/div[3]/button')
                                    ))
                                    ActionChains(self.browser).move_to_element(order_element).click().perform()
                                    time.sleep(time_to_sleep)

                                    # 勾选同意条款
                                    tips_element = wait.until(EC.presence_of_element_located(
                                        (By.XPATH, '//*[@id="apointmentDetails"]/div[2]/div[2]/div[3]/div/div[3]/div/div[1]/label/span[1]/span')
                                    ))
                                    ActionChains(self.browser).move_to_element(tips_element).click().perform()
                                    time.sleep(time_to_sleep)

                                    # 点击“提交订单”按钮
                                    submit_element = wait.until(EC.presence_of_element_located(
                                        (By.XPATH, '//*[@id="apointmentDetails"]/div[2]/div[2]/div[3]/div/div[3]/div/div[2]/button[2]/span')
                                    ))
                                    ActionChains(self.browser).move_to_element(submit_element).click().perform()
                                    time.sleep(time_to_sleep)

                                    # 点击“去支付”按钮
                                    buy_element = wait.until(EC.presence_of_element_located(
                                        (By.XPATH, '//*[@id="orderDetails"]/div[5]/div[2]/button')
                                    ))
                                    ActionChains(self.browser).move_to_element(buy_element).click().perform()
                                    time.sleep(time_to_sleep)

                                    self.log("预订成功，等待支付确认...")

                                    # 点击支付确认弹窗的“确定”按钮 (假设这是最终确认)
                                    sure_element = wait.until(EC.presence_of_element_located(
                                        (By.XPATH, '//*[@id="orderDetails"]/div[6]/div/div[3]/span/button[2]/span')
                                    ))
                                    ActionChains(self.browser).move_to_element(sure_element).click().perform()
                                    time.sleep(time_to_sleep)

                                    # 点击最终的“支付”按钮 (这可能跳转到支付页面，脚本在此可能停止)
                                    pay_element = wait.until(EC.presence_of_element_located(
                                        (By.XPATH, '//*[@id="submitBut"]')
                                    ))
                                    ActionChains(self.browser).move_to_element(pay_element).click().perform()
                                    time.sleep(time_to_sleep)

                                    # 再次点击一个确认按钮 (根据页面实际情况，可能需要调整)
                                    yes_element = wait.until(EC.presence_of_element_located(
                                        (By.XPATH, '//*[@id="ext-comp-1002"]/tbody/tr[2]/td[2]')
                                    ))
                                    ActionChains(self.browser).move_to_element(yes_element).click().perform()
                                    time.sleep(time_to_sleep)

                                    # 截图并发送微信通知
                                    screenshot_name = f"{expected_date}-{time_slot}.png"
                                    self.browser.save_screenshot(screenshot_name)

                                    self.log(f"截图已保存: {screenshot_name}")
                                    self.send_wechat_message(screenshot_name)

                                    self.success_signal.emit(f"✅ 成功预订! 日期: {expected_date}, 时间段: {time_slot}:00, 座位: {seat}")
                                    booking_successful_this_cycle = True # 标记本轮成功预订

                                    # 预订成功后，返回主页面继续扫描，不关闭浏览器
                                    self.log("预订成功，返回主页面等待下一轮扫描...")
                                    try:
                                        self.browser.get(BOOKING_URL) # 重新导航到主URL
                                        self.log("已返回主页面。")
                                    except WebDriverException as nav_e:
                                        self.log(f"返回主页面时发生错误: {nav_e}. 尝试刷新页面。")
                                        self.browser.refresh() # 回退到刷新
                                        time.sleep(2) # 给予一些时间加载

                                    break # 退出座位循环，然后时间段循环，然后日期循环，开始新的15分钟周期
                                else:
                                    self.log(f"时间段 {time_slot}:00 座位 {seat} 不可用.")
                            except TimeoutException:
                                self.log(f"等待时间段 {time_slot}:00 座位 {seat} 元素超时，可能不可用或页面未加载。")
                                time.sleep(1) # 等待页面刷新
                                continue # 继续扫描下一个座位或时间段
                            except Exception as e:
                                self.log(f"预订时间段 {time_slot}:00 座位 {seat} 时发生错误: {e}")
                                continue # 发生错误时，继续扫描其他选项

                        if booking_successful_this_cycle: # 如果本轮已成功预订，退出当前时间段循环
                            break
                    if booking_successful_this_cycle: # 如果本轮已成功预订，退出当前日期循环
                        break

                if self.running: # 只有在线程仍然运行时才进行等待，否则直接退出
                    self.log(f"当前轮次扫描完毕，等待{self.loop_time}分钟后继续下一轮扫描...")
                    self.log(f"下次扫描时间：{datetime.now() + timedelta(minutes=self.loop_time)}")
                    # 使用小步长睡眠，以便在收到停止信号时能及时中断
                    for _ in range(15 * 60): # 15分钟 * 60秒/分钟 = 900秒
                        if not self.running:
                            break # 如果停止标志变为False，立即中断睡眠
                        time.sleep(1)
            self.log("扫描线程已停止。")

        except Exception as e:
            self.log(f"运行过程中发生致命错误: {e}")
        finally:
            # 确保无论发生什么，浏览器最终都会被关闭
            if self.browser:
                try:
                    self.browser.quit()
                    self.log("浏览器已关闭。")
                except WebDriverException as e:
                    self.log(f"关闭浏览器时发生错误: {e}")
                self.browser = None # 清除引用

    def log(self, message):
        """发送日志消息到UI"""
        self.log_signal.emit(message)

    def _cleanup(self):
        """清理资源"""
        if self.browser:
            try:
                self.browser.quit()
                self.log("浏览器已关闭。")
            except WebDriverException as e:
                self.log(f"关闭浏览器时发生错误: {e}")
            self.browser = None

class BookingApp(QWidget):
    """
    PyQt6 应用程序主窗口，提供用户界面来控制预约线程。
    """
    def __init__(self): # 修正了这里的语法错误
        super().__init__()
        self.initUI()
        self.booking_thread = None # 预约线程实例

    def initUI(self):
        """初始化用户界面布局和组件。"""
        self.setWindowTitle("交我抢-健身房版(持续扫描版)")
        self.setGeometry(200, 200, 600, 500) # 调整窗口大小
        self.setWindowIcon(QIcon("Gym.ico")) # 如果有图标文件，可以取消注释

        layout = QVBoxLayout()

        # 开始时间输入
        start_layout = QHBoxLayout()
        self.start_label = QLabel("开始时间 (小时，例如 9):")
        self.start_label.setFont(QFont("Arial", 12))
        self.start_input = QLineEdit()
        self.start_input.setText("9") # 默认开始时间
        self.start_input.setFont(QFont("Arial", 12))
        start_layout.addWidget(self.start_label)
        start_layout.addWidget(self.start_input)

        # 结束时间输入
        end_layout = QHBoxLayout()
        self.end_label = QLabel("结束时间 (小时，例如 21):")
        self.end_label.setFont(QFont("Arial", 12))
        self.end_input = QLineEdit()
        self.end_input.setText("21") # 默认结束时间
        self.end_input.setFont(QFont("Arial", 12))
        end_layout.addWidget(self.end_label)
        end_layout.addWidget(self.end_input)

        loop_layput = QHBoxLayout()
        self.loop_label = QLabel("扫描间隔 (分钟):")
        self.loop_label.setFont(QFont("Arial", 12))
        self.loop_input = QLineEdit()
        self.loop_input.setText("15")
        self.loop_input.setFont(QFont("Arial", 12))
        loop_layput.addWidget(self.loop_label)
        loop_layput.addWidget(self.loop_input)

        # 按钮
        self.start_button = QPushButton("开始扫描")
        self.start_button.setFont(QFont("Arial", 14)) # 增大字体
        self.start_button.setFixedSize(120, 60) # 增大按钮尺寸
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; /* 绿色 */
                color: white;
                border-radius: 10px; /* 更圆润的边角 */
                padding: 10px;
                font-weight: bold;
                border: 2px solid #388E3C; /* 深绿色边框 */
            }
            QPushButton:hover {
                background-color: #45a049;
                border: 2px solid #388E3C;
            }
            QPushButton:pressed {
                background-color: #388E3C;
            }
            QPushButton:disabled {
                background-color: #A5D6A7; /* 禁用状态颜色 */
                color: #E0E0E0;
                border: 2px solid #C8E6C9;
            }
        """)

        self.stop_button = QPushButton("停止扫描")
        self.stop_button.setFont(QFont("Arial", 14)) # 增大字体
        self.stop_button.setFixedSize(120, 60) # 增大按钮尺寸
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336; /* 红色 */
                color: white;
                border-radius: 10px; /* 更圆润的边角 */
                padding: 10px;
                font-weight: bold;
                border: 2px solid #D32F2F; /* 深红色边框 */
            }
            QPushButton:hover {
                background-color: #d32f2f;
                border: 2px solid #D32F2F;
            }
            QPushButton:pressed {
                background-color: #C62828;
            }
            QPushButton:disabled {
                background-color: #FFCDD2; /* 禁用状态颜色 */
                color: #E0E0E0;
                border: 2px solid #EF9A9A;
            }
        """)
        self.stop_button.setEnabled(False) # 初始禁用停止按钮

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)
        button_layout.addWidget(self.stop_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # 日志输出区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True) # 只读
        self.log_text.setFont(QFont("Consolas", 10)) # 使用等宽字体方便阅读日志
        # 修改背景为黑色，文字为白色
        self.log_text.setStyleSheet("background-color: black; color: white; border: 1px solid #cccccc;") 

        # 添加到主布局
        layout.addLayout(start_layout)
        layout.addLayout(end_layout)
        layout.addLayout(loop_layput)
        layout.addLayout(button_layout)
        layout.addWidget(self.log_text)
        self.setLayout(layout)

        # 连接信号与槽
        self.start_button.clicked.connect(self.start_booking)
        self.stop_button.clicked.connect(self.stop_booking)

    def start_booking(self):
        """
        开始预约扫描。
        从输入框获取时间，创建并启动BookingThread。
        """
        try:
            start_time = int(self.start_input.text())
            end_time = int(self.end_input.text())
            loop_time = float(self.loop_input.text())


            # 输入时间验证
            if not (6 <= start_time <= 22 and 6 <= end_time <= 22 and start_time <= end_time):
                self.log_text.append("❌ 错误: 开始和结束时间必须在 7-22 之间，且开始时间不能晚于结束时间。")
                return

            self.log_text.append(f"🚀 开始扫描时间段: {start_time}:00 到 {end_time}:00")
            # 创建新的线程实例
            self.booking_thread = BookingThread(start_time, end_time, loop_time)
            # 连接线程的信号到UI更新槽
            self.booking_thread.log_signal.connect(self.update_log)
            self.booking_thread.success_signal.connect(self.booking_success)
            # 启动线程
            self.booking_thread.start()

            # 更新按钮状态
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

        except ValueError:
            self.log_text.append("❌ 错误: 时间输入必须是 **整数** (小时)。")
        except Exception as e:
            self.log_text.append(f"❌ 启动扫描时发生意外错误: {e}")

    def stop_booking(self):
        """
        停止预约扫描。
        向BookingThread发送停止信号并等待其终止。
        """
        if self.booking_thread and self.booking_thread.isRunning():
            self.log_text.append("⏳ 正在发送停止信号，请稍候...")
            self.booking_thread.stop() # 调用线程的停止方法
            self.booking_thread.wait() # 等待线程完成其清理工作并终止
            self.log_text.append("🛑 扫描已停止。")
            # 更新按钮状态
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
        else:
            self.log_text.append("ℹ️ 扫描未运行，无需停止。")

    def booking_success(self, message):
        """
        处理预约成功的信号。
        更新日志，但不停止扫描线程，而是让其继续。
        """
        self.log_text.append(message)
        # 预订成功后，不再停止线程，而是让其继续扫描。
        # 按钮状态保持不变（开始按钮禁用，停止按钮启用）。
        # self.start_button.setEnabled(True) # 移除此行
        # self.stop_button.setEnabled(False) # 移除此行

    def update_log(self, message):
        """
        更新日志文本框。
        """
        self.log_text.append(message)
        # 移除了自动滚动功能
        # self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BookingApp()
    window.show()
    sys.exit(app.exec())

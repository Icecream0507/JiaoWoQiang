import sys
import time
import requests
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QThread
import sys
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PyInstaller.utils.win32.versioninfo import VSVersionInfo



with open("account.txt", "r") as f:
    lines = f.readlines()
    jaccount = lines[0].split("=")[1].strip()  # 学号
    mima = lines[1].split("=")[1].strip()  # 密码


book_time = "12:00:00"

time_to_sleep = 0.1  # 设置等待时间间隔

class BookingThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, need_time):
        super().__init__()
        self.need_time = need_time

    def run(self):
        try:
            self.log("初始化浏览器...")
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument("--ignore-certificate-errors")
            
            browser = webdriver.Chrome(options=options)
            browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

            self.log("正在打开预约页面...")
            url = "https://sports.sjtu.edu.cn/pc#/"
            browser.get(url)
            wait = WebDriverWait(browser, 10)
        
                
            self.log("开始预约...")
            browser.refresh()
            time.sleep(time_to_sleep)

            wait = WebDriverWait(browser, 10)  # 显式等待

            expected_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
            self.log(f"预期日期: {expected_date}")

            try:
                # 等待并点击“学生服务中心”
                xuefu_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//h3[contains(text(), '气膜体育中心')]/ancestor::div[1]")
                ))
                ActionChains(browser).move_to_element(xuefu_element).click().perform()

                # 等待并点击登录按钮
                login_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="loginSelection"]/div/div[2]/div[2]/button')
                ))
                ActionChains(browser).move_to_element(login_element).click().perform()


                account_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="input-login-user"]')
                ))

                account_element.send_keys(jaccount)

                mima_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="input-login-pass"]')
                ))

                mima_element.send_keys(mima)

                self.log("请在8s内输入验证码...")

                time.sleep(8)

                xuefu_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, "//h3[contains(text(), '气膜体育中心')]/ancestor::div[1]")
                ))

                self.log("验证码正确，登陆成功...")

                time.sleep(time_to_sleep)
                ActionChains(browser).move_to_element(xuefu_element).click().perform()


                # 获取服务器时间并计算时间差
                response = requests.get(url, verify=False)
                server_time = response.headers.get("Date")
                
                server_time_utc = datetime.strptime(server_time, "%a, %d %b %Y %H:%M:%S %Z")
                server_time = server_time_utc + timedelta(hours=8)  # 转换为北京时间
                local_time = datetime.now()
                local_str = local_time.strftime("%Y-%m-%d %H:%M:%S")
                self.log(f"当前时间: {local_str}")
                self.log(f"服务器时间: {server_time}")
                server_time_diff =  local_time - server_time

                a = 0
                symbol_list = ["|", "/", "-", "\\"]
                # 循环条件：直到本地时间加上时间差后超过22:30:00
                end_time = datetime.strptime(book_time, "%H:%M:%S").replace(year=local_time.year, month=local_time.month, day=local_time.day)
                while (local_time - server_time_diff).time() <= end_time.time():
                    time_to_wait = (end_time - (local_time - server_time_diff)).total_seconds()
                    if time_to_wait >= 130:
                        time.sleep(20)
                        self.log(f"\r等待~ 😋 {symbol_list[a%4]}... 当前时间: {(local_time - server_time_diff).strftime('%H:%M:%S')}")
                        if int(time_to_wait) % 120 in [t for t in range(0, 20)]:
                            browser.refresh()
                            self.log("刷新完睡会儿💤")
                            time.sleep(110)
                    else:
                        time.sleep(time_to_sleep)
                        self.log(f"\r等待~ 😋 {symbol_list[a%4]}... 当前时间: {(local_time - server_time_diff).strftime('%H:%M:%S')}")
                    
                    local_time = datetime.now()
                    a += 1
                    

                self.log("午时已到🏋️‍ 开始预约...")

                browser.refresh()
                time.sleep(time_to_sleep)

                logstr = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.log(f"time: {logstr}")

                xuefu_element2 = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="tab-29942202-d2ac-448e-90b7-14d3c6be19ff"]')
                ))
                time.sleep(time_to_sleep)
                ActionChains(browser).move_to_element(xuefu_element2).click().perform()

                days_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, f"//div[contains(@id, '{expected_date}')]")
                ))
                time.sleep(time_to_sleep)
                ActionChains(browser).move_to_element(days_element).click().perform()
                
                seat = 0

                self.log("开始查找座位💺...")
                time.sleep(0.5)
                
                for i in range(1, 6):
                    
                    self.log(f"正在查找第 {i} 个座位💺...")
                    
                    whether_s = f'//*[@id="apointmentDetails"]/div[2]/div[2]/div[2]/div/div[1]/div[1]/div/div[1]/div[{self.need_time - 6}]/div[{i}]/div'


                    whether_element = wait.until(EC.presence_of_element_located(
                            (By.XPATH, whether_s)
                        ))
                    
                    flag = whether_element.get_attribute("class")

                    if "unselected" in flag:
                        self.log(f"{i} 座位💺可用")
                        seat = i
                        break
                    else:
                        self.log(f"{i}座位💺不可用")
                        
                if seat == 0:
                    raise Exception("没抢到，遗憾离场😭")

                seat_tab = f'//*[@id="apointmentDetails"]/div[2]/div[2]/div[2]/div/div[1]/div[1]/div/div[1]/div[{self.need_time - 6}]/div[{seat}]/div'
                self.log(f"选择座位: {seat}")
                self.log("开始预约座位💺...")
                seat_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, seat_tab)
                ))
                time.sleep(time_to_sleep)
                ActionChains(browser).move_to_element(seat_element).click().perform()

                order_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="apointmentDetails"]/div[2]/div[2]/div[2]/div/div[1]/div[2]/div[3]/button')
                ))
                time.sleep(time_to_sleep)
                ActionChains(browser).move_to_element(order_element).click().perform()

                tips_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="apointmentDetails"]/div[2]/div[2]/div[3]/div/div[3]/div/div[1]/label/span[1]/span')
                ))

                time.sleep(time_to_sleep)
                ActionChains(browser).move_to_element(tips_element).click().perform()

                submit_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="apointmentDetails"]/div[2]/div[2]/div[3]/div/div[3]/div/div[2]/button[2]/span')
                ))
                time.sleep(time_to_sleep)
                ActionChains(browser).move_to_element(submit_element).click().perform()

                self.log("来财💰...")
                time.sleep(8)
                

                try:
                    money_element = wait.until(EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="orderDetails"]/div[5]/div[2]/button')
                    ))
                except:
                    self.log("也许网络卡顿，不过已经抢到了😋, 不用谢")
                time.sleep(time_to_sleep)
                ActionChains(browser).move_to_element(money_element).click().perform()

                confirm_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="orderDetails"]/div[6]/div/div[3]/span/button[2]')
                ))
                time.sleep(time_to_sleep)
                ActionChains(browser).move_to_element(confirm_element).click().perform()


                next_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="submitBut"]')
                ))
                time.sleep(time_to_sleep)
                ActionChains(browser).move_to_element(next_element).click().perform()

                yes_element = wait.until(EC.presence_of_element_located(
                    (By.XPATH, '//*[@id="ext-comp-1002"]/tbody/tr[2]/td[2]')
                ))
                time.sleep(time_to_sleep)
                ActionChains(browser).move_to_element(yes_element).click().perform()

                # 使用截图方法截取整个页面
                browser.save_screenshot(f"{expected_date}-{self.need_time}.png")

                self.log("EASY 截图已保存在运行文件夹下! 不用谢😊")


            except Exception as e:
                self.log(f"发生错误: {e}")

            finally:
                browser.quit()

            self.log("Over.")
        
        except Exception as e:
            self.log(f"错误: {e}")
        finally:
            browser.quit()
            self.log("浏览器已关闭。")
    
    def log(self, message):
        self.log_signal.emit(message)

class BookingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    
    def initUI(self):
        self.setWindowTitle("交我抢-气模羽球版")
        self.setGeometry(200, 200, 400, 300)
        self.setWindowIcon(QIcon("Badmin.ico"))  # 需要 ice_cream.png 作为图标

        layout = QVBoxLayout()
        
        self.label = QLabel("请输入抢票时间 (24小时制):")
        self.label.setFont(QFont("Arial", 12))
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.time_input = QLineEdit()
        self.time_input.setText("17")
        self.time_input.setFont(QFont("Arial", 12))
        self.time_input.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.start_button = QPushButton("开始抢票")
        self.start_button.setFont(QFont("Arial", 12))
        self.start_button.setFixedSize(100, 50)  # **设置按钮为小方形**
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #A9A9A9;
                color: white;
                border-radius: 8px;  /* **小方块圆角** */
                padding: 5px;
                font-size: 20px;
            }
            QPushButton:hover {
                background-color: #808080;
            }
        """)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Arial", 10))
        
        self.start_button.clicked.connect(self.start_booking)
        
        layout.addWidget(self.label)
        layout.addWidget(self.time_input)
        layout.addWidget(self.start_button, alignment=Qt.AlignmentFlag.AlignCenter)  # **按钮居中**
        layout.addWidget(self.log_text)
        self.setLayout(layout)
    
    def start_booking(self):
        need_time = int(self.time_input.text())
        self.log_text.append(f"设置预约时间: {need_time}")
        self.thread = BookingThread(need_time)
        self.thread.log_signal.connect(self.update_log)
        self.thread.start()
    
    def update_log(self, message):
        self.log_text.append(message)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BookingApp()
    window.show()
    sys.exit(app.exec())

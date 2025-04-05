from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
from datetime import timedelta
import requests


need_time = 17  # 时间 24小时制

with open("account.txt", "r") as f:
    lines = f.readlines()
    jaccount = lines[0].split("=")[1].strip()  # 学号
    mima = lines[1].split("=")[1].strip()  # 密码

book_time = "12:00:00"


options = webdriver.ChromeOptions()

# 浏览器设置
options.add_argument("--disable-gpu")
# options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")  # 防止被检测
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option("useAutomationExtension", False)

options.add_argument("--ignore-certificate-errors")

# 启动浏览器
browser = webdriver.Chrome(options=options)
browser.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")  # 进一步防止检测

# 获取当前日期
formatted_date = datetime.now().strftime("%Y-%m-%d")
print("格式化后的日期:", formatted_date)

# 计算预期日期（当前日期加上7天）
expected_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
print("预期日期:", expected_date)


# 打开目标网页
url = "https://sports.sjtu.edu.cn/pc#/"
browser.get(url)

wait = WebDriverWait(browser, 10)  # 显式等待

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

    login_element2 = wait.until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="submit-password-button"]')
    ))

    account_element = wait.until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="input-login-user"]')
    ))

    account_element.send_keys(jaccount)

    mima_element = wait.until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="input-login-pass"]')
    ))

    mima_element.send_keys(mima)

    print("请在8s内输入验证码...")

    time.sleep(8)

    xuefu_element = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//h3[contains(text(), '气膜体育中心')]/ancestor::div[1]")
    ))

    print("验证码正确，登陆成功...")
    time.sleep(0.1)
    ActionChains(browser).move_to_element(xuefu_element).click().perform()


    # 获取服务器时间并计算时间差
    response = requests.get(url, verify=False)
    server_time = response.headers.get("Date")
    
    server_time_utc = datetime.strptime(server_time, "%a, %d %b %Y %H:%M:%S %Z")
    server_time = server_time_utc + timedelta(hours=8)  # 转换为北京时间
    local_time = datetime.now()
    print("当前时间:", local_time.strftime("%Y-%m-%d %H:%M:%S"))
    print("服务器时间:", server_time)
    server_time_diff =  local_time - server_time

    a = 0
    symbol_list = ["|", "/", "-", "\\"]
    # 循环条件：直到本地时间加上时间差后超过22:30:00
    end_time = datetime.strptime(book_time, "%H:%M:%S").replace(year=local_time.year, month=local_time.month, day=local_time.day)
    while (local_time - server_time_diff).time() <= end_time.time():
        time_to_wait = (end_time - (local_time - server_time_diff)).total_seconds()
        if time_to_wait % 120 == 0:
            browser.refresh()
            local_time = datetime.now()
        else:
            time.sleep(0.1)
            local_time = datetime.now()
        print(f"\r别急，美好的事情值得等待 😋 {symbol_list[a%4]}... 当前时间: {(local_time - server_time_diff).strftime('%H:%M:%S')} 剩余等待时间: {time_to_wait:.2f}秒")
        a += 1
        

    print("午时已到🏋️‍ 开始预约...")

    browser.refresh()
    time.sleep(0.1)

    print("time:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    xuefu_element2 = wait.until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="tab-29942202-d2ac-448e-90b7-14d3c6be19ff"]')
    ))
    time.sleep(0.1)
    ActionChains(browser).move_to_element(xuefu_element2).click().perform()

    days_tab = f"tab + {expected_date}"
    days_element = wait.until(EC.presence_of_element_located(
        (By.XPATH, f"//div[contains(@id, '{expected_date}')]")
    ))
    time.sleep(0.1)
    ActionChains(browser).move_to_element(days_element).click().perform()
    
    

    seat = 0

    print("开始查找座位💺...")
    for i in range(1, 6):
        
        print(f"正在查找第 {i} 个座位💺...")
        
        whether_s = f'//*[@id="apointmentDetails"]/div[2]/div[2]/div[2]/div/div[1]/div[1]/div/div[1]/div[{need_time - 6}]/div[{i}]/div'


        whether_element = wait.until(EC.presence_of_element_located(
                (By.XPATH, whether_s)
            ))
        
        flag = whether_element.get_attribute("class")

        if "unselected" in flag:
            print(f"{i} 座位💺可用")
            seat = i
            break
        else:
            print(f"{i}座位💺不可用")

    if seat == 0:
        raise Exception("没抢到，遗憾离场😭")
    
    seat_tab = f'//*[@id="apointmentDetails"]/div[2]/div[2]/div[2]/div/div[1]/div[1]/div/div[1]/div[{need_time - 6}]/div[{seat}]/div'
    print(f"选择座位: {seat}")
    print("开始预约座位💺...")
    seat_element = wait.until(EC.presence_of_element_located(
        (By.XPATH, seat_tab)
    ))
    time.sleep(0.1)
    ActionChains(browser).move_to_element(seat_element).click().perform()

    order_element = wait.until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="apointmentDetails"]/div[2]/div[2]/div[2]/div/div[1]/div[2]/div[3]/button')
    ))
    time.sleep(0.1)
    ActionChains(browser).move_to_element(order_element).click().perform()

    tips_element = wait.until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="apointmentDetails"]/div[2]/div[2]/div[3]/div/div[3]/div/div[1]/label/span[1]/span')
    ))

    time.sleep(0.1)
    ActionChains(browser).move_to_element(tips_element).click().perform()

    submit_element = wait.until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="apointmentDetails"]/div[2]/div[2]/div[3]/div/div[3]/div/div[2]/button[2]/span')
    ))
    time.sleep(0.1)
    ActionChains(browser).move_to_element(submit_element).click().perform()

    print("来财💰...")
    time.sleep(8)
    

    try:
        money_element = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//*[@id="orderDetails"]/div[5]/div[2]/button')
        ))
    except:
        print("也许网络卡顿，不过已经抢到了😋, 不用谢  --from 🍦")


    time.sleep(0.1)
    ActionChains(browser).move_to_element(money_element).click().perform()

    confirm_element = wait.until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="orderDetails"]/div[6]/div/div[3]/span/button[2]')
    ))
    time.sleep(0.1)
    ActionChains(browser).move_to_element(confirm_element).click().perform()


    next_element = wait.until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="submitBut"]')
    ))
    time.sleep(0.1)
    ActionChains(browser).move_to_element(next_element).click().perform()

    yes_element = wait.until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="ext-comp-1002"]/tbody/tr[2]/td[2]')
    ))
    time.sleep(0.1)
    ActionChains(browser).move_to_element(yes_element).click().perform()

    code_element = wait.until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="code_url"]/div')
    ))

    # 定位到需要截图的区域
    element = wait.until(EC.presence_of_element_located(
        (By.XPATH, '//*[@id="code_url"]/div')
    ))

    # 获取该区域的位置和大小
    location = element.location
    size = element.size

    # 使用截图方法截取整个页面
    browser.save_screenshot(f"{expected_date}-{need_time}.png")

    print("EASY 截图已保存在运行文件夹下! 不用谢😊 --from 🍦")


except Exception as e:
    print(f"获取元素失败: {e}")

finally:
    browser.quit()

print("It's over.")


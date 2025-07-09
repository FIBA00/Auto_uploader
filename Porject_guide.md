
Step	Command
1	Open Termux
2	Allow access to storage memory
3	
termux-setup-storage
4	Force exit Termux
5	Reopen Termux
6	Update & Upgrade package
7	
yes | pkg update -y && yes | pkg upgrade -y
8	Install pip (they seperated it from python)
9	
yes | pkg install python-pip -y
10	Install selenium
11	
pip install selenium==4.9.1
12	PLEASE MAKE SURE YOUR SELENIUM VERSION <= 4.9.1
Choose WebDriver you want install
Chromium	Firefox
yes | pkg install x11-repo -y
yes | pkg install tur-repo -y
yes | pkg install chromium -y
yes | pkg install x11-repo -y
yes | pkg install firefox -y
yes | pkg install geckodriver -y


# chrome

from selenium import webdriver
options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--headless=new")
driver = webdriver.Chrome(options=options)
driver.get("https://www.google.com")
driver.save_screenshot("/sdcard/download/screenshot.png")
print("Please check screenshot image")
driver.quit()


# firefox
from selenium import webdriver
options = webdriver.FirefoxOptions()
options.add_argument("--headless")
driver = webdriver.Firefox(options=options)
driver.get("https://www.google.com")
driver.save_screenshot("/sdcard/download/screenshot.png")
driver.quit()
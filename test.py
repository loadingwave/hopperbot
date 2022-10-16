from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

from time import sleep

options = Options()
options.headless = True
driver = Chrome(options=options)

driver.set_window_position(0, 0)
driver.set_window_size(1500, 3000)

url = "https://twitter.com/cuptoast/status/1551711157785751553"

print("Getting webpage...")
driver.get(url)

# Just to make sure all elements load first
print("sleeping 2 seconds...")
sleep(2)

scrolling_xpath = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div"
full_element = driver.find_element(By.XPATH, scrolling_xpath)
driver.execute_script("arguments[0].scrollIntoView();", full_element)

driver.save_screenshot("fullscreen.png")

print("sleeping 2 seconds...")
sleep(2)

# tweet_xpath = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[{}]/div/div/div/article"
tweet_xpath = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[{}]"

for i in range(1, 12):
    print("screenshot ", i)
    tweet_element = driver.find_element(By.XPATH, tweet_xpath.format(i))
    tweet_element.screenshot("tweet{}.png".format(i))

    height = tweet_element.rect["height"]
    ActionChains(driver).scroll_by_amount(0, height).perform()

driver.close()

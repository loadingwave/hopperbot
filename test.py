from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options

from time import sleep

options = Options()
options.headless = True
driver = Firefox(options=options)

driver.set_window_position(0, 0)
driver.set_window_size(1500, 3000)

url = "https://twitter.com/cuptoast/status/1551711157785751553"

driver.get(url)

# Just to make sure all elements load first
print("sleeping 1 second...")
sleep(1)

scrolling_xpath = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div"
full_element = driver.find_element(By.XPATH, scrolling_xpath)

driver.save_screenshot("fullscreen.png")

driver.execute_script("arguments[0].scrollIntoView();", full_element)

print("sleeping 2 seconds...")
sleep(2)

# tweet_xpath = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[{}]/div/div/div/article"
# tweet_xpath = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[{}]"

footer_xpath = "/html/body/div[1]/div/div/div[1]/div"
header_xpath = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/div[1]"

footer_element = driver.find_element(By.XPATH, footer_xpath)
footer_element.screenshot("footer.png")

header_element = driver.find_element(By.XPATH, header_xpath)
header_element.screenshot("header.png")


# for i in range(1, 12):
#     print("screenshot ", i)
#     tweet_element = driver.find_element(By.XPATH, tweet_xpath.format(i))
#     driver.execute_script("arguments[0].scrollIntoView();", tweet_element)
#     tweet_element = driver.find_element(By.XPATH, tweet_xpath.format(i))
#     tweet_element.screenshot("tweet{}.png".format(i))

# img = web_element.screenshot_as_png

# filename = "tweet.png"
# # Write the image data to a file
# with open(filename, "wb") as file:
#     file.write(img)

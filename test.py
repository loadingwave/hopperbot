from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

from time import sleep

viewport_width = 1500
viewport_height = 2000
footer_height = 225
header_bottom = 53

options = Options()
options.headless = True
driver = Chrome(options=options)

driver.set_window_position(0, 0)
driver.set_window_size(viewport_width, viewport_height)

url = "https://twitter.com/cuptoast/status/1551711157785751553"

print("Getting webpage...")
driver.get(url)

# Just to make sure all elements load first
print("sleeping 2 seconds...")
sleep(1.5)

# Scroll to top
scrolling_xpath = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div"
full_element = driver.find_element(By.XPATH, scrolling_xpath)
driver.execute_script("arguments[0].scrollIntoView();", full_element)

print("sleeping 2 seconds...")
sleep(1.5)

tweet_xpath = "/html/body/div[1]/div/div/div[2]/main/div/div/div/div[1]/div/section/div/div/div[{}]"

view_bottom = viewport_height - footer_height

for i in range(1, 12):
    tweet_element = driver.find_element(By.XPATH, tweet_xpath.format(i))
    tweet_top = tweet_element.rect["y"]
    tweet_height = tweet_element.rect["height"]
    tweet_bottom = tweet_top + tweet_height
    print(
        "tweet {} bottom is at {} + {} = {}".format(
            i, tweet_top, tweet_height, tweet_bottom
        )
    )

    if tweet_bottom >= view_bottom:
        to_scroll = tweet_top - header_bottom
        print("Scrolled by", to_scroll)
        ActionChains(driver).scroll_by_amount(0, to_scroll).perform()
        view_bottom += to_scroll
        header_bottom += to_scroll

        # because we scrolled we now need to relocate the tweet
        tweet_element = driver.find_element(By.XPATH, tweet_xpath.format(i))

    tweet_element.screenshot("tweet{}.png".format(i))

driver.close()

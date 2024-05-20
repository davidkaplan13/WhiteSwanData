from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from selenium.webdriver.safari.webdriver import WebDriver as SafariWebDriver
from selenium.webdriver.remote.webelement import WebElement
from datetime import datetime, timedelta
import pandas as pd
from typing import Any
import time
import re

def establish_connection(connection_str: str) -> SafariWebDriver:
    driver = webdriver.Safari()
    driver.get(connection_str)
    try:
        WebDriverWait(driver, 180).until(EC.presence_of_element_located((By.ID, "main-content")))
    except TimeoutException:
        driver.quit()
        exit()
    return driver

 
def re_initalize_elements(location: WebElement) -> list[WebElement]:
    return location.find_elements(By.TAG_NAME, "a")

def get_race_containers(driver, search_string: str = "css-1d6i0xy-Tabs-Tabs-Tabs-Tabs-Tabs-Tabs", search_type: Any = By.CLASS_NAME) -> list[WebElement]:
    return driver.find_elements(search_type, search_string)

def date_parser(time) -> str:
    current_time = datetime.now()
    hours = int(re.search(r'(\d+)h', time).group(1)) if re.search(r'(\d+)h', time) else 0
    minutes = int(re.search(r'(\d+)m', time).group(1)) if re.search(r'(\d+)h', time) else 0
    days = int(re.search(r'(\d+)d', time).group(1)) if re.search(r'(\d+)h', time) else 0
    if (hours, minutes, days) == (0, 0, 0):
        return "Event Finished"
    return current_time + timedelta(days=days, hours=hours, minutes=minutes).strftime("%Y-%m-%d %H:%M")

def extract_race_urls(driver: SafariWebDriver) -> tuple(list[str], list[str], list[str]):
    wait = WebDriverWait(driver, 10)

    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "css-1gtokez-RaceNav-RaceNav-RaceNav__CarouselItem-RaceNav-MeetingContainer-MeetingContainer__RaceNav-MeetingContainer")))
    wrapper = driver.find_element(By.CLASS_NAME, "css-1gtokez-RaceNav-RaceNav-RaceNav__CarouselItem-RaceNav-MeetingContainer-MeetingContainer__RaceNav-MeetingContainer")

    try:
        slides = wrapper.find_elements(By.CLASS_NAME, "swiper-slide")
    except TimeoutException:
        wrapper = driver.find_element(By.CLASS_NAME, "css-1gtokez-RaceNav-RaceNav-RaceNav__CarouselItem-RaceNav-MeetingContainer-MeetingContainer__RaceNav-MeetingContainer")
        slides = wrapper.find_elements(By.CLASS_NAME, "swiper-slide")

    hrefs = []
    times = []
    race_numbers = []
    race_number = 0
    for slide in slides:
        anchors = slide.find_elements(By.TAG_NAME, "a")
        for anchor_index in range(len(anchors)):
            try:
                href = anchors[anchor_index].get_attribute("href")
            except StaleElementReferenceException:
                href = re_initalize_elements(slide)[anchor_index].get_attribute("href")
                
            try:
                time = anchors[anchor_index].find_element(By.XPATH, ".//div[2]").text
            except StaleElementReferenceException:
                time = re_initalize_elements(slide)[anchor_index].find_element(By.XPATH, ".//div[2]").text
                
            
            event_time = date_parser(time)

            hrefs.append(href)
            times.append(event_time)  
            race_number += 1
            race_numbers.append(race_number)
    return hrefs, times, race_numbers

def click_race_date(driver: SafariWebDriver, element_selector: str) -> SafariWebDriver:
    button = driver.find_element(By.CSS_SELECTOR, element_selector)
    driver.execute_script("arguments[0].click();", button)
    return driver    

def extract_tracks(driver: SafariWebDriver, tommorw: bool=False) -> pd.DataFrame:
    tracks = []
    tracks_links = []
    race_times = []
    race_numbers = []
    wait = WebDriverWait(driver, 10)
    
    if tommorw:
        button_selector = '[data-fs-title="page:racing-tab:tomorrow-header_bar"]'
    else:
        button_selector = '[data-fs-title="page:racing-tab:today-header_bar"]'
    
    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector)))
    driver = click_race_date(driver, button_selector)
    driver = click_race_date(driver, button_selector)
    
    # Number of Race Containers - There is usually 3 types of races (Gallops, Greyhounds, Harness)
    race_containers = get_race_containers(driver)
    
    for race_index in range(len(race_containers)):
        race_containers = get_race_containers(driver)
        race = race_containers[race_index]
        items = re_initalize_elements(race)
        print(len(items), len(race_containers))
        
        for item_index in range(len(items)):
            race_containers = get_race_containers(driver)
            race = race_containers[race_index]
            item = re_initalize_elements(race)[item_index]
            
            try:
                track = item.get_attribute("title")
            except StaleElementReferenceException:
                track = re_initalize_elements(race)[item_index].get_attribute("title")
            
            if not track:
                continue
            
            
            item = re_initalize_elements(race)[item_index]
            try:
                driver.execute_script("arguments[0].click();", item)
            except:
                driver.execute_script("arguments[0].click();", re_initalize_elements(race)[item_index])
            hrefs, times, track_race_numbers = extract_race_urls(driver)
            for index in range(len(hrefs)):
                tracks.append(track)
                tracks_links.append(hrefs[index])
                race_times.append(times[index])
                race_numbers.append(track_race_numbers[index])

            
            time.sleep(2)
            button = driver.find_element(By.CSS_SELECTOR, button_selector)
            try:
                driver.execute_script("arguments[0].click();", button)
            except:
                button = driver.find_element(By.CSS_SELECTOR, button_selector)
                driver.execute_script("arguments[0].click();", button)
    
            
            # Wait until the page is back to the race container state
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "css-1d6i0xy-Tabs-Tabs-Tabs-Tabs-Tabs-Tabs")))
    
    return pd.DataFrame(data={"Track Name": tracks, "Track Links": tracks_links, "Race Time": race_times, "Race Number": race_numbers})

        

if __name__ == "__main__":
    response = establish_connection("https://getsetbet.com.au/racing/")
    response.implicitly_wait(60)
    df = extract_tracks(response)
    df1 = extract_tracks(response, True)
    df2 = pd.concat([df, df1])
    df2.to_csv("df_races_data.csv")

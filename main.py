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
import random

class RaceNotFoundException(Exception):
    pass

def establish_connection(connection_str: str) -> SafariWebDriver:
    """ Establish inital connection"""
    driver = webdriver.Safari()
    driver.get(connection_str)
    try:
        WebDriverWait(driver, 180).until(EC.presence_of_element_located((By.ID, "main-content")))
    except TimeoutException:
        driver.quit()
        exit()
    return driver

 
def re_initalize_elements(location: WebElement) -> list[WebElement] | WebElement:
    """Re-initialize elements for a given element - StaleElement Handler."""
    return location.find_elements(By.TAG_NAME, "a")

def get_race_containers(driver, search_string: str = "css-1d6i0xy-Tabs-Tabs-Tabs-Tabs-Tabs-Tabs", search_type: Any = By.CLASS_NAME) -> list[WebElement]:
    return driver.find_elements(search_type, search_string)

def date_parser(time) -> str:
    """ Custom date parser to estimate starting time. Time will be given according to UK as the time is not present on site. """
    current_time = datetime.now()
    hours = int(re.search(r'(\d+)h', time).group(1)) if re.search(r'(\d+)h', time) else 0
    minutes = int(re.search(r'(\d+)m', time).group(1)) if re.search(r'(\d+)m', time) else 0
    days = int(re.search(r'(\d+)d', time).group(1)) if re.search(r'(\d+)d', time) else 0
    if (hours, minutes, days) == (0, 0, 0):
        return "Event Finished"
    return (current_time + timedelta(days=days, hours=hours, minutes=minutes)).strftime("%Y-%m-%d %H:%M")

def extract_race_urls(driver: SafariWebDriver, tomorrow: bool=False) -> Any:
    """ Gets race urls, times and number. """
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
    days = []
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
            if tomorrow:
                days.append("tomorrow")
            else:
                days.append("today")
            
            race_numbers.append(race_number)
            
    return hrefs, times, race_numbers, days

def click_race_date(driver: SafariWebDriver, element_selector: str) -> SafariWebDriver:
    """ Click on race date element"""
    button = driver.find_element(By.CSS_SELECTOR, element_selector)
    try:
        driver.execute_script("arguments[0].click();", button)
    except StaleElementReferenceException:
        button = driver.find_element(By.CSS_SELECTOR, element_selector)
        driver.execute_script("arguments[0].click();", button)
    return driver    

def extract_tracks(driver: SafariWebDriver, tomorrow: bool=False) -> pd.DataFrame:
    """ Main function for extracting tracks and race information"""
    tracks = []
    tracks_links = []
    race_times = []
    race_numbers = []
    days = []
    wait = WebDriverWait(driver, 10)
    
    time.sleep(2)
    
    if tomorrow:
        button_selector = '[data-fs-title="page:racing-tab:tomorrow-header_bar"]'
    else:
        button_selector = '[data-fs-title="page:racing-tab:today-header_bar"]'
    
    click_race_date(driver, button_selector)
    click_race_date(driver, button_selector)
    
    # Wait for content to load before continuing
    time.sleep(10)
    
    # Number of Race Containers - There is usually 3 types of races (Gallops, Greyhounds, Harness)
    race_containers = get_race_containers(driver)
    
    for race_index in range(len(race_containers)):
        race_containers = get_race_containers(driver)
        race = race_containers[race_index]
        items = re_initalize_elements(race)
        
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
            except Exception:
                item = re_initalize_elements(race)[item_index]
                driver.execute_script("arguments[0].click();", re_initalize_elements(race)[item_index])
            hrefs, times, track_race_numbers, day = extract_race_urls(driver, tomorrow)
            for index in range(len(hrefs)):
                tracks.append(track)
                tracks_links.append(hrefs[index])
                race_times.append(times[index])
                race_numbers.append(track_race_numbers[index])
                days.append(day[index])
            

            
            time.sleep(2)
            button = driver.find_element(By.CSS_SELECTOR, button_selector)
            try:
                driver.execute_script("arguments[0].click();", button)
            except:
                button = driver.find_element(By.CSS_SELECTOR, button_selector)
                driver.execute_script("arguments[0].click();", button)
    
            
            # Wait until the page is back to the race container state
            wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "css-1d6i0xy-Tabs-Tabs-Tabs-Tabs-Tabs-Tabs")))
    
    return pd.DataFrame(data={"Track Name": tracks, "Track Links": tracks_links, "Race Time": race_times, "Race Number": race_numbers, 'Day': days})

def extract_market_prices(driver, track_name, race_number, other_race_data):
    """ Extract market prices Fixed(W) and Fixed(P) and calculates """
    data = {
        "Track": [],
        "Race Number": [],
        "Participant Name": [],
        "Fixed(W)": [],
        "Fixed(P)": [],
        "Market Price (%)": [],
        "Event Time": [],
    }
    race_items = driver.find_elements(By.CLASS_NAME, "css-1c8uam-ListItem-ListItem-ListItem-RaceSelectionsListItem-RaceSelectionsListItem-RaceSelectionsListItem-RaceSelectionsListItem")
    for participant in race_items:
        participant_element = participant.find_element(By.CSS_SELECTOR, '[data-fs-title*="racer_name"]')
        
        is_line_through = driver.execute_script(
            "return window.getComputedStyle(arguments[0]).textDecoration.includes('line-through');",
            participant_element
        )
        if is_line_through:
            # This indicates that the horse has been removed from the race (The name has a line-through style).
            continue
        participant_name = participant_element.text.strip()
        
        fixed_w_element = participant.find_element(By.CSS_SELECTOR, '[data-fs-title*="button:0-price_button"] span.eatknsg1')
        fixed_p_element = participant.find_element(By.CSS_SELECTOR, '[data-fs-title*="button:1-price_button"] span.eatknsg1')

        fixed_w_price = fixed_w_element.text.strip()
        fixed_p_price = fixed_p_element.text.strip()
        try:
            # Handling times where the Fixed(W) and Fixed(P) have not been set yet. 
            market_price = round(100 / float(fixed_w_price), 2)
        except:
            market_price=  None
        
        data["Track"].append(track_name)
        data["Event Time"].append(other_race_data["Race Time"])
        data["Race Number"].append(race_number)
        data["Participant Name"].append(participant_name)
        data["Fixed(W)"].append(fixed_w_price)
        data["Fixed(P)"].append(fixed_p_price)
        data["Market Price (%)"].append(market_price)
    
    return pd.DataFrame(data)
        
def find_race(driver: SafariWebDriver, race_data: pd.DataFrame) -> pd.DataFrame:
    random_race = random.randint(0, len(race_data) - 1)
    
    track_name = race_data.iloc[random_race]['Track Name']
    race_number = race_data.iloc[random_race]['Race Number']
    other_data = race_data.iloc[random_race]
    # Display for reference purposes.
    print(race_data.iloc[random_race])
    wait = WebDriverWait(driver, 10)
    
    button_selectors = ['[data-fs-title="page:racing-tab:today-header_bar"]', '[data-fs-title="page:racing-tab:tomorrow-header_bar"]']
    
    def get_anchors_with_retry(driver: SafariWebDriver, retries: int = 3) -> list[WebElement] | WebElement:
        for attempt in range(retries):
            try:
                anchors = driver.find_elements(By.TAG_NAME, "a")
                return anchors
            except StaleElementReferenceException:
                if attempt < retries - 1:
                    time.sleep(1)
                else:
                    raise
    
    def get_slides_with_retry(driver: SafariWebDriver, retries: int = 3) -> list[WebElement] | WebElement:
        for attempt in range(retries):
            try:
                wrapper = driver.find_element(By.CLASS_NAME, "css-1gtokez-RaceNav-RaceNav-RaceNav__CarouselItem-RaceNav-MeetingContainer-MeetingContainer__RaceNav-MeetingContainer")
                slides = wrapper.find_elements(By.CLASS_NAME, "swiper-slide")
                return slides
            except StaleElementReferenceException:
                if attempt < retries - 1:
                    time.sleep(1)
                else:
                    raise
    
    button_selector = button_selectors[0] if other_data["Day"] == "today" else button_selectors[1]
    click_race_date(driver, button_selector)
    time.sleep(10)
    
    anchors = get_anchors_with_retry(driver)
    
    for anchor_index in range(len(anchors)):
        try:
            title = anchors[anchor_index].get_attribute("title")
            if title == track_name:
                driver.execute_script("arguments[0].click();", anchors[anchor_index])
                wait.until(EC.presence_of_element_located((By.CLASS_NAME, "css-1gtokez-RaceNav-RaceNav-RaceNav__CarouselItem-RaceNav-MeetingContainer-MeetingContainer__RaceNav-MeetingContainer")))
                
                slides = get_slides_with_retry(driver)
                slide = slides[int(race_number) - 1]
                anchors = slide.find_element(By.TAG_NAME, "a")
                driver.execute_script("arguments[0].click();", anchors)
                return extract_market_prices(driver, track_name, race_number, other_data)
            else:
                continue
        except StaleElementReferenceException:
            # Re-fetch anchors and continue the loop
            anchors = get_anchors_with_retry(driver)
            
    raise RaceNotFoundException
    
    
if __name__ == "__main__":
    """ 
    1. Scrapes today races (AU/NZ).
    2. Scrapes tommmorw races (AU/NZ)
    3. Combines all races into df_races_data.csv
    4. Randomly selects a race from the csv file and returns a csv of market prices for participants in
    """
    response = establish_connection("https://getsetbet.com.au/racing/")
    response.implicitly_wait(60)
    df = extract_tracks(response)
    response.quit()
    
    response = establish_connection("https://getsetbet.com.au/racing/")
    response.implicitly_wait(60)
    df1 = extract_tracks(response, True)
    df2 = pd.concat([df, df1])
    df2.to_csv("df_races_data.csv", index=False)
    response.quit()
    
    response = establish_connection("https://getsetbet.com.au/racing/")
    response.implicitly_wait(60)
    race_data = pd.read_csv("df_races_data.csv")
    try:
        horse_data = find_race(response, race_data)
        horse_data.to_csv("df_performed_bets.csv", index=False)
    except RaceNotFoundException:
        print("Race not found")
    
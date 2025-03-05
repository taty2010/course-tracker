import os
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json

login_url = "/login/"
fem_url = "https://frontendmasters.com"
courses_url = "/my-account/library/started/"
course_page = "/courses/"

FEM_USERNAME = os.getenv("FEM_USERNAME")
FEM_PASSWORD = os.getenv("FEM_PASSWORD")

def get_default_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    return options

options = get_default_chrome_options()

def fem_login(browser):
  browser.get(fem_url + login_url)

  username_input = browser.find_element(By.ID, "username")
  username_input.send_keys(FEM_USERNAME)

  pwd_input = browser.find_element(By.ID, "password")
  pwd_input.send_keys(FEM_PASSWORD)

  submit = browser.find_element(By.XPATH, "//button[@type='submit']")
  submit.click()

course_list = []
def access_library(browser):
  fem_login(browser)
  browser.get(fem_url + courses_url)

  library_started = browser.find_elements(By.CLASS_NAME, "FM-Link")
  for courses in library_started:
    if courses.text != "":
      course_list.append({"name": courses.text, "course_link": courses.get_attribute("href")})
      browser.quit()

stats = []
with open('notionList.json', 'r') as file:
  notion_courseList = json.load(file)

# should be checking to see if course already exist in notion doc if it doesnt we parse through the links to get data
# will also check to see if course is set to watching. If it is will run a check for new data
notion = {}
def get_stats(browser):
  fem_login(browser)
  for notion_course in notion_courseList:
    notion.update({notion_course["name"]: {"watching": notion_course["watching"]}})
  
  with open('courseList.json', 'r') as file:
    fem_courseList = json.load(file)

  if notion_courseList:
    for course in fem_courseList:
      name = course["name"]
      if course["name"] not in notion.keys() or notion[name]['watching'] == True:
        browser.get(course["course_link"])
        percentage = browser.find_elements(By.CSS_SELECTOR, ".course-progress .stat div")
        time.sleep(1)
        for stat in percentage:
          stats.append(stat.text)
        updated_stats = dict(zip(stats[::2],stats[1::2]))
        course.update(updated_stats)
        browser.quit()
  else:
    browser.quit()
    print("Notion Course List not found")

def fem_flow():
  options = get_default_chrome_options()
  options.add_experimental_option("detach", True)

  browser = webdriver.Chrome(options=options)

  try:
    get_stats(browser)
  except:
    access_library(browser)
    with open("courseList.json", "w") as file:
      json.dump(course_list, file)
    print(f'Created new file: courseList.json')

from dotenv import load_dotenv
import os
import json
from notion_client import Client, AsyncClient
import asyncio

# Env variable
load_dotenv() # Load environment variables from .env file
NOTION_KEY = os.getenv("NOTION_KEY")
DATABASE_ID = os.getenv("DATABASE_ID")

notion = Client(auth=NOTION_KEY)
notionAsync = AsyncClient(auth=NOTION_KEY)

# Files
notion_file = "notionList.json"
fm_file = "courseList.json"

response = notion.databases.query(
  **{
    "database_id": DATABASE_ID,
  }
)

data = []
for item in response['results']:
  # test = str(item['properties']['Watching']['checkbox']).lower()
  prop = item['properties']
  if prop["Time Remaining"]["rich_text"] != []:
    time_remaining = prop["Time Remaining"]["rich_text"][0]["plain_text"]
  else:
    time_remaining = ""
  processed_data = {
    "name": prop['Name']['title'][0]['plain_text'],
    "watching": prop['Watching']['checkbox'],
    "Lessons Completed": prop["Lessons Completed"]["number"],
    "Lessons Remaining": prop["Lessons Remaining"]["number"],
    "Time Remaining": time_remaining,
    'id': item["id"]
  }
  data.append(processed_data)

# checking the Notion db with current notionList.json file for any changes. Only want to update file if there's been a change.
try:
  with open(notion_file) as file:
    current_data = json.load(file)
  if current_data != data:
    with open(notion_file, "w") as f:
      json.dump(data, f)
    print(f'Change in Notion data detected: Updated {notion_file}')
  else:
    print("No updates detected from Notion")
except:
  with open(notion_file, "w") as f:
    json.dump(data, f)
  print(f'Created new file: {notion_file}')

with open(fm_file) as file:
  fem_courseList = json.load(file)

async def create_page(d):
  await notionAsync.pages.create(
    **{
      "parent": {
        "type": "database_id",
        "database_id": DATABASE_ID 
      },
      "properties": {
        "Name": {
          "title": [
            {
              "text": {
                "content": d['name']
              }
            }
          ]
        },
        "Lessons Completed":{ "number": int(d['Lessons Completed'])},
        "Lessons Remaining": { "number": int(d['Lessons Remaining'])},
        "Time Remaining": { 
          "rich_text": [
            {
              "text": {
                "content": d['Time Remaining']
              }
            }
          ]
        }
      },
      "children": [],
    }
  )

async def update_page(id, completed, remaining, time):
  await notionAsync.pages.update(
    **{
      "page_id": id,
      "properties": {
        "Lessons Completed":{ "number": int(completed)},
        "Lessons Remaining": { "number": int(remaining)},
        "Time Remaining": { 
          "rich_text": [
            {
              "text": {
                "content": time
              }
            }
          ]
        }
      }
    }
  )

curr_name = {course['name'] for course in data}
new_name = {course['name'] for course in fem_courseList}
res = curr_name.intersection(new_name)

lessons_curr = {}
lessons_new = {}
for course in data:
  lessons_curr.update({course["name"]: {"completed": course["Lessons Completed"], "id": course["id"]}})

for course in fem_courseList:
  lessons_new.update({course["name"]: int(course["Lessons Completed"])})

async def check_course():
  for fem in fem_courseList:
    if fem['name'] not in res:
      await create_page(fem)
    if lessons_new[fem['name']] != lessons_curr[fem['name']]["completed"]:
      await update_page(lessons_curr[fem['name']]["id"],fem["Lessons Completed"], fem["Lessons Remaining"], fem["Time Remaining"])
  

asyncio.run(check_course())
import os
import json
import glob
from dotenv import load_dotenv
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

#we use pathlib for the file handling of importing the files 
from pathlib import Path

# we get the variables from the .env file (ADD this file to the gitignore ! never publish youre api keys !!! not even in a commit that you overwrite 
load_dotenv()

#then we set the CONSTS from those env file variables 
COSMOS_ENDPOINT = os.environ['COSMOS_ENDPOINT']
DATABASE_NAME = os.environ['DATABASE_NAME']
CONTAINER_NAME = os.environ['CONTAINER_NAME']

## now we setup the cosmosdb client connection using Azure AD
credential = DefaultAzureCredential()
client = CosmosClient(COSMOS_ENDPOINT, credential)

## we print the endpoint 
print(f"endpoint : {COSMOS_ENDPOINT}")

## cosmos db connectors
db_client = client.get_database_client(DATABASE_NAME)
container_client = db_client.get_container_client(CONTAINER_NAME)


items_dir  = Path("./items/")

for json_file in items_dir.glob("*.json"):
    if json_file.is_file():
        with open(json_file, "r") as file:
            book_data = json.load(file)
            try:
                result = container_client.upsert_item(book_data)
                print(f"Book '{book_data['title']}' upserted in category '{book_data['category']}'")
            except Exception as e:
                print(f"Error upserting {file.name}: {e}")
    
            



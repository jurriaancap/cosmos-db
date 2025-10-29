import os
from dotenv import load_dotenv
from azure.cosmos import CosmosClient
from azure.identity import DefaultAzureCredential

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


## now we loop through all databases uses list_database 
for db in client.list_databases():
    print(f" -- DATABASE: {db["id"]}")
    # and for each databse we get all the containers
    db_client = client.get_database_client(db)
    for container in db_client.list_containers():
        print(f'  -- Container: {container['id']}')
        ## now we get all items per container 
        container_client = db_client.get_container_client(container)
        for item in container_client.read_all_items():
            print(f"    -- item: {item["title"]}")

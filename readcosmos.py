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
db_client = client.get_database_client(DATABASE_NAME)
container_client = db_client.get_container_client(CONTAINER_NAME)

def list_all_db_items():
    ## now we loop through all databases uses list_database 
    for db in client.list_databases():
        print(f" -- DATABASE: {db["id"]}")
        # and for each databse we get all the containers
        
        for container in db_client.list_containers():
            print(f'  -- Container: {container['id']}')
            ## now we get all items per container 
            for item in container_client.read_all_items():
                print(f"    -- item: {item["HotelName"]} - type : {item["Category"]} - rating : {item["Rating"]} - hotelid : {item["HotelId"]} - documentid = {item["id"]} ")


# ## now we insert a new hotel (its hotel1 from the items but we do it manualy just for this example 
# # we also going to use a uuid to avoid duplicates just in case 
# new_hotel = {
#     "id": "300bf955-8637-4a34-b17f-e8a26ea0f30a",
#     "HotelId": "bbc5cab0-f342-44a0-9652-76751e46a758",
#     "HotelName": "Azure Bay Resort",
#     "Description": "Luxury beachfront resort offering panoramic sea views, fine dining, and a private beach.",
#     "Description_fr": "Complexe de luxe en bord de mer offrant une vue panoramique sur la mer, une cuisine raffinée et une plage privée.",
#     "Category": "Resort",
#     "Tags": ["beach", "spa", "pool"],
#     "ParkingIncluded": True,
#     "IsDeleted": False,
#     "LastRenovationDate": "2023-06-12T00:00:00Z",
#     "Rating": 4.1,
#     "Address": {
#       "StreetAddress": "25 Ocean Drive",
#       "City": "Miami",
#       "StateProvince": "FL",
#       "PostalCode": "33139",
#       "Country": "USA"
#     },
#     "Location": {
#       "type": "Point",
#       "coordinates": [-80.130045, 25.790654]
#     },
#     "Rooms": [
#       {
#         "Description": "Ocean View Suite, 1 King Bed",
#         "Description_fr": "Suite vue sur l'océan, 1 très grand lit",
#         "Type": "Suite",
#         "BaseRate": 349.99,
#         "BedOptions": "1 King Bed",
#         "SleepsCount": 2,
#         "SmokingAllowed": False,
#         "Tags": ["balcony", "jacuzzi tub", "tv"]
#       },
#       {
#         "Description": "Standard Room, 2 Double Beds",
#         "Description_fr": "Chambre standard, 2 lits doubles",
#         "Type": "Standard Room",
#         "BaseRate": 189.99,
#         "BedOptions": "2 Double Beds",
#         "SleepsCount": 4,
#         "SmokingAllowed": False,
#         "Tags": ["tv", "coffee maker"]
#       }
#     ]
#   }


### print(new_hotel)

## here we create a new item, if you run this script multiple tiems you get new items with a different id every time
# container_client.create_item(new_hotel)

## if we use upsert it either creates if missing or updates it 
# container_client.upsert_item(new_hotel)
#print(list_all_db_items())


# ## now we try updating a field instead of hte complete item
# # lets add a room 
# # first we select the hotel using the ID and category
# new_room = {
#         "Description": "Smoking Room, 2 Double Beds (Cityside)",
#         "Description_fr": "Chambre du smoke, 2 lits doubles (Cityside)",
#         "Type": "Budget Room",
#         "BaseRate": 86.99,
#         "BedOptions": "2 Double Beds",
#         "SleepsCount": 2,
#         "SmokingAllowed": True,
#         "Tags": [ "bathroom shower" ]
#       }

# hotel = container_client.read_item('300bf955-8637-4a34-b17f-e8a26ea0f30a',"Resort")
# ## show the current rooms 
# print(hotel["Rooms"])
# print("*****************************************")
# ## we update the hotel with the new room 
# hotel["Rooms"].append(new_room)
# ## and now we update the cosmos db item with the extra room 
# updated_hotel = container_client.replace_item(hotel["id"],hotel)

# ## now we read the item to check if the room is added
# print(f"updated rooms : {updated_hotel["Rooms"]}")
# ## if you want to make 100 % sure the item in cosmod db is the same (just in case someone updated it with something else after you ) you should do a read_item again, but this will be a read operation extra 
# print(f"real updated rooms : {container_client.read_item('300bf955-8637-4a34-b17f-e8a26ea0f30a',"Resort")["Rooms"]} ")



# ## delet item 
# ## first we list 
# print(list_all_db_items())
# ## then we delete one of the id and list again 
# container_client.delete_item("300bf955-8637-4a34-b17f-e8a26ea0f30a","Resort")
# print(list_all_db_items())


## lets select something using parameters and querys
# let filter by propperty

## we make a query where we select Category = budget
query = "SELECT * FROM  c WHERE c.Category = 'Budget' "

# put them in a list , make sure we sue partition_key="Budget" again or we need to enable enablecrosspartitio_Search= true
items = list(container_client.query_items(query, partition_key="Budget"))

for item in items:
    print(f"{item["HotelName"]}")

print(f"items found = {len(items)} from category Budget")

print("*********************************************************")


## however this is not very safe, so lets make a parameterised query , which is safer , so lets check for a rating of 4.8 or higher
query = "SELECT * FROM  c WHERE c.Rating >= @min_rating "
params = [{"name": "@min_rating", "value": 4.8 }]

# put them in a list , we are going to look accross partition in this case since we want all paritions 
items = list(container_client.query_items(query, params, enable_cross_partition_query=True))

for item in items:
    print(f"{item["HotelName"]} - { item["Category"]} - rating {item["Rating"]}")

print(f"items found = {len(items)} with a rating higher than Value: {params[0]['value']}") 

print("*********************************************************")


## lets do a project now where we only select certain fields , for example HotelId HotelName, Rating 
query = "SELECT c.HotelId, c.HotelName, c.Rating FROM  c WHERE c.Rating >= @min_rating "
params = [{"name": "@min_rating", "value": 4.8 }]

# put them in a list , we are going to look accross partition in this case since we want all paritions searches
items = list(container_client.query_items(query, params, enable_cross_partition_query=True))

for item in items:
    print(f"{item} -- onlyu 3 fields !")

print(f"items found = {len(items)} with a rating higher than Value: {params[0]['value']}")

print("*********************************************************")


## now we log into the tags and only select the hotels that have the  tag view  (hotels with a view) , since we arent sure if every tag is lowercase or not , we normalise both sides for comparison
query = "SELECT * FROM c WHERE EXISTS(SELECT VALUE tag FROM tag IN c.Tags WHERE LOWER(tag) = LOWER(@tag))"
params = [{"name": "@tag", "value": "View" }]

# put them in a list , we are going to look accross partition in this case since we want all paritions searches
items = list(container_client.query_items(query, params, enable_cross_partition_query=True))

for item in items:
    print(f"{item["HotelName"]} -has a view !!!")

print(f"{len(items)} hotel(s) hava a view {params[0]['value']}")


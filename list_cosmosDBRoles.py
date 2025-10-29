from azure.identity import DefaultAzureCredential
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from msgraph.graph_service_client import GraphServiceClient
import asyncio
import os
from dotenv import load_dotenv

# we load the environment variables from the .env file (ADD this file to the gitignore ! never publish youre api keys !!! not even in a commit that you overwrite 
load_dotenv()

## we load the variables from the env. please ensure that the env. is NEVER commited to a public repo. this holds youre private information 
SUBSCRIPTION_ID = os.environ['SUBSCRIPTION_ID']
RESOURCE_GROUP = os.environ['RESOURCE_GROUP']
ACCOUNT_NAME = os.environ['ACCOUNT_NAME']
DATABASE_NAME = os.environ['DATABASE_NAME']
CONTAINER_NAME = os.environ['CONTAINER_NAME']

## now we setup the credential for azure authentication using the default azure credential
credential = DefaultAzureCredential()
## then we create the cosmos client for management operations (not for data operations!)
cosmos_client = CosmosDBManagementClient(credential, SUBSCRIPTION_ID)


## here we have the helper functigon to look up the principal and match it against a user, sp or group
async def lookup_principal_details_async(principal_id, credential):
    """
    this function does lookup principal details using Microsoft Graph SDK (async version)
    we need this to convert the ugly GUID principal ids to human readable names
    """
    try:
        # we Initialize Graph client to talk to microsoft graph api
        graph_client = GraphServiceClient(credentials=credential)
        
        # first we Try to find if its a user 
        try:
            user = await graph_client.users.by_user_id(principal_id).get()
            if user:
                return {
                    "displayName": user.display_name or 'Unknown',
                    "email": user.mail or user.user_principal_name or 'No email',
                    "type": "User"
                }
        except Exception as e:
            print(f"    Debug: User lookup failed: {e}")
        
        # if not user, maybe its a service principal (like an application)
        try:
            sp = await graph_client.service_principals.by_service_principal_id(principal_id).get()
            if sp:
                return {
                    "displayName": sp.display_name or 'Unknown',
                    "email": sp.app_id or 'No email',
                    "type": "Service Principal"
                }
        except Exception as e:
            print(f"    Debug: Service Principal lookup failed: {e}")
        
        # if not service principal, maybe its a group
        try:
            group = await graph_client.groups.by_group_id(principal_id).get()
            if group:
                return {
                    "displayName": group.display_name or 'Unknown',
                    "email": group.mail or 'No email',
                    "type": "Group"
                }
        except Exception as e:
            print(f"    Debug: Group lookup failed: {e}")
        
        # if we reach here, we didnt find anything :(
        return {
            "displayName": "Not Found",
            "email": "Not Found", 
            "type": "Unknown"
        }
        
    except Exception as e:
        # something went wrong with the whole lookup
        return {
            "displayName": f"Error: {str(e)}",
            "email": "Error",
            "type": "Error"
        }


## i dunno, this i just copied from someone when i had some problems. 
def lookup_principal_details(principal_id, credential):
    """
    this is synchronous wrapper for the async Graph lookup
    because we cant use async in the main program flow easily
    """
    return asyncio.run(lookup_principal_details_async(principal_id, credential))

## get the name of the role , these are hardcoded !!! in cosmos db
def get_role_name(role_definition_id):
    """this function gets friendly role name from the ugly role definition ID"""
    if role_definition_id and role_definition_id.endswith("00000000-0000-0000-0000-000000000002"):
        return "Cosmos DB Built-in Data Contributor"
    elif role_definition_id and role_definition_id.endswith("00000000-0000-0000-0000-000000000001"):
        return "Cosmos DB Built-in Data Reader"
    else:
        return "Custom/Other Role"

# get the scope level from the container aname or datbase naem etc 
def get_scope_level(scope):
    """this function gets scope level description so we know what level the permission is"""
    if scope.endswith("/colls/" + CONTAINER_NAME):
        return "Container"
    elif scope.endswith("/dbs/" + DATABASE_NAME):
        return "Database"
    elif scope.endswith(ACCOUNT_NAME):
        return "Account"
    else:
        return "Other"


## here we start outputing stuff 
print("=== Cosmos DB Roles and Members ===")

# --- now we List all the role assignments from cosmos db ---
try:
    ## we get all the assignments from the cosmos db account
    assignments = cosmos_client.sql_resources.list_sql_role_assignments(RESOURCE_GROUP, ACCOUNT_NAME)
    
    # we Group assignments by role and scope so we can show them nicely organized
    roles_dict = {}
    
    ## we loop through each assignment to organize them
    for a in assignments:
        ## we get the friendly role name instead of the ugly GUID
        role_name = get_role_name(a.role_definition_id)
        ## we get the scope level so we know if its account, database or container level
        scope_level = get_scope_level(a.scope)
        ## we combine role name and scope to make a unique key
        role_key = f"{role_name} ({scope_level})"
        
        ## if this role+scope combination is new, we create a new entry
        if role_key not in roles_dict:
            roles_dict[role_key] = {
                'members': [],
                'scope': a.scope,
                'role_definition_id': a.role_definition_id
            }
        
        roles_dict[role_key] = {
                'members': [],
                'scope': a.scope,
                'role_definition_id': a.role_definition_id
            }
        
        # now we Lookup the principal details to get human readable name
        principal_info = lookup_principal_details(a.principal_id, credential)
        ## we create member info object with all the details
        member_info = {
            'principal_id': a.principal_id,
            'display_name': principal_info['displayName'],
            'email': principal_info['email'],
            'type': principal_info['type'],
            'assignment_id': a.name
        }
        
        # we check to Avoid duplicate members in same role (same person shouldnt appear twice in same role)

        if not any(m['principal_id'] == member_info['principal_id'] for m in roles_dict[role_key]['members']):
            roles_dict[role_key]['members'].append(member_info)
    
    # now we Display results grouped by role in a nice way
    for role_name, role_info in roles_dict.items():
        print(f"\n ROLE: {role_name}")
        # # i have excluded because its soo long 
        #print(f"   Scope: {role_info['scope']}")
        #print(f"   Role Definition: {role_info['role_definition_id']}")
        print(f"   Members ({len(role_info['members'])}):")
        
        ## we loop through each member of this role to show their details
        for member in role_info['members']:
            print(f"        {member['display_name']} ({member['type']})")
            print(f"        Email: {member['email']}")
            print(f"        Principal ID: {member['principal_id']}")
            print(f"        Assignment ID: {member['assignment_id']}")
            print()
        
        print("-" * 80)

except Exception as e:
    print(f"Error listing role assignments: {e}")
    print("\nMake sure you have the required permissions and the azure-mgmt-cosmosdb package installed")
    print("Install with: uv add azure-mgmt-cosmosdb")

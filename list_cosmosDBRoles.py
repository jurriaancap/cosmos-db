from azure.identity import DefaultAzureCredential
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from msgraph.graph_service_client import GraphServiceClient
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

## we load the variables from the env. please ensure that the env. is NEVER commited to a public repo. this holds youre private information 
SUBSCRIPTION_ID = os.environ['SUBSCRIPTION_ID']
RESOURCE_GROUP = os.environ['RESOURCE_GROUP']
ACCOUNT_NAME = os.environ['ACCOUNT_NAME']
DATABASE_NAME = os.environ['DATABASE_NAME']
CONTAINER_NAME = os.environ['CONTAINER_NAME']

credential = DefaultAzureCredential()
cosmos_client = CosmosDBManagementClient(credential, SUBSCRIPTION_ID)

async def lookup_principal_details_async(principal_id, credential):
    """
    Lookup principal details using Microsoft Graph SDK (async version)
    """
    try:
        # Initialize Graph client
        graph_client = GraphServiceClient(credentials=credential)
        
        # Try user first
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
        
        # Try service principal
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
        
        # Try group
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
        
        # Not found in any category
        return {
            "displayName": "Not Found",
            "email": "Not Found", 
            "type": "Unknown"
        }
        
    except Exception as e:
        return {
            "displayName": f"Error: {str(e)}",
            "email": "Error",
            "type": "Error"
        }

def lookup_principal_details(principal_id, credential):
    """
    Synchronous wrapper for the async Graph lookup
    """
    return asyncio.run(lookup_principal_details_async(principal_id, credential))

print("=== Cosmos DB Role Assignments ===")

# --- List role assignments ---
try:
    assignments = cosmos_client.sql_resources.list_sql_role_assignments(RESOURCE_GROUP, ACCOUNT_NAME)

    for a in assignments:
        print(f"Role Assignment ID: {a.name}")
        print(f"Principal ID: {a.principal_id}")
        
        # Lookup principal details
        principal_info = lookup_principal_details(a.principal_id, credential)
        print(f"Display Name: {principal_info['displayName']}")
        print(f"Email: {principal_info['email']}")
        print(f"Principal Type: {principal_info['type']}")
        
        print(f"Role Definition ID: {a.role_definition_id}")
        print(f"Scope: {a.scope}")
        
        # Check if it's the Data Contributor role
        if a.role_definition_id and a.role_definition_id.endswith("00000000-0000-0000-0000-000000000002"):
            print("Role Type: Cosmos DB Built-in Data Contributor")
        elif a.role_definition_id and a.role_definition_id.endswith("00000000-0000-0000-0000-000000000001"):
            print("Role Type: Cosmos DB Built-in Data Reader")
        else:
            print("Role Type: Custom/Other")
            
        print("-" * 60)

except Exception as e:
    print(f"Error listing role assignments: {e}")
    print("\nMake sure you have the required permissions and the azure-mgmt-cosmosdb package installed")
    print("Install with: pip install azure-mgmt-cosmosdb")

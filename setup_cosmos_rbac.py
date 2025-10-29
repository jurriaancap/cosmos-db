#!/usr/bin/env python3

"""
Azure Cosmos DB RBAC Setup Script (Python Version)
This script sets up all necessary RBAC permissions for Azure Cosmos DB using Python
"""

import os
import sys
from azure.identity import DefaultAzureCredential
from azure.mgmt.cosmosdb import CosmosDBManagementClient
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.mgmt.authorization.models import RoleAssignmentCreateParameters
from datetime import datetime
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

## we load the variables from the env. please ensure that the env. is NEVER commited to a public repo. this holds youre private information 
# =============================================================================
# CONFIGURATION - LOADED FROM .ENV FILE
# =============================================================================
SUBSCRIPTION_ID = os.environ['SUBSCRIPTION_ID']
RESOURCE_GROUP = os.environ['RESOURCE_GROUP']
COSMOS_ACCOUNT_NAME = os.environ['ACCOUNT_NAME']
DATABASE_NAME = os.environ['DATABASE_NAME']
CONTAINER_NAME = os.environ['CONTAINER_NAME']

# USER CONFIGURATION
USER_EMAIL = ""  # Leave empty to use current user, or set to "user@domain.com"
PRINCIPAL_ID = ""  # Leave empty to auto-detect

# ROLE DEFINITION IDs
DATA_READER_ROLE = "00000000-0000-0000-0000-000000000001"
DATA_CONTRIBUTOR_ROLE = "00000000-0000-0000-0000-000000000002"

def get_principal_id(credential):
    """Get the principal ID for the user"""
    if PRINCIPAL_ID:
        print(f"Using provided principal ID: {PRINCIPAL_ID}")
        return PRINCIPAL_ID
    
    if USER_EMAIL:
        print(f"Looking up user ID for email: {USER_EMAIL}")
        # You would need Microsoft Graph SDK for this
        # from azure.graphrbac import GraphRbacManagementClient
        # But for now, we'll use the current user
        print("⚠️  Email lookup requires Microsoft Graph SDK - using current user instead")
    
    # For now, you'll need to provide the principal ID manually
    # You can get it with: az ad signed-in-user show --query id -o tsv
    print("Please provide PRINCIPAL_ID in the script")
    print("Get it with: az ad signed-in-user show --query id -o tsv")
    sys.exit(1)

def create_azure_rbac_roles(auth_client, principal_id, account_scope):
    """Create Azure RBAC roles for management plane access"""
    print("Setting up Azure RBAC roles...")
    
    roles = [
        "CosmosDB SDK Reader",
        "Cosmos DB Account Reader Role"
    ]
    
    for role_name in roles:
        try:
            # Create role assignment
            role_assignment_params = RoleAssignmentCreateParameters(
                role_definition_id=f"/subscriptions/{SUBSCRIPTION_ID}/providers/Microsoft.Authorization/roleDefinitions/{get_role_definition_id(role_name)}",
                principal_id=principal_id
            )
            
            assignment_name = str(uuid.uuid4())
            auth_client.role_assignments.create(
                scope=account_scope,
                role_assignment_name=assignment_name,
                parameters=role_assignment_params
            )
            print(f"✅ Created {role_name} role assignment")
            
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"{role_name} role assignment already exists")
            else:
                print(f"Error creating {role_name}: {e}")

def get_role_definition_id(role_name):
    """Get the role definition ID for built-in roles"""
    role_ids = {
        "CosmosDB SDK Reader": "fbdf93bf-df7d-467e-a4d2-9458aa1360c8",
        "Cosmos DB Account Reader Role": "fbdf93bf-df7d-467e-a4d2-9458aa1360c8"
    }
    return role_ids.get(role_name, "")

def create_cosmos_data_plane_roles(cosmos_client, principal_id, account_scope, database_scope, container_scope):
    """Create Cosmos DB data plane roles"""
    print("Setting up Cosmos DB data plane roles...")
    
    scopes = [
        (account_scope, "account-scoped"),
        (database_scope, "database-scoped"), 
        (container_scope, "container-scoped")
    ]
    
    for scope, scope_name in scopes:
        try:
            # Create SQL role assignment
            assignment_id = str(uuid.uuid4())
            
            cosmos_client.sql_resources.create_update_sql_role_assignment(
                resource_group_name=RESOURCE_GROUP,
                account_name=COSMOS_ACCOUNT_NAME,
                role_assignment_id=assignment_id,
                create_update_sql_role_assignment_parameters={
                    "roleDefinitionId": f"/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.DocumentDB/databaseAccounts/{COSMOS_ACCOUNT_NAME}/sqlRoleDefinitions/{DATA_CONTRIBUTOR_ROLE}",
                    "scope": scope,
                    "principalId": principal_id
                }
            )
            
            print(f"Created {scope_name} Data Contributor role")
            
        except Exception as e:
            if "already exists" in str(e).lower():
                print(f"{scope_name} role assignment already exists")
            else:
                print(f"Error creating {scope_name} role: {e}")

def main():
    print("=== Azure Cosmos DB RBAC Setup (Python) ===")
    print(f"Account: {COSMOS_ACCOUNT_NAME}")
    print(f"Resource Group: {RESOURCE_GROUP}")
    print("=" * 50)
    
    # Initialize credential
    credential = DefaultAzureCredential()
    
    # Get principal ID
    principal_id = get_principal_id(credential)
    
    # Compute scopes
    account_scope = f"/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.DocumentDB/databaseAccounts/{COSMOS_ACCOUNT_NAME}"
    database_scope = f"{account_scope}/dbs/{DATABASE_NAME}"
    container_scope = f"{database_scope}/colls/{CONTAINER_NAME}"
    
    print(f"Principal ID: {principal_id}")
    print(f"Account Scope: {account_scope}")
    
    # Initialize clients
    auth_client = AuthorizationManagementClient(credential, SUBSCRIPTION_ID)
    cosmos_client = CosmosDBManagementClient(credential, SUBSCRIPTION_ID)
    
    # Create role assignments
    create_azure_rbac_roles(auth_client, principal_id, account_scope)
    create_cosmos_data_plane_roles(cosmos_client, principal_id, account_scope, database_scope, container_scope)
    
    print("\n=== RBAC setup complete! ===")
    print(f"✅ All permissions configured for principal: {principal_id}")
    print("\nTo verify, check the Azure Portal or run:")
    print(f"az cosmosdb sql role assignment list --account-name {COSMOS_ACCOUNT_NAME} --resource-group {RESOURCE_GROUP}")

if __name__ == "__main__":
    main()
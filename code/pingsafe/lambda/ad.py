import os
import msal
import requests
import yaml

from pprint import pprint

msal_auth_base_url = "https://login.microsoft.com/"
msal_auth_scope_list = ["https://graph.microsoft.com/.default"]
azuread_base_url = "https://graph.microsoft.com/"

'''
fetches the auth token for authenticating with Azure AD
list used for differentiating between human users and service accounts
'''
def get_auth_token():
  # Scope list for requested token
  scope = msal_auth_scope_list

  # Get auth credentials from env variables ( configured in Lambda function )
  tenantid = os.environ.get('TENANT_ID')
  clientid = os.environ.get('CLIENT_ID')
  secret = os.environ.get('CLIENT_SECRET')

  authority = msal_auth_base_url + tenantid

  # Construct a confidential client application
  app = msal.ConfidentialClientApplication(
    clientid, authority=authority,
    client_credential=secret,
  )

  # Acquire token for current confidential client
  result = app.acquire_token_for_client(scopes=scope)

  if "access_token" in result:
    return result['access_token']

'''
fetches the users from 'devops' AD group
in case the Azure credentials don't work, update this to use the get_group_users_from_yaml to get static users list from k8s configmap
'''
def get_group_users():
  return get_group_users_from_ad()

'''
fetches the users from 'devops' group as a list
'''
def get_group_users_from_ad():
  token = get_auth_token()
  bearer_token = 'Bearer ' + token
  headers = {
    "Content-Type": "application/json",
    "Authorization": bearer_token,
  }

  # devops group id
  group_id='DEVOPS_GROUP_ID'

  url = azuread_base_url + "v1.0/groups/" + group_id + "/members"
  res = requests.get(url, headers=headers).json()

  dat = res['value']

  ret = []
  for j in dat:
    assert(j['mail'] == j['userPrincipalName'])
    ret.append(j['mail'].replace('@razorpay.com',''))
  print(ret)
  return ret

def get_group_users_from_yaml():
  ret = []
  with open('/app/config/users.yaml') as f:
    data = yaml.safe_load(f)
    ret = [j for j in data['devops']]

  return ret

if __name__ == '__main__':
  ret = get_group_users_from_ad()
  print(len(ret))
  pprint(ret)
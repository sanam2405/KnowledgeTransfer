import os, requests, json, boto3

def send_slack(msg):
  slack_hook = os.environ['SLACK_HOOK_URL']
  payload = {"text": msg, "channel": "#pingsafe-alerts"}
  requests.post(slack_hook, json.dumps(payload))

'''
input: Array / List
output:
```
arr[0]
arr[1]..
```
check #pingsafe-alerts channel for details
'''
def format(arr):
  return "```" + '\n'.join(arr) + "```"

'''
mode can be 'newResources' or 'affectedResources'
newResources: will contain all the new resources that got generated in a particular event
affectedResources: will contain all resources
'''
MODE=os.environ['MODE']

'''
Allowed services that the lambda can assume ( ec2,iam right now)
Define to restrict lambda from defining boto3 clients other than the defined ones
if we want to do something with sns ( boto3.client('sns') for eg ) with lambda, this lambda env variable needs to be updated to ec2,iam,sns
'''
services = (os.environ['ALLOWED_SERVICES']).split(',')

'''
Pingsafe sends event in a single json

the event json object contains findings
from all accounts under the pingsafe project

function maps the account with respective findings
ret['acc1'] = [{finding1}, {finding2}]
ret['acc2'] = [{finding1}, {finding2}]
'''
def sort_into_accs(event):
  assert (MODE == "affectedResources" or MODE == "newResources")

  findings = event[MODE]
  accounts = [j['accountTitle'] for j in findings]
  accounts = list(set(accounts))

  ret = {}
  for j in accounts:
    account = j.replace('-', '_')
    # mp_resolved[account] = {}
    ret[account] = []
    for finding in findings:
      if (finding['accountTitle']).replace('-', '_') == account:
        ret[account].append(finding)

  return ret

'''
input: role_arn
assumes the given role and returns dict of temporary aws access credentials
'''
def get_creds(role_arn):
  role_name = role_arn.split("/")[1]

  sts_client = boto3.client('sts')

  assumed_role_object = sts_client.assume_role(
    RoleArn         = role_arn,
    RoleSessionName = "boto3-lambda-{}".format(role_name),
  )

  temp_credentials = assumed_role_object['Credentials']
  return temp_credentials

'''
input: service(ec2, iam etc), role_arn
returns a boto3 client for the specified service using the role credentials
'''
def get_client(service, role_arn):
  assert(service in services)
  creds = get_creds(role_arn)

  client = boto3.client(
    service,
    aws_access_key_id     = creds['AccessKeyId'],
    aws_secret_access_key = creds['SecretAccessKey'],
    aws_session_token     = creds['SessionToken']
  )
  return client

'''
List of env vars that are required before the lambda can run properly
Lambda exits if it doesn't find any of the specified env vars
'''
def validate_env_vars():
  try:
    AWS_IAM_ACCESS_KEYS_LAST_USED_THRESHOLD=(int)(os.environ['AWS_IAM_ACCESS_KEYS_LAST_USED_THRESHOLD'])
    tenantid = os.environ.get('TENANT_ID')
    clientid = os.environ.get('CLIENT_ID')
    secret = os.environ.get('CLIENT_SECRET')
    slack_hook = os.environ['SLACK_HOOK_URL']
    UNUSED_IAM_ROLES_THRESHOLD=(int)(os.environ['UNUSED_IAM_ROLES_THRESHOLD'])
    IAM_USERS_EXCEPTIONS=os.environ['IAM_USERS_EXCEPTIONS']
  except Exception as e:
    print("Ensure the following Environment Variables are present:\n\n")
    arr = [
      "AWS_IAM_ACCESS_KEYS_LAST_USED_THRESHOLD",
      "TENANT_ID",
      "CLIENT_ID",
      "CLIENT_SECRET",
      "SLACK_HOOK_URL",
      "UNUSED_IAM_ROLES_THRESHOLD",
      "IAM_USERS_EXCEPTIONS"
    ]
    print('\n'.join(arr))
    exit(0)

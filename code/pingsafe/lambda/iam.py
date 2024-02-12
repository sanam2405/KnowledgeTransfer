import boto3
import os

from pprint import pprint
from datetime import datetime

from common import *
from ad import get_group_users

AWS_IAM_ACCESS_KEYS_LAST_USED_THRESHOLD=(int)(os.environ['AWS_IAM_ACCESS_KEYS_LAST_USED_THRESHOLD']) # in days
UNUSED_IAM_ROLES_THRESHOLD=(int)(os.environ['UNUSED_IAM_ROLES_THRESHOLD']) # in days

'''
this will get the DevOps users
can be modified to fetch list of all users after validating if the token has permissions

this is used when there are access keys to be disabled and we want to make sure we dont disable / delete service accounts
which can cause outages
'''
once = []
def get_human_users():
    global once
    if len(once) > 0:
        return once
    once = get_group_users()
    return once

'''
input: username, accesskeyid
deactivates the IAM access key pair with the specified AccessKeyId and then deletes the pair
'''
def delete_access_key(iam_client, username, accesskeyid):
  iam_client.update_access_key(
      UserName=username,
      AccessKeyId=accesskeyid,
      Status='Inactive'
  )
  iam_client.delete_access_key(
      UserName=username,
      AccessKeyId=accesskeyid
  )

'''
input:
pingsafe_event - list of items with each item in the following format
{
    'accountTitle': 'RZP-AWS-Prod'
    'resourceId': 'IAMUserName',
    'createDate': 'xxx',
    'AccessKeyId: 'xxx'
}
role_to_assume: Account in which these Access Keys are present
result: Removes the specified Access Keys after validating the key pair has not been used in days (limit: AWS_IAM_ACCESS_KEYS_LAST_USED_THRESHOLD)
'''
def remediate_aws_iam_access_keys_last_used(pingsafe_event, role_to_assume):
    '''
    since the finding is related to IAM, only action on human users
    this is to ensure we dont touch bot / service accounts which can cause downtime
    '''
    allowed_to_action = get_human_users()
    print("IAM Keys might be Deactivated on the following users: ", allowed_to_action)

    accountname = pingsafe_event[0]['accountTitle'].replace('-', '_')

    disabled_access_keys = []
    iam_client = get_client("iam", role_to_assume)
    for j in pingsafe_event:
        iam_user_name = j['resourceId']

        if iam_user_name not in allowed_to_action:
            continue

        # print("Disable unused Access Keys for user: {}".format(iam_user_name))
        paginator = iam_client.get_paginator('list_access_keys')
        for response in paginator.paginate(UserName=iam_user_name):
            for acc in response['AccessKeyMetadata']:
                access_key_id = acc['AccessKeyId']
                resp = iam_client.get_access_key_last_used(
                    AccessKeyId=access_key_id
                )
                
                # AccessKey is used atleast once
                if 'AccessKeyLastUsed' in resp.keys():
                    if 'LastUsedDate' in resp['AccessKeyLastUsed'].keys():
                        dt_access_key_last_used = (resp['AccessKeyLastUsed']['LastUsedDate']).replace(tzinfo=None)
                    dt_now = datetime.now()

                    if (dt_now - dt_access_key_last_used).days > AWS_IAM_ACCESS_KEYS_LAST_USED_THRESHOLD:
                        delete_access_key(iam_client, iam_user_name, access_key_id)
                        disabled_access_keys.append("{}: {}".format(iam_user_name, access_key_id))

                # Access Key created but never used
                elif 'ServiceName' in resp['AccessKeyLastUsed'].keys() and resp['AccessKeyLastUsed']['ServiceName'] == 'N/A':
                    # list all access keys of this user
                    resp2 = iam_client.list_access_keys(UserName=iam_user_name)
                    if 'AccessKeyMetadata' in resp2.keys():
                        tmp = [j['CreateDate'] for j in resp2['AccessKeyMetadata'] if j['AccessKeyId'] == access_key_id]
                        if len(tmp) > 0:
                            create_date = tmp[0].replace(tzinfo=None)
                            dt_now = datetime.now()
                            if (dt_now - create_date).days > AWS_IAM_ACCESS_KEYS_LAST_USED_THRESHOLD:
                                delete_access_key(iam_client, iam_user_name, access_key_id)
                                disabled_access_keys.append("{}: {}".format(iam_user_name, access_key_id))

    if len(disabled_access_keys) > 0:
        send_slack("{}: Deleted Access Keys\n".format(accountname) + format(disabled_access_keys))


'''
input:
pingsafe_event - list of the following items
{
    'accountTitle': '',
    'resourceID': '<username>'
}
result: delete aws console login profile for the specified user
'''
def remediate_aws_iam_userpassword_last_used(pingsafe_event, role_to_assume):
    iam_client = get_client("iam", role_to_assume)
    deleted_profiles = []

    # these might be external users like hitachi, mindeed which we don't want to disable
    # rest we can disable as these are console passwords
    accountname = pingsafe_event[0]['accountTitle'].replace('-', '_')
    exceptions = os.environ['IAM_USERS_EXCEPTIONS'].replace('"', '').split(',')
    print("These users are ignored: ", exceptions)

    for j in pingsafe_event:
        user_name = j['resourceId']
        print("to be deleted: {}".format(user_name))
        if user_name in exceptions:
            continue
        try:
            iam_client.delete_login_profile(UserName = user_name)
            print("Deleted Login profile for user: {}".format(user_name))
            deleted_profiles.append(user_name)
        except Exception as e:
            print(e)
            continue

    if len(deleted_profiles) > 0:
        send_slack("Account: {}\n\n".format(accountname) + "Deleted Login Profiles for users (password not used in 90 days):\n" + format(deleted_profiles))

'''
Doesn't do much as there are service accounts
Landing Zone automatically rotates access keys so this might not be very useful. maybe for other accounts
'''
def remediate_aws_iam_accesskeys_not_rotated(pingsafe_event, role_to_assume):
    allowed_to_action = get_human_users()

    ret = []
    accountid = role_to_assume.split(':')[4]
    for j in pingsafe_event:
        print(j)
        if j['resourceId'] not in allowed_to_action:
            continue

        print("{}/{}, Please rotate access keys".format(j['accountTitle'], j['resourceId']))
        ret.append("{}/{}".format(j['accountTitle'], j['resourceId']))
    if len(ret) > 0:
        send_slack("AccountID: {}\n\n".format(accountid) + '\n'.join(ret) + '\nDisabled Access Keys ^^')

'''
doesn't do much right now
TODO: update this function to attach EnforceMFA policy to all the users in this list
'''
def remediate_aws_iam_users_mfa_disabled(pingsafe_event, role_to_assume):
    allowed_to_action = get_human_users()
    accountid = role_to_assume.split(":")[4]
    for j in pingsafe_event:
        print(j)
        if j['resourceId'] not in allowed_to_action:
            continue
        send_slack("AccountID: {}\n\n".format(accountid) + "Please Enable MFA: {} in {}".format(j['resourceId'], j['accountTitle']))

'''
input: pingsafe_event - list of the following items
{
    'accountTitle': '',
    'resourceID': '<groupname>'
}
result: confirm the groups are empty, remove their policies and delete these groups
'''
def remediate_aws_iam_empty_groups(pingsafe_event, role_to_assume):
    iam_client = get_client("iam", role_to_assume)

    accountname = pingsafe_event[0]['accountTitle'].replace('-', '_')
    deleted_groups = []

    for j in pingsafe_event:
        group_name = j['resourceId']
        print("Deleting Empty IAM Group: {}".format(group_name))
        try:
          ret_inline_policies = iam_client.list_group_policies(GroupName=group_name)
          if 'PolicyNames' in ret_inline_policies.keys():
              for k in ret_inline_policies['PolicyNames']:
                  iam_client.delete_group_policy(GroupName=group_name, PolicyName=k)

          ret_attached_policies = iam_client.list_attached_group_policies(GroupName=group_name)
          if 'AttachedPolicies' in ret_attached_policies.keys():
              for k in ret_attached_policies['AttachedPolicies']:
                  iam_client.detach_group_policy(PolicyArn=k['PolicyArn'], GroupName=group_name)

          iam_client.delete_group(GroupName = group_name)
          deleted_groups.append(group_name)
        except Exception as e:
            pass

    if len(deleted_groups) > 0:
        send_slack("Account: {}\n\n".format(accountname) + 'Deleted Empty IAM Groups:\n' + format(deleted_groups))

'''
helper function to delete an IAM role
please do all required checks before invoking this function
'''
def delete_role(iam_client, role_name):
    ret_inline_policies=iam_client.list_role_policies(RoleName=role_name)
    if 'PolicyNames' in ret_inline_policies.keys():
        for k in ret_inline_policies['PolicyNames']:
            iam_client.delete_role_policy(RoleName=role_name, PolicyName=k)

    ret_attached_policies=iam_client.list_attached_role_policies(RoleName=role_name)
    if 'AttachedPolicies' in ret_attached_policies.keys():
        for k in ret_attached_policies['AttachedPolicies']:
            iam_client.detach_role_policy(PolicyArn=k['PolicyArn'], RoleName=role_name)
    iam_client.delete_role(RoleName=role_name)

'''
helper function to delete instance profile
'''
def delete_instance_profile(iam_client, ip_name):
  print("Deleting instance profile: {}".format(ip_name))
  ret = iam_client.get_instance_profile(InstanceProfileName=ip_name)
  if 'InstanceProfile' in ret.keys() and 'Roles' in ret['InstanceProfile'].keys():
    for k in ret['InstanceProfile']['Roles']:
      role_name_2=k['Arn'].split('/')[-1]
      # assert(role_name==role_name_2)
      iam_client.remove_role_from_instance_profile(InstanceProfileName=ip_name,RoleName=role_name_2)
  iam_client.delete_instance_profile(InstanceProfileName=ip_name)


'''
helper function to get all instance profiles that are active from all ec2 instances
'''
def get_instance_profiles(ec2_client, token = "-1"):
    ret_tmp = None
    if token == "-1":
        ret_tmp = ec2_client.describe_instances()
    else:
        ret_tmp = ec2_client.describe_instances(NextToken=token)

    ret = []
    for j in ret_tmp['Reservations']:
        ret += [ k['IamInstanceProfile']['Arn'] for k in j['Instances'] if ('IamInstanceProfile' in k.keys() and 'Arn' in k['IamInstanceProfile'].keys()) ]

    if 'NextToken' in ret_tmp.keys():
        ret += get_instance_profiles(ret_tmp['NextToken'])

    ret = [j.split('/')[1] for j in ret]

    return list(set(ret))

'''
input: pingsafe_event - list of the below items
{
    'accountTitle': '',
    'resourceID': '<rolename>'
}
result: Deletes some of the roles in the event based on a criteria: role_last_used more than UNUSED_IAM_ROLES_THRESHOLD ago
'''
def remediate_unused_iam_roles(pingsafe_event, role_to_assume):
    # pprint(len(pingsafe_event['affectedResources']))
    slack_msg = []
    iam_client = get_client("iam", role_to_assume)
    ec2_client = get_client('ec2', role_to_assume)
    
    accountname = pingsafe_event[0]['accountTitle'].replace('-', '_')

    instance_profiles_active_list = get_instance_profiles(ec2_client)

    for j in pingsafe_event:
        role_name = j['resourceId']
        try:
          role_data = iam_client.get_role(RoleName = role_name)
        except iam_client.exceptions.NoSuchEntityException as e:
            continue

        if 'Role' in role_data.keys() and 'RoleLastUsed' in role_data['Role'].keys():
            
            # Ignore service roles, there are AWS created roles which cant be deleted
            if 'Path' in role_data['Role'].keys() and 'service-role/' in role_data['Role']['Path']:
                continue

            # get role last used date, get the creation date if role is never used after creation
            if 'LastUsedDate' in role_data['Role']['RoleLastUsed'].keys():
                dt = (role_data['Role']['RoleLastUsed']['LastUsedDate']).replace(tzinfo=None)
            elif len(role_data['Role']['RoleLastUsed'].keys()) == 0:
                dt = (role_data['Role']['CreateDate']).replace(tzinfo=None)

            dt_now = datetime.now()

            # only proceed if this role has not been used in the threshold
            if (dt_now - dt).days >= UNUSED_IAM_ROLES_THRESHOLD:
                # attempt to delete this role
                try:
                  delete_role(iam_client, role_name)
                  slack_msg.append("IAM Role: {}, Last Used: {} days ago".format(role_name, (dt_now - dt).days))

                except iam_client.exceptions.DeleteConflictException as e1:
                    if role_name in instance_profiles_active_list:
                        # dont do anything if the instance profile with the specified role is active
                        continue

                    # Error in deleting Role means there might be an instance profile attached to this role
                    role_instance_profile_data = iam_client.list_instance_profiles_for_role(RoleName=role_name)
                    role_active = False
                    if 'InstanceProfiles' in role_instance_profile_data.keys():
                        for prof in role_instance_profile_data['InstanceProfiles']:
                            if prof['InstanceProfileName'] not in instance_profiles_active_list:
                                delete_instance_profile(iam_client, prof['InstanceProfileName'])
                                slack_msg.append("Instance Profile: {}".format(prof['InstanceProfileName']))
                            else:
                                role_active = True
                    
                    # attempt to delete role again, since we've deleted the associates instance profile
                    if not role_active:
                        delete_role(iam_client, role_name)
                        slack_msg.append("IAM Role: {}, Last Used: {} days ago".format(role_name, (dt_now - dt).days))

                except iam_client.exceptions.UnmodifiableEntityException as e2:
                    print(e2)

    if len(slack_msg) > 0:
        send_slack('{}: Deleted IAM Roles\n'.format(accountname) + format(slack_msg))

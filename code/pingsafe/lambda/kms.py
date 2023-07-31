import boto3
import os
from common import *

'''
input:
pingsafe_event - list of the following items
{
    'resourceType': '<resource_type',
    'resourceID': '<resource_id>'
}
result: enable key rotation if it was disabled previously
'''
def remediate_kms_key_rotation(pingsafe_event, role_to_assume):

    # Get the AWS Account Name
    accountname = pingsafe_event[0]['accountTitle'].replace('-', '_')
    
    # List to store the ARNs of modified KMS keys
    modified_resources = []

    try:
        kms_client = get_client("kms", role_to_assume)

        # Iterate through each KMS key in the pingsafe_event list
        for kms_data in pingsafe_event:
            if kms_data["resourceType"] == "AWS::KMS::Key":
                
                print("Trying to enable key rotation for KMS key:", kms_data["resourceId"])

                # Enable key rotation for the KMS key
                kms_client.enable_key_rotation(
                    KeyId=kms_data["resourceId"]
                )

                # Add the ARN of the modified KMS key to the modified_resources list
                print("Enabled key rotation for KMS key:", kms_data["resourceId"])
                modified_resources.append(kms_data["resourceId"])

    except Exception as e:
        print("The error is ", e)

    # Check if any KMS keys were modified and send the list as a Slack message
    if len(modified_resources) > 0:
        send_slack('{}: Enabled Key Rotation for KMS keys:\n'.format(accountname) + format(modified_resources))
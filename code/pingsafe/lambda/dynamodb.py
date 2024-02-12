import boto3
import os
from common import *

"""
input:
pingsafe_event - list of the following items
{
    'resourceType': '<resource_type',
    'resourceID': '<resource_id>'
}
result: enable continuous if it was disabled previously
"""


def remediate_dynamodb_continuous_backups(pingsafe_event, role_to_assume):

    # Get the AWS Account Name
    accountname = pingsafe_event[0]["accountTitle"].replace("-", "_")

    # List to store the ARNs of modified DynamoDB tables
    modified_resources = []

    try:
        dynamodb_client = get_client("dynamodb", role_to_assume)

        # Iterate through each DynamoDB table in the pingsafe_event list
        for table_data in pingsafe_event:
            if table_data["resourceType"] == "AWS::DynamoDB::Table":

                table_name = table_data["resourceId"]

                # Lambda doesn't support remediation for AWS:DynamoDB:dynamoContinuousBackupsNotEnabled

                print("Trying to modify DynamoDB table:", table_name)

                # Enable continuous backups for the DynamoDB table
                dynamodb_client.update_continuous_backups(
                    TableName=table_name,
                    PointInTimeRecoverySpecification={
                        "PointInTimeRecoveryEnabled": True
                    },
                )

                # Add the ARN of the modified DynamoDB table to the modified_resources list
                print("Modified DynamoDB table:", table_name)
                modified_resources.append(table_name)

    except Exception as e:
        print("The error is ", e)

    # Check if any DynamoDB tables were modified and send the list as a Slack message
    if len(modified_resources) > 0:
        send_slack(
            "{}: Enabled DynamoDB Continuous Backups on:\n".format(accountname)
            + format(modified_resources)
        )

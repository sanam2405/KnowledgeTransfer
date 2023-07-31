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
result: enable deletion protection if it was disabled previously
'''
def remediate_elb_deletion_protection_not_enabled(pingsafe_event, role_to_assume):

     # Get the AWS Account Name
    accountname = pingsafe_event[0]['accountTitle'].replace('-', '_')
    
    # List to store the ARNs of modified ELBs
    modified_resources = []

    try:
        elbv2_client = get_client("elbv2", role_to_assume)

        # Iterate through each ELB in the pingsafe_event list
        for elb_data in pingsafe_event:
            if elb_data["resourceType"] == "AWS::ELB::LoadBalancer":
                # Describe the ELB to get its details
                response = elbv2_client.describe_load_balancers(
                    Names=[elb_data["resourceId"]]
                )
                elb_description = response['LoadBalancers'][0]

                # Get the Load Balancer ARN from the response
                load_balancer_arn = elb_description['LoadBalancerArn']

                print("Trying to modify ELB:", load_balancer_arn)

                # Enable deletion protection for the ELB
                elbv2_client.modify_load_balancer_attributes(
                    LoadBalancerArn=load_balancer_arn,
                    Attributes=[
                        {
                            "Key": "deletion_protection.enabled",
                            "Value": "true"
                        }
                    ]
                )

                # Add the ARN of the modified ELB to the modified_resources list
                print("Modified ELB:", load_balancer_arn)
                modified_resources.append(load_balancer_arn)

    except Exception as e:
        print("The error is ", e)

    # Check if any ELBs were modified and send the list as a Slack message
    if len(modified_resources) > 0:
        send_slack('{}: Enabled ELB Deletion Protection on:\n'.format(accountname) + format(modified_resources))
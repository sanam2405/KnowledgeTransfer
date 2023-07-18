'''

List all the Elastic Load Balancers that 
do not have Deletion Protection enabled

'''
import boto3

def get_elb_client():
    return boto3.client('elbv2')

def get_non_protected_elbs():
    elb_client = get_elb_client()
    response = elb_client.describe_load_balancers()

    non_protected_elbs = []
    for elb in response['LoadBalancers']:
        if not elb.get('DeletionProtection', False):
            non_protected_elbs.append(elb['LoadBalancerArn'])

    return non_protected_elbs

def main():
    non_protected_elbs = get_non_protected_elbs()

    if non_protected_elbs:
        print("Elastic Load Balancers without deletion protection:")
        for elb_arn in non_protected_elbs:
            print(elb_arn)
    else:
        print("No Elastic Load Balancers found without deletion protection.")

if __name__ == '__main__':
    main()

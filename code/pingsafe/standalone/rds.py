'''

List all the RDS database instances that do not 
have Deletion Protection Enabled

'''

import boto3

def get_rds_instances():
    rds = boto3.client('rds')
    response = rds.describe_db_instances()

    instances = response['DBInstances']
    while 'Marker' in response:
        response = rds.describe_db_instances(Marker=response['Marker'])
        instances.extend(response['DBInstances'])

    return instances

def list_instances_without_deletion_protection(instances):
    print("RDS Instances without Deletion Protection:")

    for instance in instances:
        if not instance['DeletionProtection']:
            print(f"Instance Identifier: {instance['DBInstanceIdentifier']}")
            print(f"Engine: {instance['Engine']}")
            print("------")

def main():
    rds_instances = get_rds_instances()
    list_instances_without_deletion_protection(rds_instances)

if __name__ == '__main__':
    main()

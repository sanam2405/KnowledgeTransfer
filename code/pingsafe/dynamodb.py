'''

List all the DynamoDB Instances where
continuous backups are not enabled

'''
import boto3

def get_dynamodb_client():
    return boto3.client('dynamodb')

def get_non_continuous_backup_tables():
    dynamodb_client = get_dynamodb_client()
    response = dynamodb_client.list_tables()

    non_continuous_backup_tables = []
    for table_name in response['TableNames']:
        table_description = dynamodb_client.describe_table(TableName=table_name)
        if not table_description['Table'].get('ContinuousBackupsDescription', {}).get('PointInTimeRecoveryDescription', {}).get('PointInTimeRecoveryStatus'):
            non_continuous_backup_tables.append(table_name)

    return non_continuous_backup_tables

def main():
    non_continuous_backup_tables = get_non_continuous_backup_tables()

    if non_continuous_backup_tables:
        print("DynamoDB tables without continuous backups enabled:")
        for table_name in non_continuous_backup_tables:
            print(table_name)
    else:
        print("No DynamoDB tables found without continuous backups enabled.")

if __name__ == '__main__':
    main()

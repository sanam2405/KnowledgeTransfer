import boto3

def get_iam_users():
    iam = boto3.client('iam')
    response = iam.list_users()

    users = response['Users']
    while response['IsTruncated']:
        response = iam.list_users(Marker=response['Marker'])
        users.extend(response['Users'])

    return users

def print_iam_users(users):
    print("IAM Users:")
    for user in users:
        print(f"Username: {user['UserName']}")
        print(f"User ID: {user['UserId']}")
        print("------")

def main():
    iam_users = get_iam_users()
    print_iam_users(iam_users)

if __name__ == '__main__':
    main()

"""

List all the IAM Users that do not have 
Multi Factor Authentication (MFA) enabled

"""
import boto3


def get_iam_users():
    iam = boto3.client("iam")
    response = iam.list_users()

    users = response["Users"]
    while response["IsTruncated"]:
        response = iam.list_users(Marker=response["Marker"])
        users.extend(response["Users"])

    return users


def list_users_without_mfa(users):
    print("IAM Users without MFA Active:")

    for user in users:
        username = user["UserName"]
        mfa_devices = boto3.client("iam").list_mfa_devices(UserName=username)[
            "MFADevices"
        ]
        if not mfa_devices:
            print(f"Username: {username}")
            print("------")


def main():
    iam_users = get_iam_users()
    list_users_without_mfa(iam_users)


if __name__ == "__main__":
    main()

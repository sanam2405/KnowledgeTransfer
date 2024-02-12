"""

List all the Keys where
KMS Key rotation is not enabled

"""
import boto3


def get_kms_client():
    return boto3.client("kms")


def get_non_rotated_keys():
    kms_client = get_kms_client()
    response = kms_client.list_keys()

    non_rotated_keys = []
    for key_id in response["Keys"]:
        key_metadata = kms_client.describe_key(KeyId=key_id["KeyId"])
        if "KeyMetadata" in key_metadata:
            key_rotation_enabled = key_metadata["KeyMetadata"].get(
                "KeyRotationEnabled", False
            )
            if not key_rotation_enabled:
                non_rotated_keys.append(key_id["KeyId"])

    return non_rotated_keys


def main():
    non_rotated_keys = get_non_rotated_keys()

    if non_rotated_keys:
        print("KMS keys without key rotation enabled:")
        for key_id in non_rotated_keys:
            print(key_id)
    else:
        print("No KMS keys found without key rotation enabled.")


if __name__ == "__main__":
    main()

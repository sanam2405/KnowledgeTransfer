import base64
import hashlib
import json
import os
import requests

import boto3

from pprint import pprint
from datetime import datetime
from common import sort_into_accs, validate_env_vars

import handlers

API_KEY = os.environ.get("PINGSAFE_API_KEY")

RESPONSE_CODES = {
    "METHOD_NOT_ALLOWED": {
        "statusCode": 405,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": "Method not allowed"}),
    },
    "UNAUTHORIZED_REQUEST": {
        "statusCode": 401,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": "Cannot verify request"}),
    },
    "CHECKSUM_VERIFICATION_FAILED": {
        "statusCode": 403,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": "Checksum verification failed"}),
    },
    "INTERNAL_SERVER_ERROR": {
        "statusCode": 500,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": "Something went wrong"}),
    },
    "ALL_OK": {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": "All is well"}),
    },
}


def sha256_hash(string):
    # Create a new SHA-256 hash object
    sha256 = hashlib.sha256()
    # Update the hash object with the bytes of the string
    sha256.update(string.encode())
    # Return the hexadecimal representation of the hash
    return sha256.hexdigest()


def validate_request(event, body, headers):
    if event["requestContext"]["http"]["method"] != "POST":
        return False, RESPONSE_CODES["METHOD_NOT_ALLOWED"]

    # verify checksum
    if "x-pingsafe-checksum" not in headers:
        print("X-PingSafe-Checksum header cannot be found, aborting request")
        return False, RESPONSE_CODES["UNAUTHORIZED_REQUEST"]

    checksum = headers["x-pingsafe-checksum"]
    # For more details refer to https://docs.pingsafe.com/getting-pingsafe-events-on-custom-webhook
    if sha256_hash(f"{body['event']}.{API_KEY}") != checksum:
        return False, RESPONSE_CODES["CHECKSUM_VERIFICATION_FAILED"]

    return True, None


"""
this get_handlers returns a dict of
{
    'findingTypeinPingsafe': 'functionNameintheHandler'
}
Eg:
{
    'AWS:IAM:iamRoleLastUsed': iam.remediate_unused_iam_roles
}
In the above example,
function 'remediate_unused_iam_roles' is defined in iam.py
'AWS:IAM:iamRoleLastUsed' is the finding ID in Pingsafe
based on this mapping, lambda knows which function to call to remediate this finding
"""
remediation_handlers = handlers.get_handlers()

"""
This is entrypoint into the lambda function

the body that is sent here via webhook from pingsafe contains all the findings of a specific type in a single json
the sort_into_accs groups the findings by Account so that findings in a single account can be actioned once without too many AssumeRole API requests

The other functions like validate_request etc are just utility functions, we don't need to change them

if you want to see how the body sent by Pingsafe looks like, just print it here below at the entry
"""


def lambda_handler(event, context):
    try:
        body = json.loads(event["body"])
        headers = event["headers"]
        valid, response = validate_request(event, body, headers)
        if not valid:
            return response

        event = base64.b64decode(body["event"])
        pingsafe_event = json.loads(event)

        # check for required env variables, function quits if this fails
        validate_env_vars()

        plugin_key = pingsafe_event["pluginKey"]

        if plugin_key in remediation_handlers:
            handler = remediation_handlers[plugin_key]

            # gets the event data in a sorted manner with key as the AccountTitle
            # check the function definition for explanation
            pingsafe_event = sort_into_accs(pingsafe_event)

            for account_title in pingsafe_event:
                print("Account: {}".format(account_title))

                # Check whether lambda can action on this Account. Enable new accounts by adding env vars
                if (
                    account_title in os.environ
                    and os.environ.get(account_title) != "-1"
                    and len(pingsafe_event[account_title]) > 0
                ):
                    """
                    role to be assumed when actioning an account is defined in the env var
                    'AWS_RZP_Prod': 'arn:aws:iam::141592612890:role/autoremediation-pingsafe'
                    """
                    role = os.environ.get(account_title)

                    """
                    every remediation function that is called from here makes a request to get_client(service, role_arn)
                    if this function is remediation something related to IAM, it will make a request like this
                    get_client("iam", role_arn) -> this will give the fn back a boto3 client which can be used directly in the function
                    """
                    handler.__call__(pingsafe_event[account_title], role)
        else:
            print(f"Lambda doesn't support remediation for {plugin_key}")
        return RESPONSE_CODES["ALL_OK"]
    except Exception as e:
        print("failed to trigger the lambda function, error: ", e)
        return RESPONSE_CODES["INTERNAL_SERVER_ERROR"]

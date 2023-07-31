import iam, elb, dynamodb, kms

'''
mapping of Pingsafe event ID to the function that remediates the finding
to add a new Pingsafe finding to the function,
go to the Pingsafe UI, browse to the finding, go to the network tab in dev tools and get the finding ID
( reload the issue page, and find the issuse Id in /apis/v1/issue/ this req's response )
'''
iam_handlers = {
  # AWS IAM access keys last used time is older than the configured threshold time
  'AWS:IAM:accessKeysLastUsed': iam.remediate_aws_iam_access_keys_last_used,

  # AWS IAM Users have not used their password since long time
  'AWS:IAM:usersPasswordLastUsed': iam.remediate_aws_iam_userpassword_last_used,

  # AWS IAM access Keys are not rotated for more than the configured threshold time - threshold is in pingsafe
  'AWS:IAM:accessKeysRotated': iam.remediate_aws_iam_accesskeys_not_rotated,

  # AWS IAM users don't have MFA active
  # TODO: attach EnforceMFA policy on users
  'AWS:IAM:usersMfaEnabled': iam.remediate_aws_iam_users_mfa_disabled,

  # AWS IAM groups without users found
  'AWS:IAM:emptyGroups': iam.remediate_aws_iam_empty_groups,

  # Unused AWS IAM roles with age greater than threshold exist
  'AWS:IAM:iamRoleLastUsed': iam.remediate_unused_iam_roles
}

elb_handlers = {
  
    # AWS Elastic Load balancers do not have deletion protection enabled
    'AWS:ELB:elbv2DeletionProtection': elb.remediate_elb_deletion_protection_not_enabled
}

dynamodb_handlers = {
  
  # DynamoDB tables do not have continuous backups enabled
  'AWS:DynamoDB:dynamoContinuousBackupsNotEnabled': dynamodb.remediate_dynamodb_continuous_backups
}

kms_handlers = {

  # AWS KMS Key rotation is not enabled
  'AWS:KMS:kmsKeyRotationDisabled': kms.remediate_kms_key_rotation
}

def get_handlers():
  ret = {}
  ret |= iam_handlers
  ret |= elb_handlers
  ret |= dynamodb_handlers
  ret |= kms_handlers
  
  return ret
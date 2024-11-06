from botocore.exceptions import ClientError
from modules.common import exponential_backoff

def list_s3_buckets(session):
    s3_data = []
    try:
        s3_client = session.client('s3')
        buckets = exponential_backoff(s3_client.list_buckets)

        for bucket in buckets['Buckets']:
            bucket_name = bucket['Name']
            creation_date = bucket['CreationDate'].strftime("%Y-%m-%d %H:%M:%S")

            # Additional bucket information
            region = "Unknown"
            versioning = "Disabled"
            encryption = "Not Configured"
            block_public_access = "Unknown"
            static_web_hosting = "Disabled"
            bucket_policy = "-"
            cors = "-"
            lifecycle_expire_days = "-"
            tags_parsed = "-"

            try:
                # Get bucket location (region)
                location = exponential_backoff(s3_client.get_bucket_location, Bucket=bucket_name)
                region = location['LocationConstraint'] if location['LocationConstraint'] else 'us-east-1'
            except ClientError as e:
                print(f"Error retrieving location for bucket {bucket_name}: {e}")

            try:
                # Get versioning status
                versioning_status = exponential_backoff(s3_client.get_bucket_versioning, Bucket=bucket_name)
                versioning = versioning_status.get('Status', 'Disabled')
            except ClientError as e:
                print(f"Error retrieving versioning status for bucket {bucket_name}: {e}")

            try:
                # Get encryption status
                encryption_status = exponential_backoff(s3_client.get_bucket_encryption, Bucket=bucket_name)
                rules = encryption_status['ServerSideEncryptionConfiguration']['Rules']
                encryption = ', '.join([rule['ApplyServerSideEncryptionByDefault']['SSEAlgorithm'] for rule in rules])
            except ClientError as e:
                if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                    encryption = 'Not Configured'
                else:
                    print(f"Error retrieving encryption status for bucket {bucket_name}: {e}")

            try:
                # Get block public access settings
                public_access_status = exponential_backoff(s3_client.get_bucket_acl, Bucket=bucket_name)
                grants = public_access_status.get('Grants', [])
                block_public_access = 'Blocked' if all(grant['Grantee']['Type'] != 'Group' or grant['Grantee'].get('URI') != 'http://acs.amazonaws.com/groups/global/AllUsers' for grant in grants) else 'Not Fully Blocked'
            except ClientError as e:
                print(f"Error retrieving public access block status for bucket {bucket_name}: {e}")

            try:
                # Get static website hosting status
                s3_client.get_bucket_website(Bucket=bucket_name)
                static_web_hosting = 'Enabled'
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchWebsiteConfiguration':
                    static_web_hosting = 'Disabled'
                else:
                    print(f"Error retrieving static website hosting status for bucket {bucket_name}: {e}")

            try:
                # Get bucket policy
                exponential_backoff(s3_client.get_bucket_policy, Bucket=bucket_name)
                bucket_policy = 'Exists'
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchBucketPolicy':
                    bucket_policy = '-'
                else:
                    print(f"Error retrieving bucket policy for bucket {bucket_name}: {e}")

            try:
                # Get CORS configuration
                exponential_backoff(s3_client.get_bucket_cors, Bucket=bucket_name)
                cors = 'Configured'
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchCORSConfiguration':
                    cors = '-'
                else:
                    print(f"Error retrieving CORS configuration for bucket {bucket_name}: {e}")

            try:
                # Get lifecycle configuration
                lifecycle_status = exponential_backoff(s3_client.get_bucket_lifecycle_configuration, Bucket=bucket_name)
                rules = lifecycle_status.get('Rules', [])
                expire_days = [rule['Expiration']['Days'] for rule in rules if 'Expiration' in rule]
                lifecycle_expire_days = ', '.join(map(str, expire_days)) if expire_days else '-'
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
                    lifecycle_expire_days = '-'
                else:
                    print(f"Error retrieving lifecycle configuration for bucket {bucket_name}: {e}")

            try:
                # Get bucket tags
                tagging_status = exponential_backoff(s3_client.get_bucket_tagging, Bucket=bucket_name)
                tags = tagging_status.get('TagSet', [])
                tags_parsed = ', '.join([f"{tag['Key']}: {tag['Value']}" for tag in tags])
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchTagSet':
                    tags_parsed = '-'
                else:
                    print(f"Error retrieving tags for bucket {bucket_name}: {e}")

            # Append the gathered data to the list
            s3_data.append({
                'Bucket Name': bucket_name,
                'Creation Date': creation_date,
                'Region': region,
                'Block All Public Access': block_public_access,
                'Versioning': versioning,
                'Encryption': encryption,
                'Static Web Hosting': static_web_hosting,
                'Bucket Policy': bucket_policy,
                'CORS': cors,
                'Lifecycle Expire Days': lifecycle_expire_days,
                'Tag': tags_parsed
            })
    except ClientError as e:
        print(f"Error retrieving S3 buckets: {e}")
    return s3_data

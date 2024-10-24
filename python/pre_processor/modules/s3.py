import pandas as pd


def extract_principals(policy):
    try:
        if policy is not None:
            statements = policy.get('Statement', [])

            if not isinstance(statements, list):
                statements = [statements]

            principals = []

            for statement in statements:
                principal_dict = statement.get('Principal', {})

                if isinstance(principal_dict, dict):
                    principals.extend([f"{k}: {v}" for k, v in principal_dict.items()])
                elif isinstance(principal_dict, str):
                    principals.append(principal_dict)
                else:
                    print(f"Warning: Unexpected type for Principal in statement: {type(principal_dict)}")

            sorted_principals = sorted(principals)

            return '\n'.join(sorted_principals) if principals else 'No principals found.'
        else:
            return 'None'

    except Exception as e:
        print(f"s3.py > extract_principals(assume_role_policy): {e}")
        return ''


def extract_expire_days(lifecycle_rules):
    try:
        expire_days = []
        if isinstance(lifecycle_rules, list):
            for rule in lifecycle_rules:
                expiration = rule.get('Expiration', {})
                days = expiration.get('Days', '')
                if days:
                    expire_days.append(str(days))
        return ', '.join(expire_days)
    except Exception as e:
        print(f"s3.py > extract_expire_days(lifecycle_rules): {e}")
        return ''



def extract_target_bucket(logging):
    try:
        if logging is not None:
            target_bucket = logging.get('TargetBucket', '-')
        else:
            target_bucket = ''
        return target_bucket
    except Exception as e:
        print(f"s3.py > extract_target_bucket(logging): {e}")
        return '-'



def format_tags(tags):
    try:
        if tags is not None:
            sorted_tags = sorted(tags.items(), key=lambda item: item[0])
            formatted_tags = ', '.join(f"{k}: {v}" for k, v in sorted_tags)
            return formatted_tags if formatted_tags else '-'
        else:
            return ''
    except Exception as e:
        print(f"s3.py → format_tags() : {e}")
        return '-'


def transform_s3_data(s3_data):
    try:
        transformed_data = pd.DataFrame({
            'Name': s3_data['name'],
            'Region': s3_data['region'],
            'Block All Public Access': s3_data[
                    ['block_public_acls', 'block_public_policy', 'ignore_public_acls', 'restrict_public_buckets']
                ].apply(lambda x: 'On' if all(val == True for val in x) else 'Off', axis=1),
            'Versioning': s3_data['versioning_enabled'],
            'Encryption': s3_data['server_side_encryption_configuration'].apply(
                lambda x: 'Enabled' if pd.notna(x) and any(v is not None for v in x.get('Rules', [{}])[0].get('ApplyServerSideEncryptionByDefault', {}).values()) else 'Disabled'),
            'Static Web Hosting': s3_data['website_configuration'].apply(
                lambda x: 'Enabled' if pd.notna(x) and x.get('IndexDocument', {}).get('Suffix') else 'Disabled'),
            'Bucket Policy': s3_data['policy'].apply(extract_principals),
            'CORS': '(Type Here)',
            'Lifecycle Expire Days': s3_data['lifecycle_rules'].apply(extract_expire_days),
            'Static Log': s3_data['logging'].apply(extract_target_bucket),
            'Tag': s3_data['tags'].apply(format_tags),
        })

        transformed_data = transformed_data.sort_values(by='Name', ascending=False)
    except Exception as e:
        print(f"s3.py → transform_s3_data(s3_data): {e}")
        return pd.DataFrame()

    return transformed_data

def load_and_transform_s3_data(s3_data):
    return transform_s3_data(s3_data)

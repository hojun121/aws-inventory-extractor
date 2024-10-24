import pandas as pd


def extract_policies(attached_policy_arns):
    try:
        if attached_policy_arns is None:
            return '-'

        policies = [policy.replace('arn:aws:iam::', '') for policy in attached_policy_arns]

        sorted_policies = sorted(policies)

        return '\n'.join(sorted_policies)

    except Exception as e:
        print(f"iamrole.py > extract_policies(attached_policy_arns): {e}")
        return '-'


def extract_principals(assume_role_policy):
    try:
        statements = assume_role_policy.get('Statement', [])

        if not isinstance(statements, list):
            statements = [statements]

        principals = []

        for statement in statements:
            principal_dict = statement.get('Principal', {})

            principals.extend([f"{k}: {v}" for k, v in principal_dict.items()])

        sorted_principals = sorted(principals)

        return '\n'.join(sorted_principals)

    except Exception as e:
        print(f"iamrole.py > extract_principals(assume_role_policy): {e}")
        return ''


def transform_iam_role_data(iamrole_data):
    try:
        transformed_data = pd.DataFrame({
            'Name': iamrole_data['name'],
            'Trusted Entities': iamrole_data['assume_role_policy'].apply(extract_principals),
            'Policy(arn:aws:iam::)': iamrole_data['attached_policy_arns'].apply(extract_policies),
            'Create Date': iamrole_data['create_date'].dt.tz_localize(None),
            'Role Last Used Date': iamrole_data['role_last_used_date'].dt.tz_localize(None),
        })

        transformed_data = transformed_data.sort_values(by='Name', ascending=False)
    except Exception as e:
        print(f"iamrole.py > transform_iam_role_data(iamrole_data): {e}")
        return pd.DataFrame()

    return transformed_data


def load_and_transform_iam_role_data(iamrole_data):
    return transform_iam_role_data(iamrole_data)

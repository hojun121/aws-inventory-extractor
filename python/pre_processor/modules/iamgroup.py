import pandas as pd
import json

def extract_policies(attached_policy_arns):
    try:
        if attached_policy_arns is None:
            return '-'

        policies = [policy.replace('arn:aws:iam::', '') for policy in attached_policy_arns]

        sorted_policies = sorted(policies)

        return '\n'.join(sorted_policies)

    except Exception as e:
        print(f"iamgroup.py > extract_policies(attached_policy_arns): {e}")
        return '-'


def extract_users(users):
    try:
        user_names = []

        for user in users:
            user_name = user['UserName']
            if user_name not in user_names:
                user_names.append(user_name)

        sorted_users = sorted(user_names)
        return '\n'.join(sorted_users)
    except Exception as e:
        print(f"iamgroup.py > extract_users(users): {e}")
        return '-'


def transform_iam_group_data(iamgroup_data):
    try:
        transformed_data = pd.DataFrame({
            'Name': iamgroup_data['name'],
            'Policy(arn:aws:iam::)': iamgroup_data['attached_policy_arns'].apply(extract_policies),
            'Users': iamgroup_data['users'].apply(extract_users)
        })

        transformed_data = transformed_data.sort_values(by='Name', ascending=False)
    except Exception as e:
        print(f"iamgroup.py > transform_iam_group_data(iamgroup_data): {e}")
        return pd.DataFrame()

    return transformed_data

def load_and_transform_iam_group_data(iamgroup_data):
    return transform_iam_group_data(iamgroup_data)

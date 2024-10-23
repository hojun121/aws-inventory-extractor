import pandas as pd
import json

def extract_policies(attached_policy_arns):
    try:
        policies = [policy.replace('arn:aws:iam::', '') for policy in attached_policy_arns]

        sorted_policies = sorted(policies)

        return '\n'.join(sorted_policies)

    except Exception as e:
        print(f"iamgroup.py > extract_policies(policy_column): {e}")
        return '-'


def extract_users(users):
    user_names = []

    for user in users:
        user_name = user['UserName']
        if user_name not in user_names:
            user_names.append(user_name)

    sorted_users = sorted(user_names)
    return '\n'.join(sorted_users)


def transform_iam_group_data(iamgroup_data):
    transformed_data = pd.DataFrame({
        'Name': iamgroup_data['name'],
        'IAM Policy': iamgroup_data['attached_policy_arns'].apply(extract_policies),
        'Users': iamgroup_data['users'].apply(extract_users)
    })

    transformed_data = transformed_data.sort_values(by='Name', ascending=False)

    return transformed_data

def load_and_transform_iam_group_data(iamgroup_data):
    return transform_iam_group_data(iamgroup_data)

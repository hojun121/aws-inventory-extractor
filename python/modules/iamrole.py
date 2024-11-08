from modules.common import exponential_backoff

def list_iam_roles(session):
    iam_client = session.client('iam')
    roles_data = []
    try:
        # List all IAM roles
        paginator = iam_client.get_paginator('list_roles')
        for page in exponential_backoff(paginator.paginate):
            for role in page['Roles']:
                role_name = role['RoleName']
                trusted_entities = []
                assume_role_policy_document = role.get('AssumeRolePolicyDocument', {})
                if isinstance(assume_role_policy_document, dict):
                    for statement in assume_role_policy_document.get('Statement', []):
                        if statement.get('Effect') == 'Allow':
                            principal = statement.get('Principal', {})
                            for entity_type, entities in principal.items():
                                if isinstance(entities, list):
                                    trusted_entities.extend(entities)
                                else:
                                    trusted_entities.append(entities)

                trusted_entities_str = ', '.join(trusted_entities)

                # Get attached policies
                policy_arns = []
                try:
                    attached_policies = exponential_backoff(iam_client.list_attached_role_policies, RoleName=role_name)
                    for policy in attached_policies.get('AttachedPolicies', []):
                        policy_arns.append(policy['PolicyArn'].replace('arn:aws:iam::aws:policy/', ''))
                except Exception as e:
                    print(f"Error retrieving attached policies for role {role_name}: {e}")

                # Add role data to list
                roles_data.append({
                    'Name': role_name,
                    'Trusted Entities': trusted_entities_str,
                    'Policy(arn:aws:iam::)': ', '.join(policy_arns)
                })
    except Exception as e:
        print(f"Error retrieving IAM roles: {e}")
    return roles_data

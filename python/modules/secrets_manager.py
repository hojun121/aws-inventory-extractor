from modules.common import exponential_backoff

def list_secrets_manager(session):
    client = session.client('secretsmanager')
    secrets = exponential_backoff(client.list_secrets).get("SecretList", [])

    result = []

    for secret in secrets:
        secret_name = secret.get("Name", "-")
        secret_arn = secret.get("ARN", "-")
        secret_desc = secret.get("Description", "-")
        secret_created = secret.get("CreatedDate", "-")
        secret_tags = ", ".join([tag.get("Key", "-") + ":" + tag.get("Value", "-") for tag in secret.get("Tags", [])])

        result.append({
            "Secret Name": secret_name,
            "ARN": secret_arn,
            "Description": secret_desc,
            "Created Date": secret_created,
            "Tags": secret_tags,
            "Rotation Enabled": secret.get("RotationEnabled", False),
            "Last Accessed Date": secret.get("LastAccessedDate", "-")
        })

    return result

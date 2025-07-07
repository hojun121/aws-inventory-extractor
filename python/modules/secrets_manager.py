from modules.common import exponential_backoff

def list_secrets_manager(session):
    client = session.client('secretsmanager')
    secrets = exponential_backoff(client.list_secrets).get("SecretList", [])

    result = []

    for secret in secrets:
        created_date = secret.get("CreatedDate")
        created_date_str = created_date.astimezone().replace(tzinfo=None).isoformat() if created_date else "-"

        last_accessed_date = secret.get("LastAccessedDate")
        last_accessed_date_str = last_accessed_date.astimezone().replace(tzinfo=None).isoformat() if last_accessed_date else "-"

        secret_tags = ", ".join(
            f"{tag.get('Key', '-')}: {tag.get('Value', '-')}"
            for tag in secret.get("Tags", [])
        )

        result.append({
            "Secret Name": secret.get("Name", "-"),
            "ARN": secret.get("ARN", "-"),
            "Description": secret.get("Description", "-"),
            "Created Date": created_date_str,
            "Tags": secret_tags,
            "Rotation Enabled": secret.get("RotationEnabled", False),
            "Last Accessed Date": last_accessed_date_str
        })

    return result

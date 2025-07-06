from modules.common import exponential_backoff

def list_kms_keys(session):
    client = session.client('kms')
    keys = exponential_backoff(client.list_keys).get("Keys", [])

    result = []

    for key in keys:
        key_id = key.get("KeyId", "-")
        key_info = exponential_backoff(client.describe_key, KeyId=key_id).get("KeyMetadata", {})

        result.append({
            "Key ID": key_id,
            "ARN": key_info.get("Arn", "-"),
            "Description": key_info.get("Description", "-"),
            "Key State": key_info.get("KeyState", "-"),
            "Key Usage": key_info.get("KeyUsage", "-"),
            "Creation Date": key_info.get("CreationDate", "-"),
            "Enabled": key_info.get("Enabled", False),
            "Customer Master Key Spec": key_info.get("CustomerMasterKeySpec", "-"),
            "Key Manager": key_info.get("KeyManager", "-"),
            "Origin": key_info.get("Origin", "-"),
            "Expiration Model": key_info.get("ExpirationModel", "-")
        })

    return result

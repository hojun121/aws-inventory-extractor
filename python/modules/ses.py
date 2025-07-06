from modules.common import exponential_backoff

def list_ses_identities(session):
    client = session.client('ses')
    identities = exponential_backoff(client.list_identities).get("Identities", [])

    result = []

    for identity in identities:
        attrs = exponential_backoff(client.get_identity_verification_attributes, Identities=[identity]).get("VerificationAttributes", {}).get(identity, {})
        dkim_attrs = exponential_backoff(client.get_identity_dkim_attributes, Identities=[identity]).get("DkimAttributes", {}).get(identity, {})

        result.append({
            "Identity": identity,
            "Verification Status": attrs.get("VerificationStatus", "-"),
            "Verification Token": ", ".join(attrs.get("VerificationToken", [])),
            "DKIM Enabled": dkim_attrs.get("DkimEnabled", False),
            "DKIM Verification Status": dkim_attrs.get("DkimVerificationStatus", "-"),
            "DKIM Tokens": ", ".join(dkim_attrs.get("DkimTokens", []))
        })

    return result

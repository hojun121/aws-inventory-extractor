from modules.common import exponential_backoff

def list_acm_certificates(session):
    client = session.client('acm')
    certs = exponential_backoff(client.list_certificates).get("CertificateSummaryList", [])

    result = []

    for cert in certs:
        cert_arn = cert.get("CertificateArn", "-")
        cert_info = exponential_backoff(client.describe_certificate, CertificateArn=cert_arn).get("Certificate", {})

        result.append({
            "Certificate ARN": cert_arn,
            "Domain Name": cert_info.get("DomainName", "-"),
            "Subject Alternative Names": ", ".join(cert_info.get("SubjectAlternativeNames", [])),
            "Status": cert_info.get("Status", "-"),
            "Type": cert_info.get("Type", "-"),
            "In Use By": ", ".join(cert_info.get("InUseBy", [])),
            "Issued At": cert_info.get("IssuedAt", "-"),
            "Not Before": cert_info.get("NotBefore", "-"),
            "Not After": cert_info.get("NotAfter", "-"),
            "Issuer": cert_info.get("Issuer", "-"),
            "Key Algorithm": cert_info.get("KeyAlgorithm", "-"),
            "Signature Algorithm": cert_info.get("SignatureAlgorithm", "-")
        })

    return result

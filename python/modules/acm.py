from modules.common import exponential_backoff

def list_acm_certificates(session):
    client = session.client('acm')
    certs = exponential_backoff(client.list_certificates).get("CertificateSummaryList", [])

    result = []

    for cert in certs:
        cert_arn = cert.get("CertificateArn", "-")
        cert_info = exponential_backoff(client.describe_certificate, CertificateArn=cert_arn).get("Certificate", {})

        # datetime 변환 처리
        issued_at = cert_info.get("IssuedAt")
        not_before = cert_info.get("NotBefore")
        not_after = cert_info.get("NotAfter")

        issued_at_str = issued_at.astimezone().replace(tzinfo=None).isoformat() if issued_at else "-"
        not_before_str = not_before.astimezone().replace(tzinfo=None).isoformat() if not_before else "-"
        not_after_str = not_after.astimezone().replace(tzinfo=None).isoformat() if not_after else "-"

        result.append({
            "Certificate ARN": cert_arn,
            "Domain Name": cert_info.get("DomainName", "-"),
            "Subject Alternative Names": ", ".join(cert_info.get("SubjectAlternativeNames", [])),
            "Status": cert_info.get("Status", "-"),
            "Type": cert_info.get("Type", "-"),
            "In Use By": ", ".join(cert_info.get("InUseBy", [])),
            "Issued At": issued_at_str,
            "Not Before": not_before_str,
            "Not After": not_after_str,
            "Issuer": cert_info.get("Issuer", "-"),
            "Key Algorithm": cert_info.get("KeyAlgorithm", "-"),
            "Signature Algorithm": cert_info.get("SignatureAlgorithm", "-")
        })

    return result

from modules.common import exponential_backoff

def list_opensearch_clusters(session):
    client = session.client('opensearch')
    domains = exponential_backoff(client.list_domain_names).get("DomainNames", [])

    result = []

    for domain in domains:
        domain_name = domain.get("DomainName", "-")
        domain_info = exponential_backoff(client.describe_domain, DomainName=domain_name).get("DomainStatus", {})

        result.append({
            "Domain Name": domain_name,
            "Engine Version": domain_info.get("EngineVersion", "-"),
            "Endpoint": domain_info.get("Endpoint", "-"),
            "VPC ID": domain_info.get("VPCOptions", {}).get("VPCId", "-"),
            "Instance Type": domain_info.get("ClusterConfig", {}).get("InstanceType", "-"),
            "Instance Count": domain_info.get("ClusterConfig", {}).get("InstanceCount", "-"),
            "Dedicated Master": domain_info.get("ClusterConfig", {}).get("DedicatedMasterEnabled", False),
            "Zone Awareness": domain_info.get("ClusterConfig", {}).get("ZoneAwarenessEnabled", False),
            "Created": domain_info.get("Created", False),
            "Deleted": domain_info.get("Deleted", False),
            "ARN": domain_info.get("ARN", "-")
        })

    return result

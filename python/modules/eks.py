from modules.common import exponential_backoff

def list_eks_clusters(session):
    client = session.client('eks')
    cluster_names = exponential_backoff(client.list_clusters).get("clusters", [])

    result = []

    for cluster_name in cluster_names:
        cluster_info = exponential_backoff(client.describe_cluster, name=cluster_name).get("cluster", {})

        created_at = cluster_info.get("createdAt")
        created_at_str = created_at.astimezone().replace(tzinfo=None).isoformat() if created_at else "-"

        result.append({
            "Cluster Name": cluster_name,
            "Status": cluster_info.get("status", "-"),
            "Version": cluster_info.get("version", "-"),
            "Endpoint": cluster_info.get("endpoint", "-"),
            "Role ARN": cluster_info.get("roleArn", "-"),
            "VPC ID": cluster_info.get("resourcesVpcConfig", {}).get("vpcId", "-"),
            "Subnet IDs": ", ".join(cluster_info.get("resourcesVpcConfig", {}).get("subnetIds", [])),
            "Security Group IDs": ", ".join(cluster_info.get("resourcesVpcConfig", {}).get("securityGroupIds", [])),
            "Created At": created_at_str,
            "ARN": cluster_info.get("arn", "-")
        })

    return result

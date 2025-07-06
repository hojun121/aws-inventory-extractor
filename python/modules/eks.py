from modules.common import exponential_backoff

def list_eks_clusters(session):
    client = session.client('eks')
    cluster_names = exponential_backoff(client.list_clusters).get("clusters", [])

    result = []

    for cluster_name in cluster_names:
        cluster_info = exponential_backoff(client.describe_cluster, name=cluster_name).get("cluster", {})

        result.append({
            "Cluster Name": cluster_name,
            "Status": cluster_info.get("status", "-"),
            "Version": cluster_info.get("version", "-"),
            "Endpoint": cluster_info.get("endpoint", "-"),
            "Role ARN": cluster_info.get("roleArn", "-"),
            "VPC ID": cluster_info.get("resourcesVpcConfig", {}).get("vpcId", "-"),
            "Subnet IDs": ", ".join(cluster_info.get("resourcesVpcConfig", {}).get("subnetIds", [])),
            "Security Group IDs": ", ".join(cluster_info.get("resourcesVpcConfig", {}).get("securityGroupIds", [])),
            "Created At": cluster_info.get("createdAt", "-"),
            "ARN": cluster_info.get("arn", "-")
        })

    return result

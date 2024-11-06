from modules.common import exponential_backoff

# Corrected ElastiCache clusters listing function
def list_elasticache_clusters(session):
    elasticache_data = []
    try:
        elasticache_client = session.client('elasticache')
        paginator = elasticache_client.get_paginator('describe_cache_clusters')
        response_iterator = paginator.paginate(ShowCacheNodeInfo=True)

        for response in response_iterator:
            clusters = response.get('CacheClusters', [])

            for cluster in clusters:
                cluster_name = cluster.get('CacheClusterId', '-')
                region = session.region_name
                engine = cluster.get('Engine', '-')
                subnet_group = cluster.get('CacheSubnetGroupName', '-')
                parameter_group = cluster.get('CacheParameterGroup', {}).get('CacheParameterGroupName', '-')
                security_groups = ', '.join([sg.get('SecurityGroupId', '-') for sg in cluster.get('SecurityGroups', [])])
                cluster_mode = cluster.get('CacheClusterStatus', '-')
                multi_az = cluster.get('PreferredAvailabilityZone', '-') if cluster.get('Engine') == 'redis' else '-'
                shard = cluster.get('NumCacheNodes', '-')
                node = len(cluster.get('CacheNodes', []))
                backup = 'Enabled' if cluster.get('SnapshotRetentionLimit', 0) > 0 else 'Disabled'
                encryption_at_rest = cluster.get('AtRestEncryptionEnabled', '-') if cluster.get('Engine') == 'redis' else '-'
                auto_failover = cluster.get('AutoMinorVersionUpgrade', '-') if cluster.get('Engine') == 'redis' else '-'

                # Corrected ARN retrieval for tags
                arn = cluster.get('ARN', None)
                if arn:
                    try:
                        tags_response = exponential_backoff(elasticache_client.list_tags_for_resource, ResourceName=arn)
                        tags = ', '.join([f"{tag['Key']}={tag['Value']}" for tag in tags_response.get('TagList', [])])
                    except Exception as e:
                        tags = '-'
                else:
                    tags = '-'

                elasticache_data.append({
                    'Cluster Name': cluster_name,
                    'Region': region,
                    'Engine': engine,
                    'Subnet Name': subnet_group,
                    'Security Group ID': security_groups,
                    'Parameter Group': parameter_group,
                    'Cluster Mode': cluster_mode,
                    'Multi-AZ': multi_az,
                    'Shard': shard,
                    'Node': node,
                    'Automatic Backups': backup,
                    'Encryption at rest': encryption_at_rest,
                    'Auto-failover': auto_failover,
                    'Tags': tags
                })

    except Exception as e:
        print(f"Error retrieving ElastiCache clusters: {e}")
    return elasticache_data


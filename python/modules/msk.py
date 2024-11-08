from modules.common import exponential_backoff

def list_kafka_clusters(session):
    kafka_data = []
    try:
        kafka_client = session.client('kafka')
        paginator = kafka_client.get_paginator('list_clusters')
        response_iterator = paginator.paginate()

        for response in response_iterator:
            for cluster in response['ClusterInfoList']:
                cluster_name = cluster['ClusterName']
                kafka_version = cluster.get('CurrentBrokerSoftwareInfo', {}).get('KafkaVersion', '-')
                cluster_status = cluster.get('State', '-')
                subnet_ids = []
                security_groups = []
                broker_instance_type = '-'
                brokers_per_az = 0
                total_brokers = 0
                ebs_volume_size = '-'
                kms_key_arn = '-'

                # Fetching cluster information to get subnets, security groups, and other details
                try:
                    cluster_info = exponential_backoff(kafka_client.describe_cluster, ClusterArn=cluster['ClusterArn'])
                    if 'ClusterInfo' in cluster_info:
                        broker_node_group_info = cluster_info['ClusterInfo'].get('BrokerNodeGroupInfo', {})
                        subnet_ids = broker_node_group_info.get('ClientSubnets', [])
                        security_groups = broker_node_group_info.get('SecurityGroups', [])
                        broker_instance_type = broker_node_group_info.get('InstanceType', '-')
                        brokers_per_az = cluster_info['ClusterInfo']['NumberOfBrokerNodes'] // len(subnet_ids) if len(subnet_ids) > 0 else 0
                        total_brokers = cluster_info['ClusterInfo']['NumberOfBrokerNodes']
                        storage_info = broker_node_group_info.get('StorageInfo', {}).get('EbsStorageInfo', {})
                        ebs_volume_size = storage_info.get('VolumeSize', '-')
                        kms_key_arn = cluster_info['ClusterInfo'].get('EncryptionInfo', {}).get('EncryptionAtRest', {}).get('DataVolumeKMSKeyId', '-')
                except Exception as e:
                    print(f"Error retrieving cluster info for {cluster_name}: {e}")

                kafka_data.append({
                    'Cluster Name': cluster_name,
                    'Kafka Version': kafka_version,
                    'Status': cluster_status,
                    'Subnet IDs': ', '.join(subnet_ids) if subnet_ids else '-',
                    'Security Group IDs': ', '.join(security_groups) if security_groups else '-',
                    'Broker Instance Type': broker_instance_type,
                    'Brokers per AZ': brokers_per_az,
                    'Total Brokers': total_brokers,
                    'EBS Volume Size (GiB)': ebs_volume_size,
                    'KMS Key ARN': kms_key_arn,
                })
    except Exception as e:
        print(f"Error retrieving Kafka Clusters: {e}")
    return kafka_data

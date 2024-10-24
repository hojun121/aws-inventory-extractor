import pandas as pd


def extract_security_groups(security_groups):
    if pd.isna(security_groups) or not isinstance(security_groups, list):
        return ''

    try:
        return '\n'.join(sg.get('SecurityGroupId', '') for sg in security_groups)
    except Exception as e:
        print(f"ec.py > extract_security_groups(security_groups): {e}")
        return ''


def format_tags(tags):
    try:
        if tags is not None:
            sorted_tags = sorted(tags.items(), key=lambda item: item[0])
            formatted_tags = ', '.join(f"{k}: {v}" for k, v in sorted_tags)
            return formatted_tags if formatted_tags else '-'
        else:
            return ''
    except Exception as e:
        print(f"ec.py → format_tags() : {e}")
        return '-'


def extract_endpoint(cache_nodes):
    try:
        if not cache_nodes:
            return ''
        return '\n'.join(node.get('Endpoint', {}).get('Address', '') for node in cache_nodes if 'Endpoint' in node)
    except Exception as e:
        print(f"ec.py > extract_endpoint(cache_nodes): {e}")
        return ''


def extract_node(node_groups):
    try:
        if not node_groups:
            return 0
        total_members = sum(len(node_group.get('NodeGroupMembers', [])) for node_group in node_groups)
        return total_members
    except Exception as e:
        print(f"ec.py > extract_node(node_groups): {e}")
        return 0


def merge_ec_and_ecrep_data(ec_data, ecrep_data):
    return ec_data.merge(
        ecrep_data,
        on='replication_group_id',
        how='left',
        suffixes=('_cluster', '_replication')
    )


def transform_elasticache_data(ec_data, ecrep_data):
    try:
        merged_data = merge_ec_and_ecrep_data(ec_data, ecrep_data)

        transformed_data = pd.DataFrame({
            'Name': merged_data['title_cluster'],
            'Region': merged_data['region_cluster'],
            'Engine': merged_data['engine'],
            'Type': merged_data['cache_node_type_cluster'],
            'Subnet Group': merged_data['cache_subnet_group_name'],
            'Parameter Group': merged_data['cache_parameter_group'].apply(lambda x: x.get('CacheParameterGroupName') if isinstance(x, dict) else ''),
            'Security Group': merged_data['security_groups'].apply(extract_security_groups),
            'Cluster Mode': merged_data['cluster_enabled'].apply(lambda x: 'Enabled' if x is True else 'Disabled'),
            'Multi-AZ': merged_data['member_clusters'].apply(lambda x: 'Yes' if len(x) >= 2 else 'No'),
            'Shard': merged_data['num_cache_nodes'],
            'Node': merged_data['node_groups'].apply(extract_node),
            'Endpoint': merged_data['cache_nodes'].apply(extract_endpoint),
            # 'Backup': merged_data.apply(lambda x: 'Enabled' if x['snapshotting_cluster_id'] is not None and x['snapshot_retention_limit'] >= 1 else 'Disabled', axis=1),
            'Encryption at rest': merged_data['at_rest_encryption_enabled_cluster'].apply(lambda x: 'Enabled' if x is True else 'Disabled'),
            'Description': merged_data['description']
        })

        transformed_data = transformed_data.sort_values(by='Name', ascending=False)
    except Exception as e:
        print(f"ec.py > transform_elasticache_data(ec_data, ecrep_data): {e}")
        return pd.DataFrame()

    return transformed_data

def load_and_transform_elasticache_data(ec_data, ecrep_data):
    return transform_elasticache_data(ec_data, ecrep_data)

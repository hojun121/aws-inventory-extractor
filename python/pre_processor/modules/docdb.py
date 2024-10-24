import pandas as pd


def extract_vpc_security_group(vpc_security_groups):
    try:
        if pd.isna(vpc_security_groups) or not isinstance(vpc_security_groups, list):
            return ''
        return '\n'.join(sg.get('VpcSecurityGroupId', '') for sg in vpc_security_groups)
    except Exception as e:
        print(f"docdb.py > extract_security_group_ids(vpc_security_groups): {e}")
        return ''


def extract_subnet_ids(subnets):
    try:
        if subnets is None or not isinstance(subnets, list):
            return ''
        return '\n'.join(subnet.get('SubnetIdentifier', '') for subnet in subnets if 'SubnetIdentifier' in subnet)
    except Exception as e:
        print(f"docdb.py > extract_subnet_ids(subnets): {e}")
        return ''


def format_backup_retention_period(period):
    try:
        if pd.notna(period) and period > 0:
            days_label = 'day' if period == 1 else 'days'
            return f'Enabled ({int(period)} {days_label})'
        return 'Disabled'
    except Exception as e:
        print(f"docdb.py > format_backup_retention_period(period): {e}")
        return ''


def extract_cloud_watch(db_instance_identifier, cloudwatch_data):
    try:
        if not (cloudwatch_data['namespace'] == 'AWS/DocDB').any():
            return 'Disabled'

        for _, row in cloudwatch_data[cloudwatch_data['namespace'] == 'AWS/DocDB'].iterrows():
            dimensions = row.get('dimensions', [])
            for dimension in dimensions:
                if dimension.get('Name') == 'DBInstanceIdentifier' and dimension.get('Value') == db_instance_identifier:
                    return 'Enabled'

        return 'Disabled'

    except Exception as e:
        print(f"docdb.py > extract_cloud_watch(db_cluster_identifier, cloudwatch_data): {e}")
        return ''


def transform_docdb_data(docdbcluster_data, docdbinstance_data, cloudwatch_data):
    try:
        merged_data = docdbinstance_data.merge(
            docdbcluster_data,
            left_on='db_cluster_identifier',
            right_on='db_cluster_identifier',
            how='left',
            suffixes=('_instance', '_cluster')
        )

        transformed_data = pd.DataFrame({
            'Cluster Name': merged_data['db_cluster_identifier'],
            'DB Name': merged_data['db_instance_identifier'],
            'Port': merged_data['endpoint_port'],
            'Engine Version': merged_data['engine_version_instance'],
            'Size': merged_data['db_instance_class'],
            'Subnet Group ID': merged_data['db_subnet_group_name'],
            'Subnet ID': merged_data['subnets'].apply(extract_subnet_ids),
            'Parameter Group': merged_data['db_cluster_parameter_group'],
            'Security Group': merged_data['vpc_security_groups_instance'].apply(extract_vpc_security_group),
            'Endpoint': merged_data['endpoint_address'],
            'Backup': merged_data['backup_retention_period_instance'].apply(format_backup_retention_period),
            'Encryption At Rest': merged_data['storage_encrypted_instance'].apply(lambda x: 'Enabled' if x else 'Disabled'),
            'Description': merged_data['db_subnet_group_description'],
            'CloudWatch': merged_data['db_instance_identifier'].apply(lambda x: extract_cloud_watch(x, cloudwatch_data)),
            'Tier': merged_data['promotion_tier'],
        })

        transformed_data = transformed_data.sort_values(by='Cluster Name', ascending=False)
    except Exception as e:
        print(f"docdb.py > transform_docdb_data(docdbcluster_data, docdbinstance_data, cloudwatch_data): {e}")
        return pd.DataFrame()

    return transformed_data


def load_and_transform_docdb_data(docdbcluster_data, docdbinstance_data, cloudwatch_data):
    return transform_docdb_data(docdbcluster_data, docdbinstance_data, cloudwatch_data)

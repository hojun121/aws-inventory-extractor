import pandas as pd

import pandas as pd


def extract_vpc_security_group(vpc_security_groups):
    try:
        if isinstance(vpc_security_groups, pd.Series):
            vpc_security_groups = vpc_security_groups.dropna().tolist()

        if not isinstance(vpc_security_groups, list) or len(vpc_security_groups) == 0:
            return ''

        return '\n'.join(sg.get('VpcSecurityGroupId', '') for sg in vpc_security_groups if isinstance(sg, dict))

    except Exception as e:
        print(f"rds.py > extract_vpc_security_group(vpc_security_groups): {e}")
        return ''


def extract_subnet_ids(subnets):
    try:
        if subnets is None or not isinstance(subnets, list):
            return ''
        return '\n'.join(subnet.get('SubnetIdentifier', '') for subnet in subnets if 'SubnetIdentifier' in subnet)
    except Exception as e:
        print(f"rds.py > extract_subnet_ids(subnets): {e}")
        return ''


def format_backup_retention_period(period):
    try:
        if pd.notna(period) and period > 0:
            days_label = 'day' if period == 1 else 'days'
            return f'Enabled ({int(period)} {days_label})'
        return 'Disabled'
    except Exception as e:
        print(f"rds.py > format_backup_retention_period(period): {e}")
        return ''

def merge_rds_instance_and_cluster_data(rdscluster_data, rdsinstance_data):
    return rdsinstance_data.merge(
        rdscluster_data,
        on='db_cluster_identifier',
        how='left',
        suffixes=('_instance', '_cluster')
    )


def extract_cloud_watch(db_instance_identifier, cloudwatch_data):
    try:
        if not (cloudwatch_data['namespace'] == 'AWS/RDS').any():
            return 'Disabled'

        for _, row in cloudwatch_data[cloudwatch_data['namespace'] == 'AWS/RDS'].iterrows():
            dimensions = row.get('dimensions', [])
            for dimension in dimensions:
                if dimension.get('Name') == 'DBInstanceIdentifier' and dimension.get('Value') == db_instance_identifier:
                    return 'Enabled'

        return 'Disabled'

    except Exception as e:
        print(f"rds.py > extract_cloud_watch(db_cluster_identifier, cloudwatch_data): {e}")
        return ''


def transform_rds_data(rdscluster_data, rdsinstance_data, cloudwatch_data):
    try:
        merged_data = merge_rds_instance_and_cluster_data(rdscluster_data, rdsinstance_data)

        transformed_data = pd.DataFrame({
            'Cluster Name': merged_data['db_cluster_identifier'],
            'DB Name': merged_data['db_instance_identifier'],
            'Port': merged_data['endpoint_port'],
            'Engine Version': merged_data['engine_version_instance'],
            'Size': merged_data['class'],
            'Subnet Group ID': merged_data['db_subnet_group_name'],
            'Subnet ID': merged_data['subnets'].apply(extract_subnet_ids),
            'Parameter Group': merged_data['db_cluster_parameter_group'],
            'VPC Security Group': merged_data['vpc_security_groups_instance'].apply(extract_vpc_security_group),
            'Endpoint': merged_data['endpoint_address'],
            'Backup': merged_data['backup_retention_period_instance'].apply(format_backup_retention_period),
            'Encryption At Rest': merged_data['storage_encrypted_instance'].apply(lambda x: 'Enabled' if x else 'Disabled'),
            'Tier': merged_data['promotion_tier'],
            'CloudWatch': merged_data['db_instance_identifier'].apply(lambda x: extract_cloud_watch(x, cloudwatch_data)),
            'Description': merged_data['db_subnet_group_description'],
        })

        transformed_data = transformed_data.sort_values(by='Cluster Name', ascending=False)
    except Exception as e:
        print(f"rds.py > transform_rds_data(rdscluster_data, rdsinstance_data, cloudwatch_data): {e}")
        return pd.DataFrame()

    return transformed_data


def load_and_transform_rds_data(rdscluster_data, rdsinstance_data, cloudwatch_data):
    return transform_rds_data(rdscluster_data, rdsinstance_data, cloudwatch_data)

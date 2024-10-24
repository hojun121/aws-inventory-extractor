import pandas as pd


def extract_target_health_states(target_health_data):
    try:
        if target_health_data is None or len(target_health_data) == 0:
            return 'none'

        states = [item['TargetHealth']['State'] for item in target_health_data if 'TargetHealth' in item]

        if not states:
            return 'none'

        if all(state == 'healthy' for state in states):
            return 'healthy'
        elif any(state == 'unhealthy' for state in states):
            return 'partially unhealthy'
        else:
            return 'unknown'
    except Exception as e:
        print(f"tg.py > extract_target_health_states(): {e}")
        return ''


def extract_az(target_health_descriptions, autoscaling_data, ec2_data):
    try:
        if len(target_health_descriptions) == 1:
            target = target_health_descriptions[0].get('Target', {})
            availability_zone = target.get('AvailabilityZone')

            if availability_zone == "all":
                return "All"

            if availability_zone is not None:
                return availability_zone

            target_id = target.get('Id')

            if target_id and isinstance(target_id, str):
                def is_valid_ip(ip):
                    parts = ip.split('.')
                    return len(parts) == 4 and all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)

                if is_valid_ip(target_id):
                    matching_row = ec2_data[ec2_data['private_ip_address'] == target_id]
                    if not matching_row.empty:
                        return matching_row['placement_availability_zone'].values[0]
                else:
                    matching_row = ec2_data[ec2_data['instance_id'] == target_id]
                    if not matching_row.empty:
                        return matching_row['placement_availability_zone'].values[0]

        elif len(target_health_descriptions) > 1:
            target_ids = []
            for item in target_health_descriptions:
                if 'Target' in item and 'Id' in item['Target']:
                    target_id = item['Target']['Id']
                    if isinstance(target_id, str) and target_id.count('.') == 3:
                        matching_row = ec2_data[ec2_data['private_ip_address'] == target_id]
                        if not matching_row.empty:
                            target_ids.append(matching_row['instance_id'].values[0])
                    else:
                        target_ids.append(target_id)
            matching_rows = autoscaling_data[
                autoscaling_data['instances'].apply(
                    lambda x: all(instance['InstanceId'] in target_ids for instance in x)
                )
            ]

            if not matching_rows.empty:
                placed_availability_zones = []
                for target_id in target_ids:
                    matching_instances = ec2_data[ec2_data['instance_id'] == target_id]
                    placed_availability_zones.extend(matching_instances['placement_availability_zone'].tolist())
                unique_zones = sorted(set(placed_availability_zones))
                return "\n".join(unique_zones)

        return "(Type Here)"
    except Exception as e:
        print(f"tg.py > extract_az(target_health_descriptions, autoscaling_data, ec2_data): {e}")
        return ''


def transform_target_group_data(target_group_data,autoscaling_data, ec2_data):
    try:
        transformed_data = pd.DataFrame({
            'Name': target_group_data['target_group_name'],
            'Protocol': target_group_data['protocol'],
            'Target Type': target_group_data['target_type'],
            'Load Balancer Arn': target_group_data['load_balancer_arns'].apply(
            lambda x: ', '.join(x) if isinstance(x, list) and x else ''),
            'VPC ID': target_group_data['vpc_id'],
            'Healthy Threshold Count': target_group_data['healthy_threshold_count'],
            'Unhealthy Threshold Count': target_group_data['unhealthy_threshold_count'],
            'Health Check Enabled': target_group_data['health_check_enabled'],
            'Health Check Interval Seconds': target_group_data['health_check_interval_seconds'],
            'Health Check Path': target_group_data['health_check_path'],
            'Health Check Port': target_group_data['health_check_port'],
            'Health Check Protocol': target_group_data['health_check_protocol'],
            'Health Check Timeout Seconds': target_group_data['health_check_timeout_seconds'],
            'Target Health States': target_group_data['target_health_descriptions'].apply(extract_target_health_states),
            # 'AZ': target_group_data.apply(lambda row: extract_az(row['target_health_descriptions'], autoscaling_data, ec2_data), axis=1),
        })

        transformed_data = transformed_data.sort_values(by='Name', ascending=False)
    except Exception as e:
        print(f"tg.py → transform_target_group_data(target_group_data,autoscaling_data, ec2_data): {e}")
        return pd.DataFrame()

    return transformed_data


def load_and_transform_target_group_data(target_group_data, autoscaling_data, ec2_data):
    return transform_target_group_data(target_group_data, autoscaling_data, ec2_data)

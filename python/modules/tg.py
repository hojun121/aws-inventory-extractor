from modules.common import exponential_backoff

def get_tag_value(tags, key):
    for tag in tags:
        if tag['Key'] == key:
            return tag['Value']
    return '-'

def list_target_groups(session):
    elbv2_client = session.client('elbv2')
    ec2_client = session.client('ec2')
    target_groups_data = []

    try:
        target_groups = exponential_backoff(elbv2_client.describe_target_groups)
        if 'TargetGroups' not in target_groups or not target_groups['TargetGroups']:
            print("No target groups found.")
            return target_groups_data

        for target_group in target_groups['TargetGroups']:
            tg_name = target_group['TargetGroupName']
            tg_protocol = target_group['Protocol']
            tg_target_type = target_group['TargetType']
            tg_port = target_group['Port']
            tg_load_balancer_arns = target_group.get('LoadBalancerArns', [])
            tg_vpc_id = target_group['VpcId']
            tg_health_check_protocol = target_group.get('HealthCheckProtocol', '-')
            tg_health_check_path = target_group.get('HealthCheckPath', '-')
            tg_health_check_port = target_group.get('HealthCheckPort', '-')
            tg_health_check_timeout_seconds = target_group.get('HealthCheckTimeoutSeconds', '-')

            instance_data = []
            try:
                health_descriptions = exponential_backoff(
                    elbv2_client.describe_target_health,
                    TargetGroupArn=target_group['TargetGroupArn']
                )
                for desc in health_descriptions['TargetHealthDescriptions']:
                    instance_id = desc['Target']['Id']
                    health_status = desc['TargetHealth']['State']
                    zone = '-'
                    instance_name = "-"

                    if tg_target_type == 'instance':
                        try:
                            instance_info = exponential_backoff(
                                ec2_client.describe_instances,
                                InstanceIds=[instance_id]
                            )
                            for reservation in instance_info['Reservations']:
                                for instance in reservation['Instances']:
                                    zone = instance['Placement']['AvailabilityZone']
                                    instance_name = get_tag_value(instance.get('Tags', []), 'Name')
                        except Exception as e:
                            print(f"Error retrieving instance details for instance ID {instance_id}: {e}")

                    instance_data.append({
                        'Name': tg_name,
                        'Target Type': tg_target_type,
                        'Health Status': health_status,
                        'Instance Name': instance_name,
                        'Instance ID': instance_id,
                        'Zone': zone,
                        'Protocol': tg_protocol,
                        'Port': tg_port,
                        'VPC ID': tg_vpc_id,
                        'Load Balancer Name': '-',  # Placeholder
                        'Health Check Protocol': tg_health_check_protocol,
                        'Health Check Path': tg_health_check_path,
                        'Health Check Timeout Seconds': tg_health_check_timeout_seconds
                    })

            except Exception as e:
                print(f"Error retrieving target health for target group {tg_name}: {e}")

            # 추가된 로직: Target이 없는 TG도 포함시키기
            if not instance_data:
                instance_data.append({
                    'Name': tg_name,
                    'Target Type': tg_target_type,
                    'Health Status': 'unused',  # 타겟 없음
                    'Instance Name': '-',
                    'Instance ID': '-',
                    'Zone': '-',
                    'Protocol': tg_protocol,
                    'Port': tg_port,
                    'VPC ID': tg_vpc_id,
                    'Load Balancer Name': '-',  # Placeholder
                    'Health Check Protocol': tg_health_check_protocol,
                    'Health Check Path': tg_health_check_path,
                    'Health Check Timeout Seconds': tg_health_check_timeout_seconds
                })

            # Load Balancer 이름 매핑
            lb_names = "-"
            if tg_load_balancer_arns:
                lb_names_list = []
                for lb_arn in tg_load_balancer_arns:
                    try:
                        lb_description = exponential_backoff(
                            elbv2_client.describe_load_balancers,
                            LoadBalancerArns=[lb_arn]
                        )
                        for lb in lb_description['LoadBalancers']:
                            tags = exponential_backoff(
                                elbv2_client.describe_tags,
                                ResourceArns=[lb_arn]
                            )
                            lb_name = get_tag_value(tags['TagDescriptions'][0].get('Tags', []), 'Name')
                            if lb_name != '-':
                                lb_names_list.append(lb_name)
                    except Exception as e:
                        print(f"Error retrieving load balancer name for ARN {lb_arn}: {e}")
                lb_names = ', '.join(lb_names_list)

            # Load Balancer 이름 적용
            for instance_entry in instance_data:
                instance_entry['Load Balancer Name'] = lb_names

            target_groups_data.extend(instance_data)

    except Exception as e:
        print(f"Error retrieving target groups: {e}")

    return target_groups_data

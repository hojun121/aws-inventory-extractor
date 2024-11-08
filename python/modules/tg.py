from modules.common import exponential_backoff

def get_tag_value(tags, key):
    for tag in tags:
        if tag['Key'] == key:
            return tag['Value']
    return '-'

def list_target_groups(session):
    elbv2_client = session.client('elbv2')
    ec2_client = session.client('ec2')  # Create EC2 client once to avoid redundancy
    target_groups_data = []
    try:
        # List all target groups
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

            # Get Target Health States and Registered Targets
            instance_data = []
            try:
                health_descriptions = exponential_backoff(elbv2_client.describe_target_health, TargetGroupArn=target_group['TargetGroupArn'])
                for desc in health_descriptions['TargetHealthDescriptions']:
                    instance_id = desc['Target']['Id']
                    health_status = desc['TargetHealth']['State']
                    zone = '-'
                    instance_name = "-"

                    if tg_target_type == 'instance':
                        try:
                            instance_info = exponential_backoff(ec2_client.describe_instances, InstanceIds=[instance_id])
                            for reservation in instance_info['Reservations']:
                                for instance in reservation['Instances']:
                                    zone = instance['Placement']['AvailabilityZone']
                                    instance_name = get_tag_value(instance.get('Tags', []), 'Name')
                        except Exception as e:
                            print(f"Error retrieving instance details for instance ID {instance_id}: {e}")

                    instance_data.append({
                        'Name': tg_name,
                        'Target Type': tg_target_type,
                        'Protocol': tg_protocol,
                        'Port': tg_port,
                        'VPC ID': tg_vpc_id,
                        'Load Balancer Name': '-',  # Placeholder, will be updated below
                        'Health Check Protocol': tg_health_check_protocol,
                        'Health Check Path': tg_health_check_path,
                        'Health Check Port': tg_health_check_port,
                        'Health Check Timeout Seconds': tg_health_check_timeout_seconds,
                        'Instance ID': instance_id,
                        'Instance Name': instance_name,
                        'Zone': zone,
                        'Health Status': health_status
                    })
            except Exception as e:
                print(f"Error retrieving target health for target group {tg_name}: {e}")

            # Get Load Balancer Names from ARNs
            lb_names = "-"
            if tg_load_balancer_arns:
                lb_names_list = []
                for lb_arn in tg_load_balancer_arns:
                    try:
                        lb_description = exponential_backoff(elbv2_client.describe_load_balancers, LoadBalancerArns=[lb_arn])
                        for lb in lb_description['LoadBalancers']:
                            # Extract the "Name" tag if present
                            tags = exponential_backoff(elbv2_client.describe_tags, ResourceArns=[lb_arn])
                            lb_name = get_tag_value(tags['TagDescriptions'][0].get('Tags', []), 'Name')
                            if lb_name != '-':
                                lb_names_list.append(lb_name)
                    except Exception as e:
                        print(f"Error retrieving load balancer name for ARN {lb_arn}: {e}")
                lb_names = ', '.join(lb_names_list)

            # Update Load Balancer Name for each instance entry
            for instance_entry in instance_data:
                instance_entry['Load Balancer Name'] = lb_names

            target_groups_data.extend(instance_data)
    except Exception as e:
        print(f"Error retrieving target groups: {e}")
    return target_groups_data


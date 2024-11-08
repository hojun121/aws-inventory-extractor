from modules.common import exponential_backoff

def list_ec2_instances(session):
    ec2_data = []
    try:
        ec2_client = session.client('ec2')
        ssm_client = session.client('ssm')
        instances = ec2_client.describe_instances()
        for reservation in instances.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                # Check if instance is managed by SSM
                def ssm_check():
                    return ssm_client.describe_instance_information(Filters=[
                        {'Key': 'InstanceIds', 'Values': [instance['InstanceId']]}
                    ])

                try:
                    ssm_response = exponential_backoff(ssm_check)
                    ssm_managed = len(ssm_response.get('InstanceInformationList', [])) > 0
                except Exception as e:
                    print(f"Error checking SSM management for instance {instance['InstanceId']}: {e}")
                    ssm_managed = False

                # Get attached volumes and volume sizes
                volumes_info = []
                for device in instance.get('BlockDeviceMappings', []):
                    if 'Ebs' in device:
                        def volume_info():
                            return ec2_client.describe_volumes(VolumeIds=[device['Ebs']['VolumeId']])

                        try:
                            volume = exponential_backoff(volume_info)
                            volumes_info.append({
                                "VolumeId": device['Ebs']['VolumeId'],
                                "Size (GB)": volume['Volumes'][0]['Size']
                            })
                        except Exception as e:
                            print(f"Error retrieving volume information for volume {device['Ebs']['VolumeId']}: {e}")
                volumes = ', '.join([vol['VolumeId'] for vol in volumes_info])
                volume_sizes = ', '.join([f"{vol['Size (GB)']} GB" for vol in volumes_info])

                # Get tags
                tags = instance.get('Tags', [])
                tags_parsed = ', '.join([f"{tag['Key']}: {tag['Value']}" for tag in tags])

                # Get security groups
                security_groups = instance.get('SecurityGroups', [])
                security_groups_parsed = ', '.join([group['GroupName'] for group in security_groups])

                # Get instance name from tags
                instance_name = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), '-')

                # Get key name
                key_name = instance.get('KeyName', '-')

                # Get IAM role
                iam_instance_profile = instance.get('IamInstanceProfile', {})
                iam_role_name = '-'
                if 'Arn' in iam_instance_profile:
                    iam_role_arn = iam_instance_profile['Arn']
                    iam_role_name = iam_role_arn.split('/')[-1]

                # Get region
                region = session.region_name

                # Get image ID
                image_id = instance.get('ImageId', '-')

                ec2_data.append({
                    'Instance Name': instance_name,
                    'Instance ID': instance['InstanceId'],
                    'Instance Type': instance['InstanceType'],
                    'State': instance['State']['Name'],
                    'Region': region,
                    'SSM Managed': 'Yes' if ssm_managed else 'No',
                    'VPC ID': instance.get('VpcId', '-'),
                    'Subnet ID': instance.get('SubnetId', '-'),
                    'Availability Zone': instance['Placement']['AvailabilityZone'],
                    'Key Name': key_name,
                    'IAM Role': iam_role_name,
                    'Private IP Address': instance.get('PrivateIpAddress', '-'),
                    'Public IP Address': instance.get('PublicIpAddress', '-'),
                    'Launch Time': instance['LaunchTime'].strftime("%Y-%m-%d %H:%M:%S"),
                    'Image ID': image_id,
                    'Volumes': volumes,
                    'Volume Sizes': volume_sizes,
                    'Security Groups': security_groups_parsed,
                    'Tags': tags_parsed
                })
    except Exception as e:
        print(f"Error retrieving EC2 instances: {e}")
    return ec2_data


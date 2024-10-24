import pandas as pd


def extract_group_id(security_groups):
    try:
        if not security_groups:
            return ''
        return ', '.join(group.get('GroupId', '') for group in security_groups)
    except Exception as e:
        print(f"ec2.py > extract_group_id(): {e}")
        return ''


def extract_group_name(security_groups):
    try:
        if not security_groups:
            return ''
        return ', '.join(group.get('GroupName', '') for group in security_groups)
    except Exception as e:
        print(f"ec2.py > extract_group_name(): {e}")
        return ''


def extract_role_from_arn(arn):
    try:
        if arn and isinstance(arn, str):
            return arn.split('/')[-1]
        return ''
    except Exception as e:
        print(f"ec2.py > extract_role_from_arn(): {e}")
        return ''


def extract_volume_id(block_device_mappings):
    try:
        volume_ids = []

        for device in block_device_mappings:
            ebs_info = device.get('Ebs')
            if ebs_info:
                volume_id = ebs_info.get('VolumeId')
                if volume_id:
                    volume_ids.append(volume_id)

        volume_ids_str = "\n".join(volume_ids)

        return volume_ids_str
    except Exception as e:
        print(f"ec2.py > extract_volume_id(): {e}")


def extract_volume_size(block_device_mappings, ebs_data):
    try:
        volume_sizes = []
        for device in block_device_mappings:
            ebs_info = device.get('Ebs')
            if ebs_info:
                volume_id = ebs_info.get('VolumeId')
                if volume_id:
                    volume_size_row = ebs_data.loc[ebs_data['volume_id'] == volume_id, 'size']
                    if not volume_size_row.empty:
                        volume_sizes.append(str(volume_size_row.iloc[0]))
                    else:
                        volume_sizes.append('Unknown')
        volume_sizes_str = "\n".join(volume_sizes)
        return volume_sizes_str
    except Exception as e:
        print(f"ec2.py > extract_volume_size(): {e}")



def format_tags(tags):
    try:
        if tags is not None:
            sorted_tags = sorted(tags.items(), key=lambda item: item[0])
            formatted_tags = ', '.join(f"{k}: {v}" for k, v in sorted_tags)
            return formatted_tags if formatted_tags else '-'
        else:
            return ''
    except Exception as e:
        print(f"ec2.py → format_tags() : {e}")
        return '-'


def transform_ec2_data(ec2_data, ebs_data):
    try:
        transformed_data = pd.DataFrame({
            'Name': ec2_data['title'],
            'ID': ec2_data['instance_id'],
            'Instance State': ec2_data['instance_state'],
            'Region': ec2_data['region'],
            'Availability Zone': ec2_data['placement_availability_zone'],
            'SEV': '(Type Here)',
            'Image ID': ec2_data['image_id'],
            'Instance Type': ec2_data['instance_type'],
            'Vpc ID': ec2_data['vpc_id'],
            'Subnet ID': ec2_data['subnet_id'],
            'Private IP': ec2_data['private_ip_address'],
            'Root Device Type': ec2_data['root_device_type'],
            'Security Groups': ec2_data['security_groups'].apply(extract_group_id),
            'Security Group Name': ec2_data['security_groups'].apply(extract_group_name),
            'Key Name': ec2_data['key_name'],
            'Public IP': ec2_data['public_ip_address'].fillna('None'),
            'Volume ID': ec2_data['block_device_mappings'].apply(extract_volume_id),
            'Volume Size(GB)': ec2_data['block_device_mappings'].apply(extract_volume_size, args=(ebs_data,)),
            'IAM Role': ec2_data['iam_instance_profile_arn'].apply(extract_role_from_arn),
            'Tag': ec2_data['tags'].apply(format_tags),
        })

        transformed_data = transformed_data.sort_values(by='Name', ascending=False)
    except Exception as e:
        print(f"ec2.py → transform_ec2_data(ec2_data, ebs_data): {e}")
        return pd.DataFrame()

    return transformed_data


def load_and_transform_ec2_data(ec2_data, ebs_data):
    return transform_ec2_data(ec2_data, ebs_data)

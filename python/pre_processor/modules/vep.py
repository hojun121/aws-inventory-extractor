import pandas as pd


def extract_subnets(subnet_ids):
    try:
        return ', '.join(subnet_ids) if isinstance(subnet_ids, list) else 'None'
    except Exception as e:
        print(f"vep.py > extract_subnets(subnet_ids): {e}")
        return ''

def extract_security_groups(security_groups):
    try:
        return ', '.join([sg['GroupName'] for sg in security_groups]) if isinstance(security_groups, list) else 'None'
    except Exception as e:
        print(f"vep.py > extract_security_groups(security_groups): {e}")
        return ''

def extract_route_tables(value):
    try:
        return ', '.join(value) if isinstance(value, list) and value else 'None'
    except Exception as e:
        print(f"Error in extract_route_tables: {e}")
        return ''

def extract_terraform(tags):
    try:
        if isinstance(tags, list):
            for tag in tags:
                if tag.get('Key') == 'Terraform' and tag.get('Value') == 'True':
                    return 'Yes'
        return 'No'
    except Exception as e:
        print(f"vep.py > extract_terraform(tags): {e}")
        return ''

def transform_vep_data(vep_data):
    try:
        vep_data['subnets'] = vep_data['subnet_ids'].apply(extract_subnets)
        vep_data['security_groups'] = vep_data['groups'].apply(extract_security_groups)
        vep_data['terraform'] = vep_data['tags'].apply(extract_terraform)

        transformed_data = pd.DataFrame({
            'Name': vep_data['title'],
            'ID': vep_data['vpc_endpoint_id'],
            'VPC ID': vep_data['vpc_id'],
            'Service Name': vep_data['service_name'],
            'Type': vep_data['vpc_endpoint_type'],
            'Route Table': vep_data['route_table_ids'].apply(extract_route_tables),
            'Subnet (Interface)': vep_data['subnets'],
            'Security Group (Interface)': vep_data['security_groups'],
            'Terraform': vep_data['terraform']
        })

        transformed_data = transformed_data.sort_values(by='Name', ascending=False)
    except Exception as e:
        print(f"vep.py > transform_vep_data(vep_data): {e}")
        return pd.DataFrame()

    return transformed_data

def load_and_transform_vep_data(vep_data):
    return transform_vep_data(vep_data)

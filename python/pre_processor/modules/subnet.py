import pandas as pd


def parse_rf_associations(associations):
    try:
        return {
            assoc.get('SubnetId', ''): {
                'Route Table ID': assoc.get('RouteTableId', ''),
                'Title': assoc.get('RouteTableAssociationId', '')
            } for assoc in associations
        }
    except Exception as e:
        print(f"subnet.py > parse_rf_associations(associations): {e}")
        return {}

def parse_network_acl_associations(associations):
    try:
        return {
            assoc.get('SubnetId', ''): {
                'Network Acl ID': assoc.get('NetworkAclId', ''),
                'Title': assoc.get('NetworkAclAssociationId', '')
            } for assoc in associations
        }
    except Exception as e:
        print(f"subnet.py > parse_network_acl_associations(associations): {e}")
        return {}

def get_route_table_id(subnet_id, rt_dict):
    try:
        return rt_dict.get(subnet_id, {}).get('Route Table ID', '')
    except Exception as e:
        print(f"subnet.py > get_route_table_id(subnet_id, rt_dict): {e}")
        return ''

def get_route_table_name(subnet_id, rt_dict):
    try:
        return rt_dict.get(subnet_id, {}).get('Title', '')
    except Exception as e:
        print(f"subnet.py > get_route_table_name(subnet_id, rt_dict): {e}")
        return ''

def get_network_acl_id(subnet_id, nacl_dict):
    try:
        return nacl_dict.get(subnet_id, {}).get('Network Acl ID', '')
    except Exception as e:
        print(f"subnet.py > get_network_acl_id(subnet_id, nacl_dict): {e}")
        return ''

def get_network_acl_name(subnet_id, nacl_dict):
    try:
        return nacl_dict.get(subnet_id, {}).get('Title', '')
    except Exception as e:
        print(f"subnet.py > get_network_acl_name(subnet_id, nacl_dict): {e}")
        return ''


def transform_subnet_data(subnet_data, rt_data, nacl_data):
    try:
        rt_dict = {}
        for _, row in rt_data.iterrows():
            associations = row['associations']
            rt_dict.update(parse_rf_associations(associations))

        nacl_dict = {}
        for _, row in nacl_data.iterrows():
            associations = row['associations']
            nacl_dict.update(parse_network_acl_associations(associations))

        transformed_data = pd.DataFrame({
            'Name': subnet_data['title'],
            'ID': subnet_data['subnet_id'],
            'Subnet CIDR Block': subnet_data['cidr_block'],
            'Availability Zone': subnet_data['availability_zone'],
            'Route Table ID': subnet_data['subnet_id'].apply(lambda x: get_route_table_id(x, rt_dict)),
            'Route Table Name': subnet_data['subnet_id'].apply(lambda x: get_route_table_name(x, rt_dict)),
            'Network ACL ID': subnet_data['subnet_id'].apply(lambda x: get_network_acl_id(x, nacl_dict)),
            'Network ACL Name': subnet_data['subnet_id'].apply(lambda x: get_network_acl_name(x, nacl_dict)),
        })

        transformed_data = transformed_data.sort_values(by='Name', ascending=False)

        return transformed_data
    except Exception as e:
        print(f"subnet.py > transform_subnet_data(subnet_data, rt_data, nacl_data): {e}")
        return pd.DataFrame()

def load_and_transform_subnet_data(subnet_data, rt_data, nacl_data):
    return transform_subnet_data(subnet_data, rt_data, nacl_data)

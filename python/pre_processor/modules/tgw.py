import pandas as pd


def transform_tgw_data(tgw_data):
    try:
        transformed_data = pd.DataFrame({
            'Name': tgw_data['title'],
            'ID': tgw_data['transit_gateway_id'],
            'State': tgw_data['state'],
            'Region': tgw_data['region'],
            'Default Association Route Table': tgw_data['default_route_table_association'],
            'Default Propagation Route Table': tgw_data['default_route_table_propagation'],
            'Transit Gateway CIDR Blocks': tgw_data['cidr_blocks'].apply(lambda x: 'None' if not x else x),
            'Association Route Table ID': tgw_data['association_default_route_table_id'].apply(
                lambda x: 'None' if not x else x),
            'Propagation Route Table ID': tgw_data['propagation_default_route_table_id'].apply(
                lambda x: 'None' if not x else x),
            'Multicast Support': tgw_data['multicast_support'],
            'DNS Support': tgw_data['dns_support'],
            'Auto Accept Shared Attachments': tgw_data['auto_accept_shared_attachments'],
            'VPN ECMP Support': tgw_data['vpn_ecmp_support'],
        })

        transformed_data = transformed_data.sort_values(by='Name', ascending=False)
    except Exception as e:
        print(f"tg.py > transform_tgw_data(tgw_data): {e}")
        return pd.DataFrame()

    return transformed_data


def load_and_transform_tgw_data(tgw_data):
    return transform_tgw_data(tgw_data)

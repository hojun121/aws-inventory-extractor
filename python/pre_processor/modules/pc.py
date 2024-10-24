import pandas as pd

def extract_cidr(cidr_set):
    try:
        if isinstance(cidr_set, list):
            return ', '.join([entry['CidrBlock'] if isinstance(entry, dict) and 'CidrBlock' in entry else '' for entry in cidr_set])
        else:
            return 'None'
    except Exception as e:
        print(f"pc.py > extract_cidr(cidr_set): {e}")
        return ''


def transform_pc_data(pc_data):
    try:
        pc_data['requester_cidrs'] = pc_data['requester_cidr_block_set'].apply(extract_cidr)
        pc_data['accepter_cidrs'] = pc_data['accepter_cidr_block_set'].apply(extract_cidr)

        transformed_data = pd.DataFrame({
            'Name': pc_data['title'],
            'ID': pc_data['id'],
            'State': pc_data['status_code'],
            'Requester VPC': pc_data['requester_vpc_id'],
            'Accepter VPC': pc_data['accepter_vpc_id'],
            'Requester CIDRs': pc_data['requester_cidrs'],
            'Accepter CIDRs': pc_data['accepter_cidrs'],
            'Requester owner ID': pc_data['requester_owner_id'],
            'Accepter owner ID': pc_data['accepter_owner_id'],
            'Requester Region': pc_data['requester_region'],
            'Accepter Region': pc_data['accepter_region'],
        })

        transformed_data = transformed_data.sort_values(by='Name', ascending=False)
    except Exception as e:
        print(f"pc.py > transform_pc_data(pc_data): {e}")
        return pd.DataFrame()

    return transformed_data

def load_and_transform_pc_data(pc_data):
    return transform_pc_data(pc_data)

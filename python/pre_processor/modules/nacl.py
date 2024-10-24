import pandas as pd


def process_acl_entries(entries, nacl_name, nacl_id, vpc_id, region):
    try:
        processed_entries = []
        for entry in entries:
            protocol = entry.get("Protocol", "All")
            if protocol == "-1":
                protocol = "All"
            elif protocol == "6":
                protocol = "TCP (6)"

            port_range = entry.get("PortRange", {})
            if port_range:
                from_port = port_range.get("From", "All")
                to_port = port_range.get("To", "All")
                if from_port == 0 and to_port == 65535:
                    port_range_str = "All"
                elif from_port == to_port:
                    port_range_str = str(from_port)
                else:
                    port_range_str = f"{from_port}-{to_port}"
            else:
                port_range_str = "All"

            rule_number = entry.get("RuleNumber", "*")
            if rule_number == 32767:
                rule_number = "*"

            action = entry.get("RuleAction", "Deny").capitalize()
            source = entry.get("CidrBlock", "0.0.0.0/0") or entry.get("Ipv6CidrBlock", "0.0.0.0/0")

            processed_entries.append({
                'Name': nacl_name,
                'ID': nacl_id,
                'VPC ID': vpc_id,
                'Region': region,
                'Direction': "Inbound" if not entry.get("Egress") else "Outbound",
                'Rule': rule_number,
                'Type': 'All traffic' if protocol == "All" else 'Custom traffic',
                'Protocol': protocol,
                'Port Range': port_range_str,
                'Source': source,
                'Allow / Deny': action,
            })
        return processed_entries
    except Exception as e:
        print(f"nacl.py > process_acl_entries(entries, nacl_name, nacl_id, vpc_id, region): {e}")
        return ''

def transform_nacls_data(nacl_data):
    try:
        data_list = []

        for _, row in nacl_data.iterrows():
            entries = row['entries']

            nacl_name = row['title']
            if nacl_name == row['network_acl_id']:
                nacl_name = '-'

            data_list.extend(
                process_acl_entries(entries, nacl_name, row['network_acl_id'], row['vpc_id'], row['region']))

        transformed_data = pd.DataFrame(data_list)
        transformed_data = transformed_data.sort_values(by='Name', ascending=False)
    except Exception as e:
        print(f"nacl.py > transform_nacls_data(nacl_data): {e}")
        return pd.DataFrame()

    return transformed_data

def load_and_transform_nacl_data(nacl_data):
    return transform_nacls_data(nacl_data)

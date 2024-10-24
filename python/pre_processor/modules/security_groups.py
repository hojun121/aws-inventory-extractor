import pandas as pd


def load_sg_rules_mapping(sgrule_data):
    try:
        sgrule_data['direction'] = sgrule_data['is_egress'].apply(lambda x: 'Outbound' if x else 'Inbound')
        sgrule_data['rule_key'] = sgrule_data['group_id'] + '-' + sgrule_data['direction']
        rule_mapping = dict(zip(sgrule_data['rule_key'], sgrule_data['security_group_rule_id']))
        return rule_mapping
    except Exception as e:
        print(f"Error loading sgrule dataframe: {e}")
        return {}


def get_rule_id(sg_id, direction, rule_mapping):
    key = f"{sg_id}-{direction}"
    return rule_mapping.get(key, "-")


def get_name_from_tags(tags):
    try:
        return tags.get("Name", "-") if isinstance(tags, dict) else "-"
    except Exception as e:
        print(f"Tags parsing error: {e}")
        return "-"


def comments_from_rule(protocol, source_dest, name, sg_name):
    comments = ""

    # Check all IPs are open
    if source_dest == "0.0.0.0/0":
        comments += "All IPs are open"

    # Check all ports are open
    if protocol == "All":
        if comments:
            comments += " and all ports are open\n"
        else:
            comments = "All ports are open\n"

    # When Name is '-', Add 'No security group name'
    if name == "-":
        comments += ", No security group name" if comments else "No security group name"

    # Confirm Default Security Group
    if sg_name.lower() == 'default':
        if comments:
            comments += " and Default Security Group has rules\n"
        else:
            comments = "Default Security Group has rules\n"

    return comments.rstrip('\n')


def process_rule(rule, direction, sg_name, sg_id, region, rule_mapping, tags):
    rules_list = []
    try:
        name = get_name_from_tags(tags)

        for r in rule:
            protocol = "All" if r.get("IpProtocol") == "-1" else r.get("IpProtocol", "-")  # Protocol이 -1이면 All로 표기

            # 포트 범위 설정 (None이면 '-'로 처리)
            from_port = r.get('FromPort', '-')
            to_port = r.get('ToPort', '-')
            from_port = '-' if from_port is None else from_port
            to_port = '-' if to_port is None else to_port
            port_range = f"{from_port}" if from_port == to_port else f"{from_port}-{to_port}"

            # CIDR, IPv6 주소 범위 설정
            cidr_blocks = [ip_range.get("CidrIp", "-") for ip_range in r.get("IpRanges", [])]
            ipv6_blocks = [ip_range.get("CidrIpv6", "-") for ip_range in r.get("Ipv6Ranges", [])]
            source_dest = ', '.join(cidr_blocks + ipv6_blocks) if cidr_blocks + ipv6_blocks else "-"

            # Rule ID 얻기
            rule_id = get_rule_id(sg_id, direction, rule_mapping)
            descriptions = [ip_range.get("Description", "-") for ip_range in r.get("IpRanges", [])]
            description = ', '.join(desc if desc else "-" for desc in descriptions)

            comments = comments_from_rule(protocol, source_dest, name, sg_name)

            rules_list.append({
                'Name': name,
                'Security Group Name': sg_name,
                'Group ID': sg_id,
                'Rule ID': rule_id,
                'Region': region,
                'Protocol': protocol,
                'Port Range': port_range,
                'Source/Destination': source_dest,
                'Direction': direction,
                'Description': description,
                'Comments': comments,
            })
    except Exception as e:
        print(f"security_groups.py → process_rule(rule, direction, sg_name, sg_id, region, rule_mapping, tags): {e}")

    return rules_list


def transform_security_groups_data(sg_data, sgrule_data):
    try:
        rule_mapping = load_sg_rules_mapping(sgrule_data)

        data_list = []

        for _, row in sg_data.iterrows():
            ingress_rules = row['ip_permissions']
            data_list.extend(
                process_rule(ingress_rules, 'Inbound', row['group_name'], row['group_id'], row['region'], rule_mapping,
                             row['tags']))

            egress_rules = row['ip_permissions_egress']
            data_list.extend(
                process_rule(egress_rules, 'Outbound', row['group_name'], row['group_id'], row['region'], rule_mapping,
                             row['tags']))

        transformed_data = pd.DataFrame(data_list)

        transformed_data = transformed_data.sort_values(by='Name', ascending=False)
    except Exception as e:
        print(f"security_groups.py → transform_security_groups_data(sg_data, sgrule_data): {e}")
        return pd.DataFrame()

    return transformed_data


def load_and_transform_security_groups_data(sg_data, sgrule_data):
    return transform_security_groups_data(sg_data, sgrule_data)

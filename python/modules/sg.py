from modules.common import exponential_backoff

def list_security_groups(session):
    ec2_client = session.client('ec2')
    security_groups = []

    try:
        # Retrieve all security groups
        response = exponential_backoff(ec2_client.describe_security_groups)
        all_sgs = response['SecurityGroups']

        # Find all security group IDs that are in use by ENIs
        eni_response = exponential_backoff(ec2_client.describe_network_interfaces)
        used_sg_ids = set()
        for eni in eni_response['NetworkInterfaces']:
            for group in eni.get('Groups', []):
                used_sg_ids.add(group['GroupId'])

        for sg in all_sgs:
            security_group_name = sg.get('GroupName', '-')
            security_group_id = sg.get('GroupId', '-')
            description = sg.get('Description', '-')
            region = session.region_name

            usage_flag = security_group_id in used_sg_ids

            # Extract the 'Name' tag if it exists, or use 'default' for default security groups
            name = '-'
            for tag in sg.get('Tags', []):
                if tag['Key'] == 'Name':
                    name = tag['Value']
                    break
            if security_group_name == 'default':
                name = 'default'
            elif name == '-':
                name = security_group_name

            # If there are no inbound or outbound rules, add the security group with default values
            if not sg.get('IpPermissions') and not sg.get('IpPermissionsEgress'):
                security_groups.append({
                    'Usage': usage_flag,
                    'Name': name,
                    'Security Group ID': security_group_id,
                    'SG Description': description,
                    'Region': region,
                    'Direction': '-',
                    'Protocol': '-',
                    'Port Range': '-',
                    'Source': '-',
                    'Destination': '-',
                    'Rules Src/Dst Description': '-'
                })

            # Extract rules from Inbound (Ingress) and Outbound (Egress)
            for rule in sg.get('IpPermissions', []):
                security_groups += parse_rule(rule, name, security_group_id, description, region, 'Inbound', usage_flag)
            for rule in sg.get('IpPermissionsEgress', []):
                security_groups += parse_rule(rule, name, security_group_id, description, region, 'Outbound', usage_flag)

    except Exception as e:
        print(f"Error retrieving security groups: {e}")

    return security_groups

def parse_rule(rule, name, security_group_id, description, region, direction, usage_flag):
    protocol = rule.get('IpProtocol', '-')
    protocol = 'all' if protocol == '-1' else protocol
    from_port = rule.get('FromPort', '-')
    to_port = rule.get('ToPort', '-')
    port_range = f"{from_port}-{to_port}" if from_port != to_port else f"{from_port}"

    rules = []

    def build_rule_entry(source='-', destination='-', desc='-'):
        return {
            'Usage': usage_flag,
            'Name': name,
            'Security Group ID': security_group_id,
            'Description': description,
            'Region': region,
            'Direction': direction,
            'Protocol': protocol,
            'Port Range': port_range,
            'Source': source,
            'Destination': destination,
            'Src/Dst Description': desc
        }

    if direction == 'Inbound':
        for ip_range in rule.get('IpRanges', []):
            rules.append(build_rule_entry(source=ip_range.get('CidrIp', '-'), desc=ip_range.get('Description', '-')))
        for ipv6_range in rule.get('Ipv6Ranges', []):
            rules.append(build_rule_entry(source=ipv6_range.get('CidrIpv6', '-'), desc=ipv6_range.get('Description', '-')))
        for user_id_group_pair in rule.get('UserIdGroupPairs', []):
            rules.append(build_rule_entry(source=user_id_group_pair.get('GroupId', '-'), desc=user_id_group_pair.get('Description', '-')))
    else:
        for ip_range in rule.get('IpRanges', []):
            rules.append(build_rule_entry(destination=ip_range.get('CidrIp', '-'), desc=ip_range.get('Description', '-')))
        for ipv6_range in rule.get('Ipv6Ranges', []):
            rules.append(build_rule_entry(destination=ipv6_range.get('CidrIpv6', '-'), desc=ipv6_range.get('Description', '-')))
        for user_id_group_pair in rule.get('UserIdGroupPairs', []):
            rules.append(build_rule_entry(destination=user_id_group_pair.get('GroupId', '-'), desc=user_id_group_pair.get('Description', '-')))

    return rules
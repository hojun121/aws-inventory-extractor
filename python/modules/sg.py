from modules.common import exponential_backoff

def list_security_groups(session):
    ec2_client = session.client('ec2')
    security_groups = []

    try:
        # Retrieve all security groups
        response = exponential_backoff(ec2_client.describe_security_groups)
        
        for sg in response['SecurityGroups']:
            security_group_name = sg.get('GroupName', '-')
            security_group_id = sg.get('GroupId', '-')
            description = sg.get('Description', '-')
            region = session.region_name
            
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
                    'Name': name,
                    'Security Group ID': security_group_id,
                    'Description': description,
                    'Region': region,
                    'Direction': '-',
                    'Protocol': '-',
                    'Port Range': '-',
                    'Source': '-',
                    'Destination': '-',
                    'Src/Dst Description': '-'
                })
            
            # Extract rules from Inbound (Ingress) and Outbound (Egress)
            for rule in sg.get('IpPermissions', []):
                security_groups += parse_rule(rule, name, security_group_id, description, region, 'Inbound')
            for rule in sg.get('IpPermissionsEgress', []):
                security_groups += parse_rule(rule, name, security_group_id, description, region, 'Outbound')

    except Exception as e:
        print(f"Error retrieving security groups: {e}")

    return security_groups

def parse_rule(rule, name, security_group_id, description, region, direction):
    protocol = rule.get('IpProtocol', '-')
    protocol = 'all' if protocol == '-1' else protocol
    from_port = rule.get('FromPort', '-')
    to_port = rule.get('ToPort', '-')
    port_range = f"{from_port}-{to_port}" if from_port != to_port else f"{from_port}"
    
    rules = []
    
    # Extract Source or Destination and corresponding description
    if direction == 'Inbound':
        for ip_range in rule.get('IpRanges', []):
            source = ip_range.get('CidrIp', '-')
            src_dst_description = ip_range.get('Description', '-')
            rules.append({
                'Name': name,
                'Security Group ID': security_group_id,
                'Description': description,
                'Region': region,
                'Direction': direction,
                'Protocol': protocol,
                'Port Range': port_range,
                'Source': source,
                'Destination': '-',
                'Src/Dst Description': src_dst_description
            })
        for ipv6_range in rule.get('Ipv6Ranges', []):
            source = ipv6_range.get('CidrIpv6', '-')
            src_dst_description = ipv6_range.get('Description', '-')
            rules.append({
                'Name': name,
                'Security Group ID': security_group_id,
                'Description': description,
                'Region': region,
                'Direction': direction,
                'Protocol': protocol,
                'Port Range': port_range,
                'Source': source,
                'Destination': '-',
                'Src/Dst Description': src_dst_description
            })
        for user_id_group_pair in rule.get('UserIdGroupPairs', []):
            source = user_id_group_pair.get('GroupId', '-')
            src_dst_description = user_id_group_pair.get('Description', '-')
            rules.append({
                'Name': name,
                'Security Group ID': security_group_id,
                'Description': description,
                'Region': region,
                'Direction': direction,
                'Protocol': protocol,
                'Port Range': port_range,
                'Source': source,
                'Destination': '-',
                'Src/Dst Description': src_dst_description
            })
    elif direction == 'Outbound':
        for ip_range in rule.get('IpRanges', []):
            destination = ip_range.get('CidrIp', '-')
            src_dst_description = ip_range.get('Description', '-')
            rules.append({
                'Name': name,
                'Security Group ID': security_group_id,
                'Description': description,
                'Region': region,
                'Direction': direction,
                'Protocol': protocol,
                'Port Range': port_range,
                'Source': '-',
                'Destination': destination,
                'Src/Dst Description': src_dst_description
            })
        for ipv6_range in rule.get('Ipv6Ranges', []):
            destination = ipv6_range.get('CidrIpv6', '-')
            src_dst_description = ipv6_range.get('Description', '-')
            rules.append({
                'Name': name,
                'Security Group ID': security_group_id,
                'Description': description,
                'Region': region,
                'Direction': direction,
                'Protocol': protocol,
                'Port Range': port_range,
                'Source': '-',
                'Destination': destination,
                'Src/Dst Description': src_dst_description
            })
        for user_id_group_pair in rule.get('UserIdGroupPairs', []):
            destination = user_id_group_pair.get('GroupId', '-')
            src_dst_description = user_id_group_pair.get('Description', '-')
            rules.append({
                'Name': name,
                'Security Group ID': security_group_id,
                'Description': description,
                'Region': region,
                'Direction': direction,
                'Protocol': protocol,
                'Port Range': port_range,
                'Source': '-',
                'Destination': destination,
                'Src/Dst Description': src_dst_description
            })

    return rules

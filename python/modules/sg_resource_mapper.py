from modules.common import exponential_backoff

def map_parse_sg_rule(rule, name, sg_id, description, region, direction):
    protocol = rule.get('IpProtocol', '-')
    protocol = 'all' if protocol == '-1' else protocol
    from_port = rule.get('FromPort', '-')
    to_port = rule.get('ToPort', '-')
    port_range = f"{from_port}-{to_port}" if from_port != to_port else f"{from_port}"

    rules = []

    def entry(src=None, dst=None, desc='-'):
        return {
            'Security Group Name': name,
            'Security Group ID': sg_id,
            'Description': description,
            'Region': region,
            'Direction': direction,
            'Protocol': protocol,
            'Port Range': port_range,
            'Src Origin': src if direction == 'Inbound' else '-',
            'Des Origin': dst if direction == 'Outbound' else '-',
            'Src/Dst Description': desc
        }

    if direction == 'Inbound':
        for ip in rule.get('IpRanges', []):
            rules.append(entry(src=ip.get('CidrIp'), desc=ip.get('Description', '-')))
        for ip in rule.get('Ipv6Ranges', []):
            rules.append(entry(src=ip.get('CidrIpv6'), desc=ip.get('Description', '-')))
        for group in rule.get('UserIdGroupPairs', []):
            rules.append(entry(src=group.get('GroupId'), desc=group.get('Description', '-')))
    else:
        for ip in rule.get('IpRanges', []):
            rules.append(entry(dst=ip.get('CidrIp'), desc=ip.get('Description', '-')))
        for ip in rule.get('Ipv6Ranges', []):
            rules.append(entry(dst=ip.get('CidrIpv6'), desc=ip.get('Description', '-')))
        for group in rule.get('UserIdGroupPairs', []):
            rules.append(entry(dst=group.get('GroupId'), desc=group.get('Description', '-')))

    return rules

def map_extract_all_sg_rules(session):
    ec2 = session.client('ec2')
    result = []

    response = exponential_backoff(ec2.describe_security_groups)
    for sg in response['SecurityGroups']:
        sg_name = sg.get('GroupName', '-')
        sg_id = sg.get('GroupId', '-')
        description = sg.get('Description', '-')
        region = session.region_name

        name = next((tag['Value'] for tag in sg.get('Tags', []) if tag['Key'] == 'Name'), sg_name)
        if sg_name == 'default':
            name = 'default'

        if not sg.get('IpPermissions') and not sg.get('IpPermissionsEgress'):
            result.append({
                'Security Group Name': name,
                'Security Group ID': sg_id,
                'Description': description,
                'Region': region,
                'Direction': '-',
                'Protocol': '-',
                'Port Range': '-',
                'Src Origin': '-',
                'Des Origin': '-',
                'Src/Dst Description': '-'
            })

        for rule in sg.get('IpPermissions', []):
            result += map_parse_sg_rule(rule, name, sg_id, description, region, 'Inbound')
        for rule in sg.get('IpPermissionsEgress', []):
            result += map_parse_sg_rule(rule, name, sg_id, description, region, 'Outbound')

    return result

def map_group_sg_rules_by_id(sg_rules):
    sg_map = {}
    for rule in sg_rules:
        sg_id = rule['Security Group ID']
        if sg_id not in sg_map:
            sg_map[sg_id] = []
        sg_map[sg_id].append(rule)
    return sg_map

def map_infer_resource_type(description, interface_type):
    desc = (description or '').lower()

    if 'lambda' in desc:
        return 'Lambda'
    if 'elb' in desc:
        return 'ELB'
    if 'rds' in desc:
        return 'RDS'
    if 'msk' in desc or 'kafka' in desc:
        return 'MSK'
    if 'opensearch' in desc or 'es endpoint' in desc:
        return 'OpenSearch'
    if 'efs' in desc or 'mount target' in desc:
        return 'EFS'
    if 'nat gateway' in desc:
        return 'NAT Gateway'
    if 'transit gateway' in desc or 'tgw' in desc:
        return 'Transit Gateway'
    if 'vpce' in desc or 'vpc endpoint' in desc:
        return 'VPC Endpoint'
    if 'redshift' in desc:
        return 'Redshift'
    if 'global accelerator' in desc:
        return 'Global Accelerator'

    if interface_type == 'interface':
        return 'EC2'

    return 'Unknown'

def build_sg_id_name_map(session):
    ec2 = session.client('ec2')
    response = exponential_backoff(ec2.describe_security_groups)
    return {
        sg['GroupId']: next(
            (tag['Value'] for tag in sg.get('Tags', []) if tag['Key'] == 'Name'),
            sg.get('GroupName', '-')
        )
        for sg in response['SecurityGroups']
    }

def build_resource_id_name_map(session):
    ec2 = session.client("ec2")
    reservations = exponential_backoff(ec2.describe_instances).get("Reservations", [])
    resource_map = {}
    for res in reservations:
        for inst in res.get("Instances", []):
            instance_id = inst["InstanceId"]
            name = next((tag["Value"] for tag in inst.get("Tags", []) if tag["Key"] == "Name"), "-")
            resource_map[instance_id] = name
    return resource_map

def enrich_sg_resource_result(session, combined):
    sg_name_map = build_sg_id_name_map(session)
    resource_name_map = build_resource_id_name_map(session)

    enriched = []
    for r in combined:
        src = r.get('Src Origin')
        dst = r.get('Des Origin')
        resource_id = r.get('Resource ID')

        enriched.append({
            'Resource Name': resource_name_map.get(resource_id, '-'),
            'Resource ID': resource_id,
            'Resource Type': r.get('Resource Type'),
            'Security Group Name': r.get('Security Group Name'),
            'Security Group ID': r.get('Security Group ID'),
            'Description': r.get('Description'),
            'Region': r.get('Region'),
            'Direction': r.get('Direction'),
            'Protocol': r.get('Protocol'),
            'Port Range': r.get('Port Range'),
            'Src Origin': src,
            'Src Parsed': sg_name_map.get(src, src),
            'Des Origin': dst,
            'Des Parsed': sg_name_map.get(dst, dst),
            'Src/Dst Description': r.get('Src/Dst Description'),
            'ENI ID': r.get('ENI ID'),
            'Private IP': r.get('Private IP')
        })

    return enriched

def map_sg_to_resources(session):
    ec2 = session.client('ec2')
    sg_rules = map_extract_all_sg_rules(session)
    sg_map = map_group_sg_rules_by_id(sg_rules)

    enis = exponential_backoff(ec2.describe_network_interfaces)['NetworkInterfaces']
    combined = []

    for eni in enis:
        eni_id = eni['NetworkInterfaceId']
        ip = eni.get('PrivateIpAddress', '-')
        interface_type = eni.get('InterfaceType', '-')
        description = eni.get('Description', '-')
        resource_id = eni.get('Attachment', {}).get('InstanceId') or description or '-'
        resource_type = map_infer_resource_type(description, interface_type)

        for sg in eni.get('Groups', []):
            sg_id = sg['GroupId']
            sg_name = sg['GroupName']
            rules = sg_map.get(sg_id, [{
                'Security Group Name': sg_name,
                'Security Group ID': sg_id,
                'Description': '-',
                'Region': session.region_name,
                'Direction': '-',
                'Protocol': '-',
                'Port Range': '-',
                'Src Origin': '-',
                'Des Origin': '-',
                'Src/Dst Description': '-'
            }])

            for rule in rules:
                combined.append({
                    **rule,
                    'ENI ID': eni_id,
                    'Private IP': ip,
                    'Resource ID': resource_id,
                    'Resource Type': resource_type
                })

    return enrich_sg_resource_result(session, combined)

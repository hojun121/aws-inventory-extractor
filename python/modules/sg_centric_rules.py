from modules.common import exponential_backoff

def map_sg_rules_with_resources(session):
    ec2 = session.client('ec2')
    region = session.region_name

    # SG ID → Name 매핑
    sg_response = exponential_backoff(ec2.describe_security_groups)
    sg_list = sg_response['SecurityGroups']
    sg_dict = {sg['GroupId']: sg for sg in sg_list}
    sg_name_map = {
        sg['GroupId']: next((tag['Value'] for tag in sg.get('Tags', []) if tag['Key'] == 'Name'), sg.get('GroupName', '-'))
        for sg in sg_list
    }

    # EC2 Resource ID → Name 매핑
    ec2_name_map = {}
    reservations = exponential_backoff(ec2.describe_instances).get("Reservations", [])
    for res in reservations:
        for inst in res.get("Instances", []):
            instance_id = inst.get("InstanceId")
            name = next((tag["Value"] for tag in inst.get("Tags", []) if tag["Key"] == "Name"), "-")
            ec2_name_map[instance_id] = name

    # ENI 정보 수집
    eni_response = exponential_backoff(ec2.describe_network_interfaces)
    eni_map = {}
    for eni in eni_response['NetworkInterfaces']:
        eni_id = eni.get('NetworkInterfaceId', '-')
        private_ip = eni.get('PrivateIpAddress', '-')
        description = eni.get('Description', '-')
        interface_type = eni.get('InterfaceType', '-')
        resource_id = eni.get('Attachment', {}).get('InstanceId') or description or '-'
        resource_type = infer_resource_type(description, interface_type)
        resource_name = ec2_name_map.get(resource_id, '-') if resource_type == 'EC2' else '-'

        for group in eni.get('Groups', []):
            sg_id = group['GroupId']
            eni_map.setdefault(sg_id, []).append({
                'ENI ID': eni_id,
                'Private IP': private_ip,
                'Resource ID': resource_id,
                'Resource Type': resource_type,
                'Resource Name': resource_name
            })

    result = []

    for sg in sg_list:
        sg_id = sg['GroupId']
        sg_name = sg_name_map.get(sg_id, '-')
        description = sg.get('Description', '-')
        usage_flag = sg_id in eni_map
        attached_resources = eni_map.get(sg_id, [{
            'ENI ID': '-',
            'Private IP': '-',
            'Resource ID': '-',
            'Resource Type': '-',
            'Resource Name': '-'
        }])

        def build_rule_rows(rules, direction):
            rows = []
            for rule in rules:
                protocol = rule.get('IpProtocol', '-')
                protocol = 'all' if protocol == '-1' else protocol
                from_port = rule.get('FromPort', '-')
                to_port = rule.get('ToPort', '-')
                port_range = f"{from_port}-{to_port}" if from_port != to_port else f"{from_port}"

                sources = []
                if direction == 'Inbound':
                    sources.extend([(ip.get('CidrIp', '-'), ip.get('Description', '-')) for ip in rule.get('IpRanges', [])])
                    sources.extend([(ip.get('CidrIpv6', '-'), ip.get('Description', '-')) for ip in rule.get('Ipv6Ranges', [])])
                    sources.extend([(group.get('GroupId', '-'), group.get('Description', '-')) for group in rule.get('UserIdGroupPairs', [])])
                else:
                    sources.extend([(ip.get('CidrIp', '-'), ip.get('Description', '-')) for ip in rule.get('IpRanges', [])])
                    sources.extend([(ip.get('CidrIpv6', '-'), ip.get('Description', '-')) for ip in rule.get('Ipv6Ranges', [])])
                    sources.extend([(group.get('GroupId', '-'), group.get('Description', '-')) for group in rule.get('UserIdGroupPairs', [])])

                for origin, origin_desc in sources:
                    parsed_name = sg_name_map.get(origin, origin)
                    for res in attached_resources:
                        row = {
                            'Security Group Name': sg_name,
                            'Security Group ID': sg_id,
                            'SG Description': description,
                            'Region': region,
                            'Usage': usage_flag,
                            'Direction': direction,
                            'Protocol': protocol,
                            'Port Range': port_range,
                            'Src Origin': origin if direction == 'Inbound' else '-',
                            'Src Parsed': parsed_name if direction == 'Inbound' else '-',
                            'Des Origin': origin if direction == 'Outbound' else '-',
                            'Des Parsed': parsed_name if direction == 'Outbound' else '-',
                            'Rules Src/Dst Description': origin_desc,
                            'Resource Name': res['Resource Name'],
                            'Resource ID': res['Resource ID'],
                            'Resource Type': res['Resource Type'],
                            'ENI ID': res['ENI ID'],
                            'Private IP': res['Private IP']
                        }
                        rows.append(row)
            return rows

        result.extend(build_rule_rows(sg.get('IpPermissions', []), 'Inbound'))
        result.extend(build_rule_rows(sg.get('IpPermissionsEgress', []), 'Outbound'))

    return result


def infer_resource_type(description, interface_type):
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

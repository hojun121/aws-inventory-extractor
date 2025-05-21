from modules.common import exponential_backoff

def map_sg_summary(session):
    ec2 = session.client('ec2')
    region = session.region_name

    # Fetch SG info
    sg_response = exponential_backoff(ec2.describe_security_groups)
    sg_list = sg_response['SecurityGroups']

    # Fetch ENI info and build SG → ENI map
    eni_response = exponential_backoff(ec2.describe_network_interfaces)
    sg_to_resources = {}

    for eni in eni_response['NetworkInterfaces']:
        eni_id = eni.get('NetworkInterfaceId', '-')
        private_ip = eni.get('PrivateIpAddress', '-')
        description = eni.get('Description', '-')
        interface_type = eni.get('InterfaceType', '-')
        resource_id = eni.get('Attachment', {}).get('InstanceId') or description or '-'
        resource_type = infer_resource_type(description, interface_type)

        for group in eni.get('Groups', []):
            sg_id = group['GroupId']
            sg_to_resources.setdefault(sg_id, []).append({
                'Resource ID': resource_id,
                'Resource Type': resource_type,
                'ENI ID': eni_id,
                'Private IP': private_ip
            })

    result = []

    for sg in sg_list:
        sg_id = sg['GroupId']
        sg_name = next((tag['Value'] for tag in sg.get('Tags', []) if tag['Key'] == 'Name'), sg.get('GroupName', '-'))
        description = sg.get('Description', '-')
        usage = sg_id in sg_to_resources
        resources = sg_to_resources.get(sg_id, [{'Resource ID': '-', 'Resource Type': '-', 'ENI ID': '-', 'Private IP': '-'}])

        for res in resources:
            result.append({
                'Security Group Name': sg_name,
                'Security Group ID': sg_id,
                'SG Description': description,
                'Region': region,
                'Usage': usage,
                'Resource Name': '-',
                'Resource ID': res['Resource ID'],
                'Resource Type': res['Resource Type'],
                'ENI ID': res['ENI ID'],
                'Private IP': res['Private IP']
            })

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
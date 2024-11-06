from modules.common import exponential_backoff

def list_vpcs(session):
    vpc_data = []
    try:
        ec2_client = session.client('ec2')
        vpcs = exponential_backoff(ec2_client.describe_vpcs)['Vpcs']

        for vpc in vpcs:
            vpc_id = vpc['VpcId']
            cidr_block = vpc['CidrBlock']
            dns_hostnames = vpc.get('EnableDnsHostnames', '-')

            # Find 'Name' tag
            name_tag = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Name'), 'Unnamed')

            # NAT Gateways
            nat_gateways = exponential_backoff(
                ec2_client.describe_nat_gateways,
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )['NatGateways']
            nat_gateway_ids = ', '.join([nat['NatGatewayId'] for nat in nat_gateways]) if nat_gateways else '-'

            # Internet Gateways
            internet_gateways = exponential_backoff(
                ec2_client.describe_internet_gateways,
                Filters=[{'Name': 'attachment.vpc-id', 'Values': [vpc_id]}]
            )['InternetGateways']
            internet_gateway_names = ', '.join([igw['InternetGatewayId'] for igw in internet_gateways]) if internet_gateways else '-'
            internet_gateway_ids = ', '.join([igw['InternetGatewayId'] for igw in internet_gateways]) if internet_gateways else '-'

            # Append the gathered data to the list
            vpc_data.append({
                'Name': name_tag,
                'ID': vpc_id,
                'VPC CIDR Block': cidr_block,
                'NAT Gateway': nat_gateway_ids,
                'Internet Gateways Name': internet_gateway_names,
                'Internet Gateways ID': internet_gateway_ids,
                'DNS Hostname': dns_hostnames
            })
    except Exception as e:
        print(f"Error retrieving VPCs: {e}")
    return vpc_data

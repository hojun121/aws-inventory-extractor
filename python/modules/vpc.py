from modules.common import exponential_backoff
import ipaddress

def list_vpcs(session):
    vpc_data = []
    try:
        # Get AWS account ID
        sts_client = session.client('sts')
        account_id = sts_client.get_caller_identity()["Account"]

        ec2_client = session.client('ec2')
        vpcs = exponential_backoff(ec2_client.describe_vpcs)['Vpcs']

        for vpc in vpcs:
            vpc_id = vpc['VpcId']
            cidr_block = vpc['CidrBlock']
            dns_hostnames = vpc.get('EnableDnsHostnames', '-')

            # Calculate total and available IPs in the CIDR block
            cidr = ipaddress.IPv4Network(cidr_block, strict=False)
            total_ips = cidr.num_addresses - 2  # Subtracting network and broadcast addresses

            # Get subnets in the VPC
            subnets = exponential_backoff(
                ec2_client.describe_subnets,
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )['Subnets']

            # Calculate available IPs in subnets
            available_ips = sum(subnet['AvailableIpAddressCount'] for subnet in subnets)

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
            internet_gateway_ids = ', '.join([igw['InternetGatewayId'] for igw in internet_gateways]) if internet_gateways else '-'

            # Append the gathered data to the list
            vpc_data.append({
                'AWS ID': account_id,
                'VPC Name': name_tag,
                'VPC ID': vpc_id,
                'VPC CIDR': cidr_block,
                'Total IPs': total_ips,
                'Available IPs': available_ips,
                'NAT Gateway IDs': nat_gateway_ids,
                'Internet Gateway IDs': internet_gateway_ids,
                'DNS Hostname': dns_hostnames
            })
    except Exception as e:
        print(f"Error retrieving VPCs: {e}")
    return vpc_data

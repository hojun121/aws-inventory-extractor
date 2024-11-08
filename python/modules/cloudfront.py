from modules.common import exponential_backoff

def list_cloudfront_distributions(session):
    cloudfront_data = []
    try:
        cloudfront_client = session.client('cloudfront')
        paginator = cloudfront_client.get_paginator('list_distributions')
        response_iterator = paginator.paginate()

        for response in response_iterator:
            distributions = response.get('DistributionList', {}).get('Items', [])

            for distribution in distributions:
                dist_id = distribution.get('Id', '-')
                alternate_domain_names = ', '.join(distribution.get('Aliases', {}).get('Items', [])) if distribution.get('Aliases', {}).get('Quantity', 0) > 0 else '-'
                security_policy = distribution.get('ViewerCertificate', {}).get('MinimumProtocolVersion', '-')
                waf_enabled = 'Enabled' if distribution.get('WebACLId') else 'Disabled'

                origin_items = distribution.get('Origins', {}).get('Items', [])
                for origin in origin_items:
                    origin_name = origin.get('Id', '-')
                    origin_domain = origin.get('DomainName', '-')
                    if 's3.amazonaws.com' in origin_domain or '.s3.' in origin_domain or origin_domain.endswith('.s3.amazonaws.com'):
                        origin_type = 'S3'
                    else:
                        origin_type = 'Custom'
                    origin_path = origin.get('OriginPath', '-')

                    cloudfront_data.append({
                        'Distribution ID': dist_id,
                        'Alternate Domain Name': alternate_domain_names,
                        'Security Policy': security_policy,
                        'WAF': waf_enabled,
                        'Origin Name': origin_name,
                        'Origin Type': origin_type,
                        'Origin Path': origin_path
                    })

    except Exception as e:
        print(f"Error retrieving CloudFront distributions: {e}")
    return cloudfront_data

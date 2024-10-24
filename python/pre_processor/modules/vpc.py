import pandas as pd


def transform_vpc_data(vpc_data, igw_data, ngw_data):
    try:
        def extract_vpc_id(attachments):
            try:
                if isinstance(attachments, list) and len(attachments) > 0:
                    return attachments[0].get('VpcId', '')  # 리스트의 첫 번째 요소에서 'VpcId' 추출
                else:
                    return ''
            except Exception as e:
                print(f"오류 발생: {e}")
                return ''

        igw_data['vpc_id'] = igw_data['attachments'].apply(extract_vpc_id)
        igw_data['igw_title'] = igw_data['title']
        ngw_data['vpc_id'] = ngw_data['vpc_id']

        vpc_data = vpc_data.merge(igw_data[['vpc_id', 'internet_gateway_id', 'igw_title']],
                                  on='vpc_id', how='left')

        vpc_data = vpc_data.merge(ngw_data[['vpc_id', 'nat_gateway_id']],
                                  on='vpc_id', how='left')

        vpc_data['internet_gateway_ids'] = vpc_data.groupby('vpc_id')['internet_gateway_id'].transform(
            lambda x: ', '.join(x.dropna().astype(str)) if not x.dropna().empty else "None"
        )

        vpc_data['nat_gateway_ids'] = vpc_data.groupby('vpc_id')['nat_gateway_id'].transform(
            lambda x: ', '.join(x.dropna().astype(str)) if not x.dropna().empty else "None"
        )

        vpc_data['DNS Resolution'] = "(Type Here)"
        vpc_data['DNS Hostname'] = "(Type Here)"

        vpc_data = vpc_data.drop_duplicates(subset='vpc_id')

        transformed_data = pd.DataFrame({
            'Name': vpc_data['title'],
            'ID': vpc_data['vpc_id'],
            'VPC CIDR Block': vpc_data['cidr_block'],
            'NAT Gateway': vpc_data['nat_gateway_ids'],
            'Internet Gateways Name': vpc_data['igw_title'],
            'Internet Gateways ID': vpc_data['internet_gateway_ids'],
            'DNS Resolution': vpc_data['DNS Resolution'],
            'DNS Hostname': vpc_data['DNS Hostname']
        })

        transformed_data = transformed_data.sort_values(by='Name', ascending=False)
    except Exception as e:
        print(f"vpc.py > transform_vpc_data(vpc_data, igw_data, ngw_data): {e}")
        return pd.DataFrame()

    return transformed_data


def load_and_transform_vpc_data(vpc_data, igw_data, ngw_data):
    return transform_vpc_data(vpc_data, igw_data, ngw_data)

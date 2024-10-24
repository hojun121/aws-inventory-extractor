import pandas as pd


def extract_items(aliases):
    try:
        if pd.isna(aliases) or not isinstance(aliases, dict):
            return ''

        items = aliases.get('Items', [])
        if isinstance(items, list):
            return ', '.join(items)
        else:
            return ''
    except Exception as e:
        print(f"cloudfront.py > extract_items(aliases, key): {e}")
        return ''


def extract_certificate(viewer_certificate):
    try:
        if pd.isna(viewer_certificate) or not isinstance(viewer_certificate, dict):
            return ''

        return viewer_certificate.get('Certificate', '')
    except Exception as e:
        print(f"cloudfront.py > extract_certificate(viewer_certificate, key): {e}")
        return ''


def extract_origin(origins):
    try:
        if pd.isna(origins):
            return ''

        if isinstance(origins, list):
            origin_names = [origin.get('DomainName', '') for origin in origins if 'DomainName' in origin]
            return ', '.join(origin_names)
        return ''
    except Exception as e:
        print(f"cloudfront.py > extract_origin(origins): {e}")
        return ''


def transform_cloudfront_data(cloudfront_data):
    try:
        transformed_data = pd.DataFrame({
            'Domain Name': cloudfront_data['domain_name'],
            'Alternate Domain Name': cloudfront_data['aliases'].apply(extract_items),
            'ID': cloudfront_data['id'],
            'Origin': cloudfront_data['origins'].apply(extract_origin),
            'SSL Certificate': cloudfront_data['viewer_certificate'].apply(extract_certificate),
            'Description': cloudfront_data['comment'],
        })

        transformed_data = transformed_data.sort_values(by='Domain Name', ascending=False)
    except Exception as e:
        print(f"cloudfront.py > transform_cloudfront_data: {e}")
        return pd.DataFrame()

    return transformed_data


def load_and_transform_cloudfront_data(cloudfront_data):
    return transform_cloudfront_data(cloudfront_data)

import pandas as pd


def extract_cross_zone(load_balancer_attributes):
    try:
        for attribute in load_balancer_attributes:
            if attribute['Key'] == 'load_balancing.cross_zone.enabled' and attribute['Value'].lower() == 'true':
                return 'Yes'
        return 'No'
    except Exception as e:
        print(f"elb.py > extract_cross_zone(): {e}")
        return ''


def extract_access_log(load_balancer_attributes):
    try:
        for attribute in load_balancer_attributes:
            if attribute['Key'] == 'access_logs.s3.enabled' and attribute['Value'].lower() == 'true':
                return 'Yes'
        return 'No'
    except Exception as e:
        print(f"elb.py > extract_access_log(): {e}")
        return ''


def extract_listener_from(arn, lbl_data):
    try:
        matching_rows = lbl_data[lbl_data['load_balancer_arn'] == arn]
        listen_from = matching_rows.apply(lambda row: f"{row['protocol']}:{row['port']}", axis=1)
        listen_from_str = "\n".join(listen_from)
        return listen_from_str if listen_from_str else ''

    except Exception as e:
        print(f"elb.py > extract_listener_from(): {e}")
        return ''


def extract_listener_to(arn, lbl_data):
    try:
        matching_rows = lbl_data[lbl_data['load_balancer_arn'] == arn]
        listen_to = []

        for _, row in matching_rows.iterrows():
            for action in row['default_actions']:
                if 'TargetGroupArn' in action:
                    target_group_arn = action['TargetGroupArn']
                    if target_group_arn:
                        target_group_name = target_group_arn.split('/')[-2]
                        listen_to.append(target_group_name)

        listen_to_str = "\n".join(listen_to)
        return listen_to_str if listen_to_str else ''

    except Exception as e:
        print(f"elb.py > extract_listener_to(arn, lbl_data): {e}")
        return ''


def format_tags(tags):
    try:
        if tags is not None:
            sorted_tags = sorted(tags.items(), key=lambda item: item[0])
            formatted_tags = ', '.join(f"{k}: {v}" for k, v in sorted_tags)
            return formatted_tags if formatted_tags else '-'
        else:
            return ''
    except Exception as e:
        print(f"ec2.py → format_tags() : {e}")
        return '-'


def transform_load_balancer_data(lb_data, elb_type, lbl_data):
    try:
        transformed_data = pd.DataFrame({
            'Name': lb_data['name'],
            'DNS Name': lb_data['dns_name'],
            'Type': elb_type,
            'State Code': lb_data['state_code'],
            'Region': lb_data['region'],
            'Availability Zone': lb_data['availability_zones'].apply(
                lambda x: ", ".join(sorted([az['ZoneName'] for az in x])) if isinstance(x, list) else ''),
            'Listener From': lb_data['arn'].apply(lambda arn: extract_listener_from(arn, lbl_data)),
            'Listener To': lb_data['arn'].apply(lambda arn: extract_listener_to(arn, lbl_data)),
            'Scheme': lb_data['scheme'],
            'Security Group': lb_data['security_groups'].apply(
                lambda x: ", ".join(x) if isinstance(x, list) else ''),
            'Cross-Zone Load Balancing': lb_data['load_balancer_attributes'].apply(extract_cross_zone),
            'Access Logs': lb_data['load_balancer_attributes'].apply(extract_access_log),
            'Tag': lb_data['tags'].apply(format_tags),
        })

        transformed_data = transformed_data.sort_values(by='Name', ascending=False)
    except Exception as e:
        print(f"elb.py > transform_load_balancer_data(): {e}")
        return pd.DataFrame()

    return transformed_data


def load_and_transform_elb_data(alb_data, nlb_data, lbl_data):
    data_frames = []

    if alb_data is not None:
        alb_data = transform_load_balancer_data(alb_data, 'application', lbl_data)
        data_frames.append(alb_data)

    if nlb_data is not None:
        nlb_data = transform_load_balancer_data(nlb_data, 'network', lbl_data)
        data_frames.append(nlb_data)

    combined_data = pd.concat(data_frames, ignore_index=True) if data_frames else pd.DataFrame()

    return combined_data

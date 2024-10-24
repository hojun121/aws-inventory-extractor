import pandas as pd


def extract_instances(instances):
    try:
        instance_list = [
            f"{instance.get('InstanceId', '')} ({instance.get('LifecycleState', '')})"
            for instance in instances if isinstance(instance, dict)
        ]

        return ', '.join(instance_list) if instance_list else 'None'

    except Exception as e:
        print(f"autoscaling.py > extract_instances(instances): {e}")
        return ''

def extract_launch_template(row):
    try:
        if row['launch_template_name']:
            return f"{row['launch_template_name']} (Version: {row['launch_template_name']})"
        elif row['launch_configuration_name']:
            return row['launch_configuration_name']
        return ''
    except Exception as e:
        print(f"autoscaling.py > extract_launch_template(row): {e}")
        return ''


def extract_az(availability_zones):
    az = sorted(set(availability_zones))
    return "\n".join(az)

def transform_autoscaling_data(autoscaling_data):
    try:
        transformed_data = pd.DataFrame({
            'Name': autoscaling_data['name'],
            'Launch template/configuration': autoscaling_data.apply(extract_launch_template, axis=1),
            'Instances': autoscaling_data['instances'].apply(extract_instances),
            'Desired Capacity': autoscaling_data['desired_capacity'],
            'Min': autoscaling_data['min_size'],
            'Max': autoscaling_data['max_size'],
            'AZ': autoscaling_data['availability_zones'].apply(extract_az)
        })

        transformed_data = transformed_data.sort_values(by='Name', ascending=False)
    except Exception as e:
        print(f"autoscaling.py > transform_autoscaling_data(autoscaling_data): {e}")
        return pd.DataFrame()

    return transformed_data

def load_and_transform_autoscaling_data(autoscaling_data):
    return transform_autoscaling_data(autoscaling_data)

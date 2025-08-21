import boto3

def lambda_handler(event, context):
    ec2_client = boto3.client('ec2')
    sns_client = boto3.client('sns')

    # Get all AMIs owned by self (with pagination)
    images = []
    paginator = ec2_client.get_paginator('describe_images')
    for page in paginator.paginate(Owners=['self']):
        images.extend(page['Images'])

    # Get all in-use AMIs from running instances
    instances = []
    paginator = ec2_client.get_paginator('describe_instances')
    for page in paginator.paginate():
        for reservation in page['Reservations']:
            for instance in reservation['Instances']:
                instances.append(instance['ImageId'])

    in_use_amis = set(instances)
    deregistered_amis = []
    deleted_snapshots = []

    for image in images:
        ami_id = image['ImageId']
        # Skip if AMI is in use
        if ami_id in in_use_amis:
            continue

        # Optional safeguard: skip AMIs tagged "DoNotDelete"
        tags = {t['Key']: t['Value'] for t in image.get('Tags', [])}
        if "DoNotDelete" in tags:
            continue

        # Deregister AMI
        ec2_client.deregister_image(ImageId=ami_id)
        deregistered_amis.append(ami_id)

        # Delete associated snapshots
        for mapping in image.get('BlockDeviceMappings', []):
            if 'Ebs' in mapping and 'SnapshotId' in mapping['Ebs']:
                snapshot_id = mapping['Ebs']['SnapshotId']
                try:
                    ec2_client.delete_snapshot(SnapshotId=snapshot_id)
                    deleted_snapshots.append(snapshot_id)
                except Exception as e:
                    print(f"Could not delete snapshot {snapshot_id}: {e}")

    # Send SNS notification
    if deregistered_amis:
        message = "The following AMIs have been deregistered:\n"
        for ami_id in deregistered_amis:
            message += f"- {ami_id}\n"
        if deleted_snapshots:
            message += "\nThe following snapshots were deleted:\n"
            for snap in deleted_snapshots:
                message += f"- {snap}\n"

        sns_client.publish(
            TopicArn="arn:aws:sns:ap-south-1:882026803767:Deregistered_AMI_Alerts", # replace with yours
            Message=message,
            Subject="Unused AMI Cleanup Alert"
        )

    return {
        'statusCode': 200,
        'body': 'AMI and snapshot cleanup completed.'
    }
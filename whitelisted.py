import boto3
   
def lambda_handler(event, context):
    # Retrieve whitelisted AMI IDs from DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('ami-table') # Change Dynamo Db table Name
    response = table.scan()
    whitelisted_amis = set(item.get('AMI_ID') for item in response['Items'] if 'AMI_ID' in item)


    # Check EC2 instances across all regions
    ec2_client = boto3.client('ec2')
    regions = ec2_client.describe_regions()['Regions']
    non_whitelisted_amis = []

    for region in regions:
        region_name = region['RegionName']
        ec2_client = boto3.client('ec2', region_name=region_name)
        response = ec2_client.describe_instances()

        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                ami_id = instance['ImageId']
                instance_id = instance['InstanceId']
                if ami_id not in whitelisted_amis:
                    non_whitelisted_amis.append((ami_id, instance_id, region_name))

    # Send email notification if non-whitelisted AMIs are found
    if non_whitelisted_amis:
        sns_client = boto3.client('sns')
        message = "Non-whitelisted AMI IDs found:\n"
        for ami_id, instance_id, region_name in non_whitelisted_amis:
            message += f"AMI ID: {ami_id}, Instance ID: {instance_id}, Region: {region_name}\n"
        sns_client.publish(
            TopicArn='arn:aws:sns:us-east-1:121174170074:Notifications_service', # Change Your SNS Topic 
            Message=message,
            Subject='Non-Whitelisted AMI IDs Alert'
        )

    return {
        'statusCode': 200,
        'body': 'AMI check completed.'
    }
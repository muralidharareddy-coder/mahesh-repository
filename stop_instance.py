import boto3
client = boto3.client('ec2')

response = client.stop_instances(
    InstanceIds=[
        'i-08dc4e0dea24d7559'
    ]
)
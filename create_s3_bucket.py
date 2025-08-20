import boto3

client = boto3.client('s3')

response = client.create_bucket(
    Bucket='muralibucket-20thaug-2025',
    CreateBucketConfiguration={
        'LocationConstraint': 'ap-southeast-1',
    },
)

print(response)
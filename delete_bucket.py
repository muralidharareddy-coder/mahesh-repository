import boto3

client = boto3.client('s3')

response = client.delete_bucket(
    Bucket='muralibucket-20thaug-2025',
    
)

print(response)
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    s3_client = boto3.client('s3')
    s3_resource = boto3.resource('s3')

    threshold_date = datetime.now().astimezone() - timedelta(days=30)

    response = s3_client.list_buckets()

    for bucket in response['Buckets']:
        bucket_name = bucket['Name']
        creation_date = bucket['CreationDate']

        # Check for DND tag safely
        dnd_tag_present = False
        try:
            tags = s3_client.get_bucket_tagging(Bucket=bucket_name).get('TagSet', [])
            dnd_tag_present = any(tag['Key'] == 'DND' for tag in tags)
        except ClientError as e:
            if e.response['Error']['Code'] != 'NoSuchTagSet':
                print(f"Error fetching tags for {bucket_name}: {e}")

        # If bucket is old and no DND tag
        if creation_date < threshold_date and not dnd_tag_present:
            try:
                # Empty the bucket first
                bucket_obj = s3_resource.Bucket(bucket_name)
                bucket_obj.objects.all().delete()
                bucket_obj.object_versions.all().delete()

                # Now delete bucket
                s3_client.delete_bucket(Bucket=bucket_name)
                print(f"✅ Deleted outdated bucket: {bucket_name}")
            except Exception as e:
                print(f"❌ Error deleting bucket {bucket_name}: {e}")

    return {
        'statusCode': 200,
        'body': 'S3 cleanup complete.'
    }
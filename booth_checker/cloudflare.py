import boto3

def s3_init(endpoint_url, access_key_id, access_key_secret):
    global s3
    s3 = boto3.client(
        service_name ="s3",
        endpoint_url = endpoint_url,
        aws_access_key_id = access_key_id,
        aws_secret_access_key = access_key_secret,
        region_name="apac",
        )

def s3_upload(file_path, bucket_name, object_name):
    s3.upload_file(
        file_path,
        bucket_name,
        object_name,
        ExtraArgs={'ContentType': 'text/html'}
    )
import boto3

class S3Uploader:
    def __init__(self, endpoint_url, access_key_id, secret_access_key):
        self.s3 = boto3.client(
            service_name="s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="apac",
        )

    def upload(self, file_path, bucket_name, object_name):
        self.s3.upload_file(
            file_path,
            bucket_name,
            object_name,
            ExtraArgs={'ContentType': 'text/html'}
        )
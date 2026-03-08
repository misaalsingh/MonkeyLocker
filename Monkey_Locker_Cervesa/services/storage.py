import os
import uuid
from typing import Optional
from datetime import datetime
from fastapi import UploadFile
from dotenv import load_dotenv
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

load_dotenv()

# Configuration
USE_S3 = os.getenv("USE_S3", "false").lower() == "true"
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
CLOUDFRONT_DOMAIN = os.getenv("CLOUDFRONT_DOMAIN")
LOCAL_UPLOAD_DIR = os.getenv("LOCAL_UPLOAD_DIR", "./uploaded_images")


class StorageService:
    def __init__(self):
        self.use_s3 = USE_S3
        
        if self.use_s3:
            import boto3
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=AWS_REGION,
                config=Config(signature_version='s3v4')
            )
            self.bucket_name = S3_BUCKET_NAME
        else:
            os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)
            self.upload_dir = LOCAL_UPLOAD_DIR
    
    def _generate_filename(self, original_filename: str, prefix: str = "") -> str:
        _, ext = os.path.splitext(original_filename)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}{ext}"
        
        if prefix:
            filename = f"{prefix.rstrip('/')}/{filename}"
        
        return filename
    
    async def upload_file(
        self,
        file: UploadFile,
        prefix: str = ""
    ) -> tuple[str, str]:
        filename = self._generate_filename(file.filename, prefix)
        
        content = await file.read()
        
        if self.use_s3:
            return await self._upload_to_s3(filename, content, file.content_type)
        else:
            return self._upload_to_local(filename, content)
    
    async def _upload_to_s3(self, filename: str, content: bytes, content_type: str) -> tuple[str, str]:
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=content,
                ContentType=content_type,
            )
            
            url = f"https://{self.bucket_name}.s3.{AWS_REGION}.amazonaws.com/{filename}"
            
            return filename, url
        
        except Exception as e:
            raise Exception(f"S3 upload failed: {str(e)}")
    
    def _upload_to_local(self, filename: str, content: bytes) -> tuple[str, str]:
        full_path = os.path.join(self.upload_dir, filename)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'wb') as f:
            f.write(content)
        
        url = f"/images/{filename}"
        
        return filename, url
    
    def delete_file(self, filename: str) -> bool:
        try:
            if self.use_s3:
                self.s3_client.delete_object(
                    Bucket=self.bucket_name,
                    Key=filename
                )
            else:
                full_path = os.path.join(self.upload_dir, filename)
                if os.path.exists(full_path):
                    os.remove(full_path)
            
            return True
        
        except Exception as e:
            print(f"Delete failed: {str(e)}")
            return False
    
    def get_file_url(self, filename: str, expires_in: int = 3600) -> str:
        if self.use_s3:
            # Prefer CloudFront URL — permanent, no expiry, served via CDN
            if CLOUDFRONT_DOMAIN:
                return f"https://{CLOUDFRONT_DOMAIN}/{filename}"
            # Fallback: presigned S3 URL (used before CloudFront is configured)
            try:
                return self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': filename},
                    ExpiresIn=expires_in
                )
            except ClientError:
                return f"https://{self.bucket_name}.s3.{AWS_REGION}.amazonaws.com/{filename}"
        else:
            return f"/images/{filename}"
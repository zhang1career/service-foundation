from django.db import models
from common.enums.content_type_enum import ContentTypeEnum


class MailAttachment(models.Model):
    """邮件附件模型"""
    id = models.BigAutoField(primary_key=True)
    
    # 所属邮件ID（通过程序维护关联关系）
    message_id = models.BigIntegerField(db_index=True)
    
    # 附件文件名
    filename = models.CharField(max_length=512)
    
    # MIME类型（ContentTypeEnum的ID）
    content_type = models.IntegerField(default=ContentTypeEnum.APPLICATION_OCTET_STREAM.value)
    
    # 附件大小（字节）
    size = models.BigIntegerField(default=0)
    
    # OSS存储路径（bucket/key格式）
    oss_bucket = models.CharField(max_length=255)
    oss_key = models.CharField(max_length=1024)
    
    # Content-ID（用于内嵌图片等）
    content_id = models.CharField(max_length=255, default="", blank=True)
    
    # Content-Disposition（attachment或inline）
    content_disposition = models.CharField(max_length=50, default="attachment")
    
    # 创建时间（UNIX时间戳，毫秒）
    ct = models.BigIntegerField(default=0, db_index=True)
    
    class Meta:
        db_table = "mail_attachment"
        indexes = [
            models.Index(fields=['message_id']),
            models.Index(fields=['oss_bucket', 'oss_key']),
        ]


from django.db import models


class MailMessage(models.Model):
    """邮件消息模型"""
    id = models.BigAutoField(primary_key=True)
    
    # 所属账户ID（通过程序维护关联关系）
    account_id = models.BigIntegerField(db_index=True)
    
    # 所属邮箱文件夹ID（通过程序维护关联关系）
    mailbox_id = models.BigIntegerField(db_index=True)
    
    # 邮件唯一标识（Message-ID）
    message_id = models.CharField(max_length=512, db_index=True)
    
    # 主题
    subject = models.TextField(default="")
    
    # 发件人
    from_address = models.CharField(max_length=512, db_column='from')
    
    # 收件人（多个用逗号分隔）
    to_addresses = models.TextField(default="", db_column='to')
    
    # 抄送（多个用逗号分隔）
    cc_addresses = models.TextField(default="", db_column='cc')
    
    # 密送（多个用逗号分隔）
    bcc_addresses = models.TextField(default="", db_column='bcc')
    
    # 邮件正文（文本）
    text_body = models.TextField(default="")
    
    # 邮件正文（HTML）
    html_body = models.TextField(default="")
    
    # 邮件日期（UNIX时间戳，毫秒）
    mt = models.BigIntegerField(db_index=True)
    
    # 是否已读
    is_read = models.BooleanField(default=False)
    
    # 是否已标记
    is_flagged = models.BooleanField(default=False)
    
    # 邮件大小（字节）
    size = models.BigIntegerField(default=0)
    
    # 原始邮件内容（可选，用于完整重建）
    raw_message = models.TextField(default="")
    
    # 创建时间（UNIX时间戳，毫秒）
    ct = models.BigIntegerField(default=0, db_index=True)
    
    # 更新时间（UNIX时间戳，毫秒）
    ut = models.BigIntegerField(default=0, db_index=True)
    
    class Meta:
        db_table = "mail_message"
        unique_together = [['account_id', 'message_id']]
        indexes = [
            models.Index(fields=['account_id', 'mailbox_id', 'mt']),
            models.Index(fields=['account_id', 'is_read']),
            models.Index(fields=['message_id']),
        ]


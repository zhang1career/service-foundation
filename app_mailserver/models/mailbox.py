from django.db import models


class Mailbox(models.Model):
    """邮箱文件夹模型"""
    id = models.BigAutoField(primary_key=True)
    
    # 所属账户ID（通过程序维护关联关系）
    account_id = models.BigIntegerField(db_index=True)
    
    # 文件夹名称（如：INBOX, Sent, Drafts, Trash等）
    name = models.CharField(max_length=100, db_index=True)
    
    # 文件夹路径（IMAP格式，如：INBOX, INBOX.Sent等）
    path = models.CharField(max_length=255, db_index=True)
    
    # 邮件数量
    message_count = models.IntegerField(default=0)
    
    # 未读邮件数量
    unread_count = models.IntegerField(default=0)
    
    # 创建时间（UNIX时间戳，毫秒）
    ct = models.BigIntegerField(default=0, db_index=True)
    
    # 更新时间（UNIX时间戳，毫秒）
    ut = models.BigIntegerField(default=0, db_index=True)

    class Meta:
        db_table = "mailbox"
        unique_together = [['account_id', 'path']]
        indexes = [
            models.Index(fields=['account_id', 'name']),
            models.Index(fields=['account_id', 'path']),
        ]


from django.db import models


class MailAccount(models.Model):
    """邮箱账户模型"""
    id = models.BigAutoField(primary_key=True)
    
    # 用户名（邮箱地址）
    username = models.CharField(max_length=255, unique=True, db_index=True)
    
    # 密码（加密存储）
    password = models.CharField(max_length=255)
    
    # 域名
    domain = models.CharField(max_length=255, db_index=True)
    
    # 是否激活
    is_active = models.BooleanField(default=True)
    
    # 创建时间（UNIX时间戳，毫秒）
    ct = models.BigIntegerField(default=0, db_index=True)
    
    # 更新时间（UNIX时间戳，毫秒）
    ut = models.BigIntegerField(default=0, db_index=True)

    class Meta:
        db_table = "mail_account"
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['domain']),
        ]


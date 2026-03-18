import aiosmtplib
from email.message import EmailMessage

from celery_app import celery
from conf.settings import settings


@celery.task(bind=True, name="tasks.send_mail")
def send_mail_task(self, to: str, subject: str, content: str):
    """
    用 Celery 后台任务异步发送邮件
    用 sync-to-async 方案适配 Celery Worker（不需要真的async worker）
    """
    import asyncio

    async def _send():
        msg = EmailMessage()
        msg["From"] = settings.MAIL_FROM
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(content)
        await aiosmtplib.send(
            msg,
            hostname=settings.MAIL_HOST,
            port=settings.MAIL_PORT,
            username=settings.MAIL_USER,
            password=settings.MAIL_PASS,
            use_tls=True,
        )

    try:
        asyncio.run(_send())
        return True
    except Exception as e:
        # 可记录日志或重试
        print(f"Send mail fail: {e}")
        return False

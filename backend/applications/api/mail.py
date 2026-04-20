import base64
import os
import re

from flask import Blueprint, request
from flask_mail import Message

from applications.common.utils.http import fail_api, success_api
from applications.extensions.init_mail import mail

mail_api = Blueprint('mail_api', __name__, url_prefix='/api/mail')


@mail_api.post('/send')
def send_mail():
    """
    发送邮件接口
    请求体:
      {
        "to": ["xxx@qq.com", ...],   // 收件人列表
        "subject": "邮件主题",
        "body": "正文（可选）",
        "image": "base64字符串（可选，截图附件）"
      }
    """
    req = request.json
    if not req:
        return fail_api("请求参数为空")

    to_list = req.get("to")
    if not to_list or not isinstance(to_list, list) or len(to_list) == 0:
        return fail_api("请指定收件人")

    # 简单校验邮箱格式
    email_pattern = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
    for addr in to_list:
        if not email_pattern.match(addr):
            return fail_api(f"邮箱格式不正确: {addr}")

    subject = req.get("subject", "滨海湿地变化监测 - 变化信息通报")
    body = req.get("body", "您好，请查收附件中的湿地变化检测结果截图。")
    image_b64 = req.get("image")  # base64图片（可选）

    try:
        msg = Message(
            subject=subject,
            recipients=to_list,
            body=body
        )

        # 如果有截图则作为附件发送
        if image_b64:
            # 去掉 data:image/png;base64, 前缀
            if ',' in image_b64:
                image_b64 = image_b64.split(',', 1)[1]
            img_bytes = base64.b64decode(image_b64)
            msg.attach(
                filename="变化检测结果.png",
                content_type="image/png",
                data=img_bytes
            )

        mail.send(msg)
        return success_api("邮件发送成功")
    except Exception as e:
        return fail_api(f"邮件发送失败: {str(e)}")

"""
모니터링 및 관리에 필요한 훅
"""

import boto3

ses_client = boto3.client("ses")


def email_alert(email, title, h1="", p=""):
    """
    - email: 전송 대상 이메일
    - name: 이메일 이름
    - h1: 메일 본문에 들어갈 타이틀
    - p: 메일 본문에 들어갈 내용
    """
    html_body = f"""
    <html>
        <head></head>
        <body>
            <h1>{h1}</h1>
            <p>{p}</p>
        </body>
    </html>
    """

    ses_client.send_email(
        Source="no-reply@econox.io",
        Destination={"ToAddresses": [email]},
        Message={
            "Body": {
                "Html": {
                    "Charset": "UTF-8",
                    "Data": html_body,
                },
            },
            "Subject": {
                "Charset": "UTF-8",
                "Data": title,
            },
        },
    )

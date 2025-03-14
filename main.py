import argparse
import datetime
import hashlib
import json
import os
import re
import subprocess
from dotenv import load_dotenv
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from smtplib import SMTP

def parse_args() -> argparse.Namespace:
    # def str_convert_to_datetime(date_str: str) -> datetime:
    #     return datetime.datetime.strptime(date_str, "%Y%m")

    arg_parser = argparse.ArgumentParser()
    # arg_parser.add_argument(
    #     "claim_date",
    #     type=str_convert_to_datetime,
    #     help="Claim date (YYYYmm)"
    # )
    arg_parser.add_argument(
        "config",
        type=str,
        help="Config"
    )

    return arg_parser.parse_args()

def load_config(config_path: str) -> dict:
    with open(config_path, encoding="utf-8", mode="r") as file:
        res = json.load(file)

    return res

def load_template(template_path: str) -> str:
    with open(template_path, encoding="utf-8", mode="r") as file:
        return file.read().replace("\r", "")


def replace_template(template: str, config: dict) -> str:
    res = template
    for key, value in config.items():
        if key != "details":
            if type(value) is str:
                res = res.replace(f"{{{key}}}", str(value).replace("\r", "").replace("\n", "<br/>"))
        else:
            sum = 0
            details = ""
            for item in value:
                name = item["name"]
                unit = int(item["unit"])
                qty = int(item["qty"])
                value = unit * qty

                details += f"<tr><td>{name}</td><td>{unit:,}</td><td>{qty:,}</td><td>{value:,}</td></tr>"
                sum += value
            res = res.replace("{details}", details)
            res = res.replace("{sum}", f"{sum:,}")

    res = res.replace("{hash}", f"{hashlib.sha512(config["claimee_name_long"].encode()).hexdigest()}<br/>{hashlib.sha512(res.encode()).hexdigest()}")

    if re.search(r"\{[a-zA-Z0-9_]*\}", res):
        raise ValueError("Some keys in the template are not replaced.")

    return res

def create_email_body(
        claim_date: datetime,
        addressee_display_name: str,
        addresser_display_name: str,
        signature: str) -> str:
    return f"""
{addressee_display_name}

いつもお世話になっております。
{addresser_display_name}でございます。

平素より弊サービスをご利用くださり誠にありがとうございます。
{claim_date}分の請求額が確定いたしましたので、請求書を送付させていただきます。
ご確認および期日までのお支払いをお願いいたします。

今後とも弊サービスをよろしくお願いいたします。

--------------------------------------------------
本メールはシステムより自動送信されています。
また、本アドレスは送信専用のため、ご返信いただきましても確認できません。
ご用の場合は以下にご連絡をいただけますと幸いです。

{signature}
""".strip()

def create_mime_multipart(
        subject: str,
        body: str,
        address_from: str,
        address_to: str) -> MIMEMultipart:
    message = MIMEMultipart()
    message["Subject"] = subject
    message["From"] = address_from
    message["To"] = address_to
    message["Date"] = formatdate()
    message.attach(MIMEText(body.strip(), "plain", "utf-8"))

    return message

def attach_file_to_mime_multipart(message: MIMEMultipart, file_path: str) -> MIMEMultipart:
    with open(file_path, "rb") as file:
        attachment = MIMEApplication(file.read())
    attachment.add_header("Content-Disposition", "attachment", filename=os.path.basename(file_path))
    message.attach(attachment)

    return message

def send_mail(message: MIMEMultipart) -> None:
    host = os.environ["SMTP_HOST"]
    port = int(os.environ["SMTP_PORT"])
    password = os.environ["SMTP_PASSWORD"]

    with SMTP(host, port, timeout=10) as server:
        server.starttls()
        try:
            server.login(message["From"], password)
        except:
            print("Failed to login to the email-server.")
            return
        server.send_message(message)

def main():
    # Load .env file
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

    # Parse arguments
    args = parse_args()

    # Load config
    config = load_config(args.config)
    claim_date_ym_for_file_name = f"{datetime.datetime.strptime(config["claim_date_ym"], "%Y/%m"):%Y%m}"
    config["claim_date_ym"] = f"{datetime.datetime.strptime(config["claim_date_ym"], "%Y/%m"):%Y年%m月}"
    config["today_date_ymd"] = f"{datetime.datetime.now():%Y年%m月%d日}"

    # Load template HTML
    template = load_template(os.path.join(os.path.dirname(__file__), "template.html"))

    # Write claim HTML
    doc_html_path = os.path.join(os.path.dirname(__file__), "claims", f"claim_{config["claimee_name_short"]}_{claim_date_ym_for_file_name}.html")
    with open(doc_html_path, "w", encoding="utf-8") as file:
        file.write(replace_template(template, config))

    # Write claim PDF
    doc_pdf_path = os.path.join(os.path.dirname(__file__), "claims", f"claim_{config["claimee_name_short"]}_{claim_date_ym_for_file_name}.pdf")
    print(f"{os.path.join(os.environ["CHROME_PATH"], "chrome")} --headless --print-to-pdf={doc_pdf_path} {doc_html_path}".replace("\\", "/"))
    subprocess.run(f"{os.path.join(os.environ["CHROME_PATH"], "chrome")} --headless --print-to-pdf={doc_pdf_path} {doc_html_path}".replace("\\", "/"))

    # Send e-mail
    send_mail(
        attach_file_to_mime_multipart(
            create_mime_multipart(
                subject=f"請求書送付（{config["claim_date_ym"]}分）",
                body=create_email_body(
                    claim_date=config["claim_date_ym"],
                    addressee_display_name=f"{config["claimee_name_short"]}\n財務ご担当者様",
                    addresser_display_name=config["claimer_name_short"],
                    signature=config["signature"],
                ),
                address_from=f"{os.environ["SMTP_USER"]}@{config["claimer_email"].split("@")[1]}",
                address_to=config["claimee_email"],
            ),
            doc_pdf_path
        )
    )

if __name__ == "__main__":
    main()

import logging
import os
from datetime import datetime
from datetime import timezone

import azure.functions as func
import psycopg2
import requests


def main(msg: func.ServiceBusMessage):
    try:
        logging.info(datetime.now(tz=timezone.utc))
        notification_id = int(msg.get_body().decode("utf-8"))
        logging.info(
            "Python ServiceBus queue trigger processed message: %s", notification_id
        )

        db_name = os.getenv("dbName")
        db_user = os.getenv("dbUser")
        db_password = os.getenv("dbPassword")
        db_host = os.getenv("dbHost")
        db_port = os.getenv("dbPort")
        if not (db_name and db_user and db_password and db_host and db_port):
            sanitized_password = "xxx" if db_password else db_password
            log_string = f"Read the following insufficient connection details from environment: dbName:\"{db_name or 'None'}\", dbUser:\"{db_user or 'None'}\", dbPassword:\"{sanitized_password or 'None'}\", dbHost:\"{db_host or 'None'}\", dbPort:\"{db_port or 'None'}\"."
            raise Exception(log_string)

        mailjet_api_key = os.getenv("mailjetApiKey")
        mailjet_api_secret = os.getenv("mailjetApiSecret")
        mailjet_url = os.getenv("mailjetUrl")
        if not (mailjet_api_key and mailjet_api_secret and mailjet_url):
            log_string = f"Couldn't read mailjetApiKey, mailjetApiSecret or mailjet_url from environmen."
            raise Exception(log_string)
        mailjet_auth = (mailjet_api_key, mailjet_api_secret)

        with psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
        ) as conn:

            sql = "SELECT subject, message FROM notification WHERE id=%s"
            with conn.cursor() as cur:
                cur.execute(sql, [notification_id])
                res = cur.fetchone()
            if not res:
                log_string = f"Couldn't find notification with id {notification_id}."
                raise Exception(log_string)
            subject, message = res

            sql = "SELECT first_name, last_name, email FROM attendee"
            with conn.cursor() as cur:
                cur.execute(sql, [notification_id])
                email_messages = []
                for attendee_count, (first_name, last_name, email_address) in enumerate(
                    cur, 1
                ):
                    full_name = first_name + " " + last_name
                    personalized_subject = f"Dear {full_name}, {subject}"
                    email_messages.append(
                        {
                            "From": {
                                "Email": "udacity_course@eon-orchestra.com",
                                "Name": "info@techconf.com",
                            },
                            "To": [{"Email": email_address, "Name": full_name}],
                            "Subject": personalized_subject,
                            "HTMLPart": message,
                        }
                    )
                    logging.info(
                        f'Sending email with subject "{personalized_subject}" and body "{message}" to {email_address}.'
                    )
            res = requests.post(
                mailjet_url, auth=mailjet_auth, json={"messages": email_messages}
            )
            res.raise_for_status()

            sql = (
                "UPDATE notification SET status = %s, completed_date = %s WHERE id = %s"
            )
            with conn.cursor() as cur:
                compiled_sql = cur.mogrify(
                    sql,
                    [
                        f"Notified {attendee_count} attendees",
                        datetime.now(tz=timezone.utc),
                        notification_id,
                    ],
                )
                cur.execute(compiled_sql)
                logging.info(f"Executed \"{compiled_sql.decode('utf-8')}\".")

    except Exception as error:
        logging.error(error)

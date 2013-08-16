import textwrap

from mock import Mock
from nose.tools import assert_equal
from django.core.mail.message import EmailMessage

from ..mail import DjangoEmailBackend

class TestDjangoEmailBackend(object):
    def simple_test(self):
        dj_msg = EmailMessage(subject="Hello", body="World",
                              from_email="from@example.com",
                              to=["a@example.com", "b@example.com"],
                              cc=["cc@example.com"])
        mail_backend = DjangoEmailBackend()
        mail_backend.get_hub = Mock()
        mail_backend.send_messages([dj_msg])
        sent_messages = mail_backend.get_hub().send_many.call_args[0][0]
        mail_message = sent_messages[0].as_msg()["mail_message"]
        mail_message.pop("id")
        mail_message["body"] = "\n".join([
            line for line in mail_message["body"].splitlines()
            if not any(line.startswith(x) for x in ["Date", "Message-ID"])
        ])
        assert_equal(mail_message, {
            "from": "from@example.com",
            "to": ["a@example.com", "b@example.com"],
            "body":  textwrap.dedent("""\
                Content-Type: text/plain; charset="utf-8"
                MIME-Version: 1.0
                Content-Transfer-Encoding: quoted-printable
                Subject: Hello
                From: from@example.com
                To: a@example.com, b@example.com
                Cc: cc@example.com

                World"""
            )
        })


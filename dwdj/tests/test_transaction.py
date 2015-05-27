from django.test import TestCase
from django.db import transaction

from helper_project.models import HelperModel

from ..transaction import table_lock

class TableLockTestCase(TestCase):
    def test_table_lock_no_transaction(self):
        with table_lock(HelperModel, "EXCLUSIVE"):
            pass

    def test_table_lock_in_transaction(self):
        with transaction.atomic():
            with table_lock(HelperModel, "EXCLUSIVE"):
                pass

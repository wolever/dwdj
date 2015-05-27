from django.db import connections, DEFAULT_DB_ALIAS, transaction

class table_lock(object):
    """ A context manager for PostgreSQL table locking::

        with table_lock(models.BankAccount, "EXCLUSIVE"):
            a = models.BankAccount.objects.get(id=1)
            b = models.BankAccount.objects.get(id=2)
            a.balance += 100
            b.balance -= 100
            a.save()
            b.save()
    """

    LOCK_MODES = set([
        "ACCESS SHARE",
        "ROW SHARE",
        "ROW EXCLUSIVE",
        "SHARE UPDATE EXCLUSIVE",
        "SHARE",
        "SHARE ROW EXCLUSIVE",
        "EXCLUSIVE",
        "ACCESS EXCLUSIVE",
    ])

    def __init__(self, model, mode, using=None):
        if mode.upper() not in self.LOCK_MODES:
            raise ValueError("invalid lock mode: %r" %(mode, ))
        self.model = model
        self.mode = mode
        self.using = using
        self.cxn = None
        self.txn = None

    def __enter__(self):
        assert self.cxn is None, "lock already acquired"
        self.cxn = transaction.get_connection(self.using)
        if not self.cxn.in_atomic_block:
            self.txn = transaction.atomic(using=self.using)
            self.txn.__enter__()
        self.cur = self.cxn.cursor()
        self.cur.execute("LOCK TABLE %s IN %s MODE" %(
            self.model._meta.db_table, self.mode,
        ))

    def __exit__(self, *exc):
        if self.txn is not None:
            self.txn.__exit__(*exc)

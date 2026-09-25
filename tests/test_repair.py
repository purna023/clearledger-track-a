import csv
import io
import tempfile
import unittest
from pathlib import Path

from ledger import importing, reporting, storage


class RepairTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = storage.connect(Path(self.tmp.name) / 'repair.sqlite3')
        storage.seed(self.db)

    def tearDown(self):
        self.db.close()
        self.tmp.cleanup()

    def test_invoice_identity_is_idempotent_and_conflicts_are_rejected(self):
        same = importing.import_csv(
            self.db,
            'customer_id,invoice_number,amount,due_date\nHARBOR,INV-100,1250.00,2026-09-01\n',
            'invoices')
        conflict = importing.import_csv(
            self.db,
            'customer_id,invoice_number,amount,due_date\nHARBOR,INV-100,999.99,2026-10-01\n',
            'invoices')
        self.assertEqual((same['imported'], same['skipped']), (0, 1))
        self.assertEqual(conflict['rejected'], 1)
        self.assertEqual(self.db.execute(
            'SELECT COUNT(*) FROM invoices WHERE customer_id=? AND invoice_number=?',
            ('HARBOR', 'INV-100')).fetchone()[0], 1)

    def test_payment_matches_customer_and_invoice_reference_not_amount(self):
        result = importing.import_csv(
            self.db,
            'payment_id,customer_id,invoice_number,amount\nP-EXACT,HARBOR,INV-101,1250.00\n',
            'payments')
        self.assertEqual(result['imported'], 1)
        payment = self.db.execute(
            'SELECT invoice_id FROM payments WHERE payment_id=?', ('P-EXACT',)).fetchone()
        invoice = self.db.execute(
            'SELECT id FROM invoices WHERE customer_id=? AND invoice_number=?',
            ('HARBOR', 'INV-101')).fetchone()
        self.assertEqual(payment['invoice_id'], invoice['id'])

    def test_mixed_rows_keep_valid_rows_and_report_line_number(self):
        result = importing.import_csv(
            self.db,
            'customer_id,invoice_number,amount,due_date\n'
            'HARBOR,GOOD-1,10.00,2026-09-20\n'
            'BAD,BAD-1,20.00,2026-09-21\n'
            'HARBOR,GOOD-2,11.00,2026-09-21\n',
            'invoices')
        self.assertEqual(result['imported'], 2)
        self.assertEqual(result['rejected'], 1)
        self.assertEqual(result['errors'][0]['line'], 3)

    def test_open_and_paid_filters_are_disjoint(self):
        open_rows = reporting.invoices(self.db, 'open')
        paid_rows = reporting.invoices(self.db, 'paid')
        self.assertEqual(len(open_rows), 5)
        self.assertEqual(len(paid_rows), 1)
        self.assertTrue(all(r['status'] == 'open' for r in open_rows))
        self.assertTrue(all(r['status'] == 'paid' for r in paid_rows))

    def test_export_preserves_two_decimal_places(self):
        importing.import_csv(
            self.db,
            'customer_id,invoice_number,amount,due_date\nHARBOR,CENT-29,0.29,2026-09-20\n',
            'invoices')
        row = next(r for r in reporting.export_csv(self.db).splitlines() if 'CENT-29' in r)
        self.assertEqual(row.split(',')[2], '0.29')


if __name__ == '__main__':
    unittest.main()

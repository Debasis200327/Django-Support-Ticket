import json
import tempfile
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, Client, override_settings
from django.urls import reverse

PNG = b'\x89PNG\r\n\x1a\n' + b'0' * 100
VALID = {
    'trainee_name': 'Debasis', 'email': 'debasis@example.com',
    'category': 'Django', 'severity': 'High',
    'description': 'My Django form is not submitting properly.',
}


class SupportDeskTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.data_file = Path(self.tmp.name) / 'tickets.jsonl'
        ov = override_settings(DATA_FILE=self.data_file, MEDIA_ROOT=self.tmp.name)
        ov.enable()
        self.addCleanup(ov.disable)
        self.client = Client()
        self.url = reverse('supportdesk:ticket_create')

    def post(self, **over):
        return self.client.post(self.url, {**VALID, **over})

    def test_valid_submission_and_jsonl(self):
        r = self.post()
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.cookies['last_ticket_category'].value, 'Django')
        lines = self.data_file.read_text().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertEqual(json.loads(lines[0])['email'], 'debasis@example.com')

    def test_invalid_inputs(self):
        for bad in ({'email': 'nope'}, {'description': 'short'},
                    {'category': 'Hack'}, {'severity': 'Extreme'}):
            r = self.post(**bad)
            self.assertEqual(r.status_code, 200, bad)
        self.assertFalse(self.data_file.exists())

    def test_screenshot_rules(self):
        ok = SimpleUploadedFile('a.png', PNG, 'image/png')
        self.assertEqual(self.post(screenshot=ok).status_code, 302)
        pdf = SimpleUploadedFile('a.pdf', b'%PDF-1.4', 'application/pdf')
        self.assertEqual(self.post(screenshot=pdf).status_code, 200)
        fake = SimpleUploadedFile('a.png', b'not really a png', 'image/png')
        self.assertEqual(self.post(screenshot=fake).status_code, 200)
        big = SimpleUploadedFile('b.png', PNG + b'0' * (2 * 1024 * 1024), 'image/png')
        self.assertEqual(self.post(screenshot=big).status_code, 200)

    def test_cookie_preselects_category(self):
        self.client.cookies['last_ticket_category'] = 'Python'
        r = self.client.get(self.url)
        self.assertContains(r, '<option value="Python" selected>')

    def test_request_id_changes(self):
        a = self.client.get(self.url)['X-Request-ID']
        b = self.client.get(self.url)['X-Request-ID']
        self.assertNotEqual(a, b)

    def test_ajax_priority_and_restrictions(self):
        url = reverse('supportdesk:priority_checker')
        self.assertEqual(self.client.get(url).status_code, 405)
        body = json.dumps({'severity': 'Critical',
                           'description': 'Production is completely down now'})
        strict = Client(enforce_csrf_checks=True)
        self.assertEqual(strict.post(url, body, content_type='application/json').status_code, 403)
        r = self.client.post(url, body, content_type='application/json')
        self.assertEqual(r.json()['suggested_priority'], 'Urgent')
        bad = self.client.post(url, '{bad', content_type='application/json')
        self.assertEqual(bad.status_code, 400)

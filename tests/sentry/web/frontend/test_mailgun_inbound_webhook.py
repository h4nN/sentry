from __future__ import absolute_import, print_function

import mock

from django.core.urlresolvers import reverse

from sentry.testutils import TestCase
from sentry.utils.email import group_id_to_email

body_plain = "foo bar"


class TestMailgunInboundWebhookView(TestCase):
    def setUp(self):
        super(TestMailgunInboundWebhookView, self).setUp()
        self.event = self.create_event(event_id='a' * 32)
        self.mailto = group_id_to_email(self.group.pk)

    @mock.patch('sentry.web.frontend.mailgun_inbound_webhook.process_inbound_email')
    def test_invalid_signature(self, process_inbound_email):
        resp = self.client.post(reverse('sentry-mailgun-inbound-hook'), {
            'To': 'Sentry <%s>' % (self.mailto,),
            'From': 'David <%s>' % (self.user.email,),
            'body-plain': body_plain,
            'signature': '',
            'token': '',
            'timestamp': '',
        })
        assert resp.status_code == 403

    @mock.patch('sentry.web.frontend.mailgun_inbound_webhook.process_inbound_email')
    def test_simple(self, process_inbound_email):
        token = 'a' * 50
        timestamp = '1422513193'
        signature = '436688eb38038505394ff31e621c1e4c61b26b09638016b6d630d6199aa48403'

        resp = self.client.post(reverse('sentry-mailgun-inbound-hook'), {
            'To': 'Sentry <%s>' % (self.mailto,),
            'From': 'David <%s>' % (self.user.email,),
            'body-plain': body_plain,
            'signature': signature,
            'token': token,
            'timestamp': timestamp,
        })
        assert resp.status_code == 201
        process_inbound_email.delay.assert_called_once_with(
            self.user.email,
            self.group.id,
            body_plain,
        )

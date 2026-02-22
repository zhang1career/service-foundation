from django.views.generic import TemplateView


class MailAccountListView(TemplateView):
    template_name = 'console/mail/accounts.html'


class MailboxListView(TemplateView):
    template_name = 'console/mail/mailboxes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account_id'] = kwargs.get('account_id')
        return context

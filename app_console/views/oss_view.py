from django.views.generic import TemplateView


class OssBrowserView(TemplateView):
    template_name = 'console/oss/browser.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bucket'] = self.request.GET.get('bucket', '')
        context['prefix'] = self.request.GET.get('prefix', '')
        return context

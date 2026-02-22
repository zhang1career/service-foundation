from django.views.generic import TemplateView


class KnowListView(TemplateView):
    template_name = 'console/know/list.html'


class KnowDetailView(TemplateView):
    template_name = 'console/know/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entity_id'] = kwargs.get('entity_id')
        return context


class KnowRelationshipView(TemplateView):
    template_name = 'console/know/relationships.html'


class KnowSummaryView(TemplateView):
    template_name = 'console/know/summaries.html'

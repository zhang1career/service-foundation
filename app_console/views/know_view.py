from django.views.generic import TemplateView
from django.http import Http404
from django.test import Client
import json


def _format_ts(ts):
    """Format timestamp (ms) for display."""
    if not ts or ts <= 0:
        return '-'
    from datetime import datetime
    try:
        dt = datetime.fromtimestamp(ts / 1000.0)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, OSError):
        return '-'


class KnowListView(TemplateView):
    template_name = 'console/know/list.html'


class KnowDetailView(TemplateView):
    template_name = 'console/know/detail.html'

    def get(self, request, *args, **kwargs):
        entity_id = kwargs.get('entity_id')
        if not entity_id or entity_id <= 0:
            raise Http404('无效的批次 ID')
        entity_id = int(entity_id)
        # 通过 app_know 的 API 获取数据，不直接访问数据库
        client = Client()
        resp = client.get(f'/api/know/knowledge/{entity_id}')
        if resp.status_code != 200:
            raise Http404(f'批次 {entity_id} 不存在')
        try:
            result = json.loads(resp.content.decode('utf-8'))
        except json.JSONDecodeError:
            raise Http404(f'批次 {entity_id} 不存在')
        if result.get('errorCode') != 0 or not result.get('data'):
            raise Http404(f'批次 {entity_id} 不存在')
        self.batch_data = result['data']
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entity_id'] = kwargs.get('entity_id')
        context['batch_data'] = getattr(self, 'batch_data', None)
        if context['batch_data']:
            context['batch_data']['ct_fmt'] = _format_ts(context['batch_data'].get('ct'))
            context['batch_data']['ut_fmt'] = _format_ts(context['batch_data'].get('ut'))
        return context


class KnowRelationshipView(TemplateView):
    template_name = 'console/know/relationships.html'


class KnowSummaryView(TemplateView):
    template_name = 'console/know/summaries.html'


class KnowPerspectiveView(TemplateView):
    template_name = 'console/know/perspectives.html'


class KnowInsightView(TemplateView):
    template_name = 'console/know/insights.html'

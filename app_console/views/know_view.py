from django.http import Http404
from django.views.generic import TemplateView

from app_know.repos.batch_repo import get_batch_detail
from app_know.utils.knowledge_point_dict import get_knowledge_point_detail_dict


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


class KnowPointDetailView(TemplateView):
    """知识详情：单条知识点（knowledge 表一行）。"""
    template_name = 'console/know/point_detail.html'

    def get(self, request, *args, **kwargs):
        point_id = kwargs.get('point_id')
        if not point_id or point_id <= 0:
            raise Http404('无效的知识 ID')
        point_id = int(point_id)
        data = get_knowledge_point_detail_dict(point_id)
        if not data:
            raise Http404(f'知识 {point_id} 不存在')
        self.point_data = data
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['point_id'] = kwargs.get('point_id')
        context['point_data'] = getattr(self, 'point_data', None)
        if context['point_data']:
            d = context['point_data']
            d['ct_fmt'] = _format_ts(d.get('ct'))
            d['ut_fmt'] = _format_ts(d.get('ut'))
        return context


class KnowPointEditView(TemplateView):
    """知识编辑：单条知识点的编辑页。"""
    template_name = 'console/know/point_edit.html'

    def get(self, request, *args, **kwargs):
        point_id = kwargs.get('point_id')
        if not point_id or point_id <= 0:
            raise Http404('无效的知识 ID')
        point_id = int(point_id)
        data = get_knowledge_point_detail_dict(point_id)
        if not data:
            raise Http404(f'知识 {point_id} 不存在')
        self.point_data = data
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from app_console.utils import get_edit_return_context
        context = super().get_context_data(**kwargs)
        point_id = kwargs.get('point_id')
        context['point_id'] = point_id
        point_data = getattr(self, 'point_data', None)
        context['point_data'] = point_data
        # 保证 stage=0 时下拉能正确选中（模板里 |default:'' 会把 0 当假值）
        if point_data and point_data.get('stage') is not None:
            context['initial_stage'] = str(point_data['stage'])
        else:
            context['initial_stage'] = ''
        if point_data and point_data.get('classification') is not None:
            context['initial_classification'] = str(point_data['classification'])
        else:
            context['initial_classification'] = ''
        context.update(get_edit_return_context(
            list_url_name='console:know-list',
            list_label='返回知识列表',
        ))
        return context


class KnowInsightView(TemplateView):
    template_name = 'console/know/insights.html'


class KnowBatchListView(TemplateView):
    """批次列表：从 app_know batches API 获取数据"""
    template_name = 'console/know/batch_list.html'


class KnowBatchDetailView(TemplateView):
    """批次详情：从 app_know batch detail API 获取数据"""
    template_name = 'console/know/batch_detail.html'

    def get(self, request, *args, **kwargs):
        entity_id = kwargs.get('entity_id')
        if not entity_id or entity_id <= 0:
            raise Http404('无效的批次 ID')
        entity_id = int(entity_id)
        batch_data = get_batch_detail(entity_id)
        if not batch_data:
            raise Http404(f'批次 {entity_id} 不存在')
        self.batch_data = batch_data
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entity_id'] = kwargs.get('entity_id')
        context['batch_data'] = getattr(self, 'batch_data', None)
        show_know_list_btn = False
        if context['batch_data']:
            context['batch_data']['ct_fmt'] = _format_ts(context['batch_data'].get('ct'))
            context['batch_data']['ut_fmt'] = _format_ts(context['batch_data'].get('ut'))
            try:
                sc = int(context['batch_data'].get('sentence_count') or 0)
            except (TypeError, ValueError):
                sc = 0
            context['batch_data']['sentence_count'] = sc
            show_know_list_btn = sc > 0
        context['show_know_list_btn'] = show_know_list_btn
        return context


class KnowBatchEditView(TemplateView):
    """批次编辑：仅支持来源类型为文字（source_type=0）的批次"""
    template_name = 'console/know/batch_edit.html'

    def get(self, request, *args, **kwargs):
        entity_id = kwargs.get('entity_id')
        if not entity_id or entity_id <= 0:
            raise Http404('无效的批次 ID')
        entity_id = int(entity_id)
        batch_data = get_batch_detail(entity_id)
        if not batch_data:
            raise Http404(f'批次 {entity_id} 不存在')
        if batch_data.get('source_type') != 0:
            from django.shortcuts import redirect
            return redirect('console:know-batch-detail', entity_id=entity_id)
        self.batch_data = batch_data
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        from app_console.utils import get_edit_return_context
        context = super().get_context_data(**kwargs)
        entity_id = kwargs.get('entity_id')
        context['entity_id'] = entity_id
        context['batch_data'] = getattr(self, 'batch_data', None)
        if context['batch_data']:
            context['batch_data']['ct_fmt'] = _format_ts(context['batch_data'].get('ct'))
            context['batch_data']['ut_fmt'] = _format_ts(context['batch_data'].get('ut'))
        context.update(get_edit_return_context(
            list_url_name='console:know-batch-list',
            list_label='返回批次列表',
        ))
        return context

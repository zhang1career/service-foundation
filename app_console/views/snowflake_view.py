from django.views.generic import TemplateView


class SnowflakeView(TemplateView):
    template_name = 'console/snowflake/generator.html'

# app_know URL configuration. Generated.
from django.urls import path

from common.views.atlas_repl_view import AtlasReplView
from app_know.views.knowledge_view import (
    KnowledgeListView,
    KnowledgeListItemsView,
    KnowledgePointDetailView,
    KnowledgeDetailView,
    KnowledgeSomeLikeView,
)
from app_know.views.query_view import LogicalQueryView
from app_know.views.relation_extract_view import (
    RelationExtractView,
    RelationGraphEdgeUpdateView,
    RelationGraphNodeUpdateView,
    RelationGraphView,
    RelationSaveView,
)
from app_know.views.relationship_view import RelationshipListView, RelationshipDetailView
from app_know.views.summary_view import (
    KnowledgeSummaryView,
    KnowledgeSummaryListView,
)
from app_know.views.sentence_view import SentenceListView
from app_know.views.extract_view import (
    KnowledgeExtractView,
    SentenceGraphView,
    ExtractBriefView,
    AnalyzeComponentsView,
    SaveComponentsView,
    Neo4jCypherView,
)
from app_know.views.perspective_view import PerspectiveListView
from app_know.views.parse_view import KnowledgeParseView
from app_know.views.insight_view import (
    InsightListView,
    InsightDetailView,
    InsightGenerateView,
)
from app_know.views.batch_view import (
    BatchListView,
    BatchDetailView,
    BatchCreateTextView,
    BatchCreateUploadView,
    BatchAnalyzeView,
)
from app_know.views.dict_view import DictView

urlpatterns = [
    path("atlas_repl", AtlasReplView.as_view(), name="atlas-repl"),
    path("dict", DictView.as_view(), name="dict"),
    path("knowledge", KnowledgeListView.as_view(), name="knowledge-list"),
    path("knowledge/items", KnowledgeListItemsView.as_view(), name="knowledge-list-items"),
    path("knowledge/points/<int:point_id>", KnowledgePointDetailView.as_view(), name="knowledge-point-detail"),
    path("knowledge/points/<int:point_id>/extract_brief", ExtractBriefView.as_view(), name="knowledge-point-extract-brief"),
    path("knowledge/points/<int:point_id>/analyze_components", AnalyzeComponentsView.as_view(), name="knowledge-point-analyze-components"),
    path("knowledge/points/<int:point_id>/save_components", SaveComponentsView.as_view(), name="knowledge-point-save-components"),
    path("neo4j_cypher", Neo4jCypherView.as_view(), name="neo4j-cypher"),
    path("batches", BatchListView.as_view(), name="batch-list"),
    path("batches/add_text", BatchCreateTextView.as_view(), name="batch-add-text"),
    path("batches/upload", BatchCreateUploadView.as_view(), name="batch-upload"),
    path("batches/<int:entity_id>", BatchDetailView.as_view(), name="batch-detail"),
    path("batches/<int:entity_id>/analyze", BatchAnalyzeView.as_view(), name="batch-analyze"),
    path("knowledge/some_like", KnowledgeSomeLikeView.as_view(), name="knowledge-query-by-summary"),
    path("knowledge/<int:entity_id>", KnowledgeDetailView.as_view(), name="knowledge-detail"),
    path(
        "knowledge/<int:entity_id>/summary",
        KnowledgeSummaryView.as_view(),
        name="knowledge-summary",
    ),
    path(
        "knowledge/<int:entity_id>/parse",
        KnowledgeParseView.as_view(),
        name="knowledge-parse",
    ),
    path(
        "knowledge/<int:entity_id>/sentences",
        SentenceListView.as_view(),
        name="knowledge-sentences",
    ),
    path(
        "knowledge/<int:entity_id>/extract_sentences",
        KnowledgeExtractView.as_view(),
        name="knowledge-extract-sentences",
    ),
    path(
        "knowledge/<int:entity_id>/sentence_graph",
        SentenceGraphView.as_view(),
        name="knowledge-sentence-graph",
    ),
    path(
        "knowledge/<int:entity_id>/extract_relations",
        RelationExtractView.as_view(),
        name="knowledge-extract-relations",
    ),
    path(
        "knowledge/<int:entity_id>/save_relation",
        RelationSaveView.as_view(),
        name="knowledge-save-relation",
    ),
    path(
        "knowledge/<int:entity_id>/relation_graph",
        RelationGraphView.as_view(),
        name="knowledge-relation-graph",
    ),
    path(
        "knowledge/<int:entity_id>/graph_node",
        RelationGraphNodeUpdateView.as_view(),
        name="knowledge-graph-node-update",
    ),
    path(
        "knowledge/<int:entity_id>/graph_edge",
        RelationGraphEdgeUpdateView.as_view(),
        name="knowledge-graph-edge-update",
    ),
    path(
        "knowledge/summaries",
        KnowledgeSummaryListView.as_view(),
        name="knowledge-summary-list",
    ),
    path("knowledge/query", LogicalQueryView.as_view(), name="knowledge-query"),
    path("knowledge/relationships", RelationshipListView.as_view(), name="relationship-list"),
    path(
        "knowledge/relationships/<int:relationship_id>",
        RelationshipDetailView.as_view(),
        name="relationship-detail",
    ),
    path("perspectives", PerspectiveListView.as_view(), name="perspective-list"),
    path("insights", InsightListView.as_view(), name="insight-list"),
    path("insights/generate", InsightGenerateView.as_view(), name="insight-generate"),
    path("insights/<int:insight_id>", InsightDetailView.as_view(), name="insight-detail"),
]

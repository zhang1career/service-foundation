# app_know URL configuration. Generated.
from django.urls import path

from app_know.views.atlas_repl_view import AtlasReplView
from app_know.views.knowledge_view import KnowledgeListView, KnowledgeDetailView
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

urlpatterns = [
    path("atlas_repl", AtlasReplView.as_view(), name="atlas-repl"),
    path("knowledge", KnowledgeListView.as_view(), name="knowledge-list"),
    path("knowledge/<int:entity_id>", KnowledgeDetailView.as_view(), name="knowledge-detail"),
    path(
        "knowledge/<int:entity_id>/summary",
        KnowledgeSummaryView.as_view(),
        name="knowledge-summary",
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
]

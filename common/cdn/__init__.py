"""
CDN abstraction layer

Provides protocol/interface for CDN operations compatible with Amazon CloudFront.
Implementations (e.g. app_cdn) can replace CloudFront for local/self-hosted usage.
"""
from common.cdn.protocol import CdnProviderProtocol

__all__ = ["CdnProviderProtocol"]

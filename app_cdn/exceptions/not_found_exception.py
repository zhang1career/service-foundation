"""Resource not found exception"""

from app_cdn.exceptions.cdn_exception import CdnException


class DistributionNotFoundException(CdnException):
    """Distribution not found"""

    def __init__(self, distribution_id: str):
        self.distribution_id = distribution_id
        super().__init__(f"Distribution not found: {distribution_id}")


class InvalidationNotFoundException(CdnException):
    """Invalidation not found"""

    def __init__(self, distribution_id: str, invalidation_id: str):
        self.distribution_id = distribution_id
        self.invalidation_id = invalidation_id
        super().__init__(
            f"Invalidation not found: {invalidation_id} for distribution {distribution_id}"
        )

from unittest import TestCase

from app_aibroker.enums.model_capability_enum import ModelCapabilityEnum
from common.enums.aigc_invoke_op_enum import AigcInvokeOp


class ModelCapabilityEnumAigcInvokeOpTests(TestCase):
    def test_all_supported_capabilities(self):
        self.assertIs(ModelCapabilityEnum.aigc_invoke_op(0), AigcInvokeOp.CHAT)
        self.assertIs(ModelCapabilityEnum.aigc_invoke_op(1), AigcInvokeOp.IMAGE)
        self.assertIs(ModelCapabilityEnum.aigc_invoke_op(2), AigcInvokeOp.VIDEO)
        self.assertIs(ModelCapabilityEnum.aigc_invoke_op(3), AigcInvokeOp.EMBEDDING)

    def test_invalid_capability(self):
        with self.assertRaises(ValueError) as ctx:
            ModelCapabilityEnum.aigc_invoke_op(99)
        self.assertIn("invalid", str(ctx.exception).lower())

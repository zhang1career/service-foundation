from unittest import TestCase

from common.apis.aigcbest_api import AigcBestAPI


class TestAigcBestAPI(TestCase):
    def setUp(self):
        pass

    def test_claude(self):
        self.dut = AigcBestAPI("https://api2.aigcbest.top/v1",
                               "sk-fc8FSYKW2AkAKiKbA1536003Ec944549A65b5cD53660Bb9a",
                               "claude-sonnet-4-20250514")

        content = """
Regarding the content enclosed by triple backticks, please answer the question:
what component or ingredient of technology does this text mainly involve?

If you do not know how to answer, please answer 'no'.

```
chip stocks took a hit after a Wall Street Journal report indicated the US wants to revoke waivers from top global semiconductor manufacturers used for accessing American technology in China. Nvidia (NVDA) fell around 1.1%.
```

Notes:
1. Just answer only the key words, not any complete sentence.
"""
        answer = self.dut.chat(content, 0)
        print()
        print(answer)

    def test_4o(self):
        self.dut = AigcBestAPI("https://api2.aigcbest.top/v1",
                               "sk-fc8FSYKW2AkAKiKbA1536003Ec944549A65b5cD53660Bb9a",
                               "gpt-4o-mini-2024-07-18")

        content = """
Regarding the content enclosed by triple backticks, please answer the question:
What is the conclusion?

```
Looking at the content provided, I can see it mentions "chip stocks" and specifically "Nvidia (NVDA)" as a stock that fell.

From the given options, none of them are directly mentioned in the text. The content discusses chip stocks and Nvidia specifically, but doesn't mention any of the financial indicators listed (S&P 500, interest rates, market indices, commodities, or currencies).

The most appropriate financial indicators that are directly mentioned would be:

Nvidia, chip stocks
```

Notes:
1. Just answer only the key words, not any complete sentence.
"""
        answer = self.dut.chat(content, 0)
        print()
        print(answer)

    def test_comment_financial_news(self):
        self.dut = AigcBestAPI("https://api2.aigcbest.top/v1",
                               "sk-fc8FSYKW2AkAKiKbA1536003Ec944549A65b5cD53660Bb9a",
                               "gpt-4o-mini-2024-07-18")
        content = """
Based on the news factors and financial result listed below, please summarize the attribution statement for the result:

Factors:
  * Trump said that he had struck a trade deal with Vietnam that will allow American goods to enter the country duty-free, while Vietnamese goods will face 20% tariffs, and trans-shipments from third countries through Vietnam will face a 40% levy.

Result:
    The S&P 500 rose 0.5% Wednesday and set an all-time high for the third time in four days.

Notes:
1. The summary should be as general as possible and the quantitative elements in the news factors should be appropriately reduced.
"""
        answer = self.dut.chat(content, 0.15)
        print()
        print(answer)

    def test_(self):
        self.dut = AigcBestAPI("https://api2.aigcbest.top/v1",
                               "sk-fc8FSYKW2AkAKiKbA1536003Ec944549A65b5cD53660Bb9a",
                               "gpt-4o-mini-2024-07-18")
        content = """
You are a technical analysis assistant.

Your task is to analyze the following technical document written in Chinese, enclosed by triple backticks. From the text, extract:
1. **field**: the main technical term (e.g., a register name, a variable name)
2. **feature**: the purpose or function of the field
3. **feature_detail**: a dictionary that maps specific values assigned to the field to their respective functional meanings

The output must be a JSON-formatted string with the following structure:
{
  "field": "<extracted field name>",
  "feature": "<description of what the field does>",
  "feature_detail": {
    "<description 1>": "<value 1>",
    "<description 2>": "<value 2>",
    ...
  }
}

If you cannot extract any value-description mapping, set "feature_detail" to an empty dictionary: `{}`.
If you cannot extract any of the three elements (`field`, `feature`, or `feature_detail`), just answer 'no'.

```
s2xlate 用来区分 TLB 项的类型。根据 s2xlate 的不同，TLB 项目存储的内容也有所不同。

类型 | s2xlate
=============
noS2xlate | b00
allStage | b11
onlyStage1 | b01
onlyStage2 | b10
```
"""
        answer = self.dut.chat(content, 0.15)
        print()
        print(answer)

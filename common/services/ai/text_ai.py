import logging

from common.apis.aigcbest_api import AigcBestAPI
from common.components.singleton import Singleton
from common.consts.string_const import STRING_EMPTY
from common.exceptions.ai_exception import UnexpectedAnswerException
from common.utils.string_util import explode, check_blank

logger = logging.getLogger(__name__)


################################
# single choice
################################

PROMPT_SINGLE_CHOICE = """Regarding the content enclosed by triple backticks, please answer the question:
Which of the following options is most appropriate for {question}:
{options}
{additional_question}
```
{text}
```

Notes:
1. Each option is prefixed by '☐', a symbol. This symbol should not appear in your answer.
2. If you have selected one option, answer the option itself — no need to say more words.
"""

PROMPT_SINGLE_CHOICE_EXTEND = """
Or, if any new, appropriate option has not been mentioned above, what is it?
If you believe the answer is not in the options and cannot provide a more appropriate option, please answer 'no'.
"""

PROMPT_SINGLE_CHOICE_DEBUG = """
Or, if you cannot find any appropriate one from the options, try to explain the reason.
"""

################################
# multiple choice
################################

PROMPT_MULTIPLE_CHOICE = """Regarding the content enclosed by triple backticks, please answer the question:
Which of the following options are appropriate for {question}:
{options}
{additional_question}
```
{text}
```

Notes:
1. Each option is prefixed by '☐', a symbol. This symbol should not appear in your answer.
2. If you have selected some options, answer the options themselves, join them with comma — no need to say more words.
"""

PROMPT_MULTIPLE_CHOICE_EXTEND = """
Or, if any new, appropriate options have not been mentioned above, what are they?
If you believe the answer is not in the options and cannot provide some more appropriate options, please answer 'no'.
"""

PROMPT_MULTIPLE_CHOICE_DEBUG = """
Or, if you cannot find any appropriate ones from the options, try to explain the reasons.
"""

################################
# true or false
################################

PROMPT_TRUE_OR_FALSE = """Regarding the content enclosed by triple backticks, please answer the question:
Is it true or false, that {assertion}?
{additional_question}
```
{text}
```

Notes:
1. Just answer 'true' or 'false'. No need to say more words.
"""

PROMPT_TRUE_OR_FALSE_EXTEND = """
If you are not sure it is true or false, please answer 'no'.
"""

PROMPT_TRUE_OR_FALSE_DEBUG = """
Or, if you are not sure it is true or false, try to explain the reason.
"""

################################
# ask and answer
################################

PROMPT_ASK_AND_ANSWER = """You are a {role} assistant.

Regarding the content enclosed by triple backticks, please {question}
{additional_question}

```
{text}
```
"""

PROMPT_ASK_AND_ANSWER_KEYWORD = """Regarding the content enclosed by triple backticks, please answer the question:
{question}?
{additional_question}
```
{text}
```

Notes:
1. Just answer only the key words, not any complete sentence.
"""

PROMPT_ASK_AND_ANSWER_EXTEND = """
If you do not know how to answer, please answer 'no'.
"""

PROMPT_ASK_AND_ANSWER_DEBUG = """
Or, if you do not know how to answer, try to explain the reason.
"""


class TextAI(Singleton):
    def __init__(self, url: str, token: str, model: str, is_debug: bool = False):
        self._llm = AigcBestAPI(url, token, model)
        self._is_debug = is_debug

    def single_choice_question(self,
                               text: str,
                               question: str,
                               option_list: list[str],
                               temperature=0) -> tuple[str, str]:
        """
        Chat for a single choice question.
        @param text: 题干
        @param question: 提问
        @param option_list: 选择项
        @param temperature:
        """
        # prepare data
        options = _build_options(option_list)
        # build prompt
        prompt = PROMPT_SINGLE_CHOICE.format(
            text=text,
            question=question,
            options=options,
            additional_question=PROMPT_SINGLE_CHOICE_DEBUG if self._is_debug else PROMPT_SINGLE_CHOICE_EXTEND
        )
        logger.debug("[ai][text][single_choice] prompt=%s", prompt)
        result = self._llm.chat(prompt, temperature)
        if result == "no":
            raise UnexpectedAnswerException(prompt)
        logger.debug("[ai][text][single_choice] result=%s", result)
        return prompt, result.strip()

    def multiple_choice_question(self,
                                 text: str,
                                 question: str,
                                 option_list: list[str],
                                 temperature=0) -> tuple[str, list[str]]:
        """
        Chat for a multiple choice question.
        @param text: 题干
        @param question: 提问
        @param option_list: 选择项
        @param temperature:
        """
        prompt, result = self.multiple_choice_question_with_raw_result(text, question, option_list, temperature)
        return prompt, [s.strip() for s in explode(result)]

    def multiple_choice_question_with_raw_result(self,
                                                 text: str,
                                                 question: str,
                                                 option_list: list[str],
                                                 temperature=0) -> tuple[str, str]:
        """
        Chat for a multiple choice question with raw result.
        @param text: 题干
        @param question: 提问
        @param option_list: 选择项
        @param temperature:
        """
        # prepare data
        options = _build_options(option_list)
        # build prompt
        prompt = PROMPT_MULTIPLE_CHOICE.format(
            text=text,
            question=question,
            options=options,
            additional_question=PROMPT_MULTIPLE_CHOICE_DEBUG if self._is_debug else PROMPT_MULTIPLE_CHOICE_EXTEND
        )
        logger.debug("[ai][text][multiple_choice] prompt=%s", prompt)
        result = self._llm.chat(prompt, temperature)
        if result == "no":
            raise UnexpectedAnswerException(prompt)
        logger.debug("[ai][text][multiple_choice] result=%s", result)
        return prompt, result

    def true_or_false_question(self,
                               text: str,
                               assertion: str,
                               temperature=0) -> tuple[str, bool]:
        """
        Chat for a true or false question.
        @param text:
        @param assertion: 断言
        @param temperature:
        """
        # prepare data
        # build prompt
        prompt = PROMPT_TRUE_OR_FALSE.format(
            text=text,
            assertion=assertion,
            additional_question=PROMPT_TRUE_OR_FALSE_DEBUG if self._is_debug else PROMPT_TRUE_OR_FALSE_EXTEND
        )
        logger.debug("[ai][text][true_or_false] prompt=%s", prompt)
        result = self._llm.chat(prompt, temperature)
        if result == "no":
            raise UnexpectedAnswerException(prompt)
        logger.debug("[ai][text][true_or_false] result=%s", result)
        return prompt, result.lower() == "true"

    def ask_and_answer(self,
                       text: str,
                       role: str,
                       question: str,
                       additional_question: str = STRING_EMPTY,
                       temperature=0) -> tuple[str, str]:
        """
        Ask a question and get an answer.
        @param text:
        @param role:
        @param question:
        @param additional_question:
        @param temperature:
        """
        # prepare data
        _additional_question = additional_question.strip()
        if check_blank(_additional_question):
            _additional_question = PROMPT_ASK_AND_ANSWER_DEBUG if self._is_debug else PROMPT_ASK_AND_ANSWER_EXTEND
        # build prompt
        prompt = PROMPT_ASK_AND_ANSWER.format(
            role=role,
            text=text,
            question=question,
            additional_question=_additional_question
        )
        logger.debug("[ai][text][ask_and_answer] prompt=%s", prompt)
        result = self._llm.chat(prompt, temperature)
        if result == "no":
            raise UnexpectedAnswerException(prompt)
        logger.debug("[ai][text][ask_and_answer] result=%s", result)
        return prompt, result

    def ask_and_answer_keyword(self,
                               text: str,
                               question: str,
                               temperature=0) -> tuple[str, str]:
        """
        Ask a question and get an keyword as the answer.
        @param text:
        @param question:
        @param temperature:
        """
        # prepare data
        # build prompt
        prompt = PROMPT_ASK_AND_ANSWER_KEYWORD.format(
            text=text,
            question=question,
            additional_question=PROMPT_ASK_AND_ANSWER_DEBUG if self._is_debug else PROMPT_ASK_AND_ANSWER_EXTEND
        )
        logger.debug("[ai][text][ask_and_answer_keyword] prompt=%s", prompt)
        result = self._llm.chat(prompt, temperature)
        if result == "no":
            raise UnexpectedAnswerException(prompt)
        logger.debug("[ai][text][ask_and_answer_keyword] result=%s", result)
        return prompt, result


def _build_options(option_list: list[str]) -> str:
    """
    Build a list of options.
    ["A correlation with market capitalization", "A correlation with global trade"] ->
    ["  ☐ A correlation with market capitalization.", "  ☐ A correlation with global trade."]
    """
    options = ["  ☐ {opt}".format(opt=opt) for opt in option_list]
    return '\n'.join(options)

from common.utils.string_util import explode


def get_first_paragraph(text: str, paragraph_num: int = 0):
    """
    Get partial paragraph from text
    @param text:
    @param paragraph_num:
    @return:
    """
    if not text:
        return None
    paragraph_list = explode(text, "\n")
    if not paragraph_list:
        return None
    if paragraph_num >= len(paragraph_list):
        return None

    paragraph = paragraph_list[paragraph_num]
    if not paragraph:
        return None
    # remove appended "\r"
    paragraph = remove_appending(paragraph, "\r")
    return paragraph


def remove_appending(text: str, char: str):
    """
    Remove the appending char from text

    @param text:
    @param char:
    @return:
    """
    if text.endswith(char):
        text = text[:-len(char)]
    return text

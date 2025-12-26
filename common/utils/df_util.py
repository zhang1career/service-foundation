from pandas import DataFrame

from common.exceptions.argument_exception import IllegalArgumentException


def extract_column_and_combine(df_list: list[DataFrame], head: str, index: str, extract: str):
    """
    Extract a column from DataFrame list with name and index, and combine to a new DataFrame

    @param df_list:
    @param head:
    @param index:
    @param extract:
    @return: a new DataFrame
    """
    # lazy load
    from pandas import concat as pd_concat

    combined_df = DataFrame()

    for df in df_list:
        # Ensure the dataframe has the required columns
        if not {head, extract, index}.issubset(df.columns):
            raise ValueError("Input DataFrame must contain {head}, {extract}, and {index} columns"
                             .format(head=head, extract=extract, index=index))

        # Set ['index'] as the index
        df.set_index(index, inplace=True)

        # Extract ['head'] and ['extract'] columns
        head_value = df[head].iloc[0]
        extract_series = df[extract]

        # Rename the series to the symbol
        extract_series.name = head_value

        # Combine the series into the new DataFrame
        combined_df = pd_concat([combined_df, extract_series], axis=1)

    return combined_df


def extract_row_and_combine(df_list: list[DataFrame], index: str, extract: int):
    """
    Extract a row from DataFrame list with index, and combine to a new DataFrame

    @param df_list:
    @param index: which column's value is used as new DataFrame's index
    @param extract: row number to be extracted, 0 represents the first row, and -1 represents the last row
    @return: a new DataFrame
    """
    extracted_rows = []
    for df in df_list:
        _extracted_row = df.iloc[extract]
        extracted_rows.append(_extracted_row)

    combined_df = DataFrame(extracted_rows)
    combined_df.set_index(index, inplace=True)

    return combined_df


def check_empty(df: DataFrame) -> bool:
    if df is None:
        return True
    if not isinstance(df, DataFrame):
        raise IllegalArgumentException("argument {arg} should be a DataFrame".format(arg="df"))

    return df.empty


def df_of_dict_list(record_list: list[dict], column_name: list):
    """
    Make DataFrame from dict list
    @param record_list:
    @param column_name: column name
    @return:
    """
    df = DataFrame(record_list, columns=column_name)
    return df

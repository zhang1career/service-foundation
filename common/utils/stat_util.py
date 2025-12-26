def calculate_rising_rates(df) -> dict:
    """
    Calculate rising rate of last two value
    @param df:
    @return: rising rate of each column
    """
    rising_rates = {}
    for column in df.columns:
        # Get the last two values in the column
        last_two_values = df[column].iloc[-2:]

        # Calculate the rising rate:
        previous, latest = last_two_values
        if len(last_two_values) != 2:
            rising_rates[column] = None
            continue
        rising_rate = ((latest - previous) / previous) * 100

        # Store the rising rate in the dictionary
        rising_rates[column] = rising_rate
    return rising_rates

from pandas import DataFrame


def plot_value_time_line(df: DataFrame,
                         title="", subtitle="", footnote="",
                         width=10, height=10,
                         output_file="output.jpg"):
    """
    Plot value-time line image by DataFrame

    @param df:
    @param title:
    @param width:
    @param height:
    @param output_file:
    """
    ax = df.plot(kind="line", title=title,
                 # y=["open", "close", "high", "low"], ylabel="USD",
                 figsize=(width, height))
    ax.figure.savefig(output_file)

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter, DayLocator
from pandas import DataFrame

from common.consts.image_const import (
    MAIN_GREEN_85,
    MAIN_GREY_10,
    MAIN_GREY_30,
    LINE_GREY_85,
    HEAVY_COLOR_SERIES,
    BACK_GROUND_HEAVY_COLOR, RED_60, GREEN_55,
)


def plot_value_time_line(df: DataFrame,
                         title="", subtitle="", footnote="",
                         width=10, height=10,
                         output_file="output.jpg"):
    """
    Plot value-time line image by DataFramefigure

    @param df: DataFrame, indicied by datetime, columned by stock's price
    @param title:
    @param subtitle:
    @param footnote:
    @param width:
    @param height:
    @param output_file:
    """
    # Setup plot tools
    matplotlib.rcParams["text.color"] = MAIN_GREY_10
    matplotlib.rcParams['axes.labelcolor'] = MAIN_GREY_30
    matplotlib.rcParams['xtick.color'] = MAIN_GREY_30
    matplotlib.rcParams['ytick.color'] = MAIN_GREY_30

    column_list = df.columns.tolist()

    # Setup plot size
    fig, ax = plt.subplots(figsize=(width, height))
    # Create grid
    # Zorder tells it which layer to put it on.
    # We are setting this to 1 and our data to 2 so the grid is behind the data.
    ax.grid(which="major", axis="y", color=LINE_GREY_85, alpha=0.6, zorder=1)

    # Plot data
    for i in range(0, len(column_list), 1):
        _column_name = column_list[i]
        _column_value = df[_column_name]
        ax.plot(_column_value, label=_column_name, color=HEAVY_COLOR_SERIES[i], alpha=0.8, linewidth=3)
    # Set Legend
    ax.legend(column_list, loc=(0.04, 0.6), ncol=2, frameon=True, handletextpad=.2, handleheight=.8)

    # Remove splines. Can be done one at a time or can slice with a list.
    ax.spines[["top", "right", "left"]].set_visible(False)

    # Set xlim to fit data without going over plot area
    ax.set_xlim(df.index[0], df.index[-1])
    # Reformat x-axis tick labels
    ax.xaxis.set_tick_params(labelsize=11)  # Set tick label size
    ax.xaxis.set_major_locator(DayLocator(interval=5))
    ax.xaxis.set_major_formatter(DateFormatter("%m-%d"))
    # Make space for and rotate the x-axis tick labels
    fig.autofmt_xdate()

    # Reformat y-axis tick labels
    # ax.set_yticklabels(np.arange(0, 25, 5),  # Set labels again
    #                    ha="right",  # Set horizontal alignment to right
    #                    verticalalignment="bottom")  # Set vertical alignment to make labels on top of gridline
    ax.yaxis.set_tick_params(pad=-2,  # Pad tick labels so they don"t go over y-axis
                             labeltop=True,  # Put x-axis labels on top
                             labelbottom=False,  # Set no x-axis labels on bottom
                             bottom=False,  # Set no ticks on bottom
                             labelsize=11)  # Set tick label size

    # Add in line and tag
    ax.plot([0.12, .9],  # Set width of line
            [.98, .98],  # Set height of line
            transform=fig.transFigure,  # Set location relative to plot
            clip_on=False,
            color=MAIN_GREEN_85,
            linewidth=.6)
    ax.add_patch(plt.Rectangle((0.12, .98),  # Set location of rectangle by lower left corder
                               0.04,  # Width of rectangle
                               -0.02,  # Height of rectangle. Negative so it goes down.
                               facecolor=MAIN_GREEN_85,
                               transform=fig.transFigure,
                               clip_on=False,
                               linewidth=0))

    # Add in title and subtitle
    ax.__repr__(x=0.12, y=.91, s=title, transform=fig.transFigure, ha="left", fontsize=13, weight="bold", alpha=.8)
    ax.__repr__(x=0.12, y=.86, s=subtitle, transform=fig.transFigure, ha="left", fontsize=11, alpha=.8)
    # add in footnote
    ax.__repr__(x=0.12, y=0.01, s=footnote, transform=fig.transFigure, ha="left", fontsize=9, alpha=.7)

    # Export plot as high resolution PNG
    plt.savefig(output_file,  # Set path and filename
                dpi=300,  # Set dots per inch
                bbox_inches="tight",  # Remove extra whitespace around plot
                facecolor=BACK_GROUND_HEAVY_COLOR)  # Set background color to white


WIDE = .3
NARROW = .03


def plot_daily_candlestick(df: DataFrame,
                           title="", subtitle="", footnote="",
                           width=10, height=10,
                           output_file="output.jpg"):
    # Setup plot size
    fig, ax = plt.subplots(figsize=(width, height))

    # "up" dataframe will store the stock_prices
    up = df[df.close >= df.open]

    # "down" dataframe will store the stock_prices
    down = df[df.close < df.open]

    # Plotting up prices of the stock
    plt.bar(up.index, up.close - up.open, WIDE, bottom=up.open, color=RED_60)
    plt.bar(up.index, up.high - up.close, NARROW, bottom=up.close, color=RED_60)
    plt.bar(up.index, up.low - up.open, NARROW, bottom=up.open, color=RED_60)

    # Plotting down prices of the stock
    plt.bar(down.index, down.close - down.open, WIDE, bottom=down.open, color=GREEN_55)
    plt.bar(down.index, down.high - down.open, NARROW, bottom=down.open, color=GREEN_55)
    plt.bar(down.index, down.low - down.close, NARROW, bottom=down.close, color=GREEN_55)

    # Remove splines. Can be done one at a time or can slice with a list.
    ax.spines[["top", "right", "left"]].set_visible(False)

    # Reformat x-axis tick labels
    ax.xaxis.set_tick_params(labelsize=11)  # Set tick label size
    # Make space for and rotate the x-axis tick labels
    fig.autofmt_xdate()

    # Reformat y-axis tick labels
    ax.yaxis.set_tick_params(pad=-2,  # Pad tick labels so they don"t go over y-axis
                             labeltop=True,  # Put x-axis labels on top
                             labelbottom=False,  # Set no x-axis labels on bottom
                             bottom=False,  # Set no ticks on bottom
                             labelsize=11)  # Set tick label size

    # Add in line and tag
    ax.plot([0.12, .9],  # Set width of line
            [.98, .98],  # Set height of line
            transform=fig.transFigure,  # Set location relative to plot
            clip_on=False,
            color=MAIN_GREEN_85,
            linewidth=.6)
    ax.add_patch(plt.Rectangle((0.12, .98),  # Set location of rectangle by lower left corder
                               0.04,  # Width of rectangle
                               -0.02,  # Height of rectangle. Negative so it goes down.
                               facecolor=MAIN_GREEN_85,
                               transform=fig.transFigure,
                               clip_on=False,
                               linewidth=0))

    # Add in title and subtitle
    ax.__repr__(x=0.12, y=.91, s=title, transform=fig.transFigure, ha="left", fontsize=13, weight="bold", alpha=.8)
    ax.__repr__(x=0.12, y=.86, s=subtitle, transform=fig.transFigure, ha="left", fontsize=11, alpha=.8)
    # add in footnote
    ax.__repr__(x=0.12, y=0.01, s=footnote, transform=fig.transFigure, ha="left", fontsize=9, alpha=.7)

    # Export plot as high resolution PNG
    plt.savefig(output_file,  # Set path and filename
                dpi=300,  # Set dots per inch
                bbox_inches="tight",  # Remove extra whitespace around plot
                facecolor=BACK_GROUND_HEAVY_COLOR)  # Set background color to white

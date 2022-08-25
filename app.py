import bar_chart_race as bcr
import datetime
import json
import os
import pandas as pd

# check input date format
def format_check(date, fmt):
    try: datetime.datetime.strptime(date, fmt)
    except: return False
    else: return True

# input dates
def input_date(date):
    user_input = input(f"Enter {date} date in YYYY-mm-dd format: ")
    if not format_check(user_input, '%Y-%m-%d'):
        raise ValueError("❌ invalid date format!")
    return user_input

# check lastfm-backup path and files
def path_check(dir):
    if os.path.exists(dir):
        print(f"✅ {dir} found")
    else:
        print(f"❌ {dir} not found!")
        exit()

if __name__ == "__main__":

    # enter start and end date
    start_date = input_date("start")
    end_date = input_date("end")

    # check if start date < end date
    if start_date > end_date:
        print(f"❌ start date cannot come after end date!")
        exit()

    # check lastfm-backup folder
    lfb_path = os.path.abspath(__file__ + "/../../lastfm-backup/")
    path_check(lfb_path)

    # check config file
    config_path = os.path.abspath(f"{lfb_path}/config.json")
    path_check(config_path)

    # get username from lastfm-backup config file
    with open(f"{config_path}") as f:
        config = json.loads(f.read())
        username = config["username"]

    # check JSON backup file
    json_path = os.path.abspath(f"{lfb_path}/{username}.json")
    path_check(json_path)

    # load JSON backup
    with open(f"{json_path}","r") as f:
        data=json.loads(f.read())
        print(f"✅ {username} data loaded")

    # normalize data frame
    df_normalized = pd.json_normalize(
        data,
        record_path=["recenttracks", "track"],
        errors="ignore",
    )
    df = df_normalized[["date.uts", "artist.#text"]]

    # convert date format
    df["date"] = pd.to_datetime(df["date.uts"],unit="s")

    # filter date frame
    mask = (df["date"] >= start_date) & (df['date'] <= end_date)
    df = df.loc[mask]
    df["date"] = df["date"].dt.date

    # pivot data frame
    table = pd.pivot_table(
        df, 
        values="date.uts",
        index=["date"],
        columns=["artist.#text"],
        aggfunc="count",
        fill_value=0
    )

    # fill empty dates
    idx = pd.date_range(start_date, end_date)
    table = table.reindex(idx, fill_value=0)

    # cumulate daily scrobbles
    table = table.cumsum(axis = 0)

    print("✅ data frame ready")

    # create output folder if does not exist
    dir = os.path.abspath(__file__ + "/../videos/")
    if not os.path.exists(dir):
        os.mkdir(dir)

    # build animation
    bcr.bar_chart_race(
        table,
        filename=f"{dir}/{username}_{start_date}_{end_date}.mp4",
        orientation="h",
        sort="desc",
        n_bars=10,
        fixed_order=False,
        fixed_max=True,
        steps_per_period=10,
        interpolate_period=False,
        label_bars=True,
        bar_size=.95,
        period_label={"x": .99, "y": .25, "ha": "right", "va": "center"},
        period_summary_func=lambda v, r: {"x": .99, "y": .18,
                                        "s": f"Total scrobbles: {v.nlargest(6).sum():,.0f}",
                                        "ha": "right", "size": 8, "family": "Courier New"},
        perpendicular_bar_func="median",
        period_length=500,
        figsize=(5, 3),
        dpi=144,
        cmap="dark12",
        title=f"{username}'s scrobbles by artists",
        title_size="",
        bar_label_size=7,
        tick_label_size=7,
        shared_fontdict={"family" : "Helvetica", "color" : ".1"},
        scale="linear",
        writer=None,
        fig=None,
        bar_kwargs={"alpha": .7},
        filter_column_colors=False
    )  

    print(f"✅ ANIMATION READY\nVideo located at {dir}/{username}_{start_date}_{end_date}.mp4")
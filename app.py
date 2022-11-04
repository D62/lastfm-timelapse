import bar_chart_race as bcr
import base64
import datetime
import json
import requests
import pandas as pd
import streamlit as st
import time

def lastfm_get(api_key, username, page, uts_start, uts_end):

    # add API key and format to the payload
    payload = {
        "method": "user.getRecentTracks",
        "api_key": api_key,
        "user": username,
        "format": "json",
        "from": uts_start,
        "to": uts_end,
        "limit": 200,
        "page": page
    }

    # define headers and URL
    headers = {"user-agent": "test"}
    url = "https://ws.audioscrobbler.com/2.0/"

    response = requests.get(url, headers=headers, params=payload)
    return response

@st.cache(show_spinner=False)
def get_data(api_key, username, start_date, end_date):

    # convert start and end dates to Unix timestamps
    uts_start = int(time.mktime(start_date.timetuple()))
    uts_end = int(time.mktime(end_date.timetuple()))

    responses = []
    page = 1
    total_pages = 99999 # dummy number so the loop starts

    while page <= total_pages:

        # make the API call
        response = lastfm_get(api_key, username, page, uts_start, uts_end)

        # if we get an error, print the response and halt the loop
        if response.status_code != 200:
            progress_bar.empty()
            st.error(response.text, icon="🚨")
            st.stop()

        # check number of scrobbles and stop if >15000
        limit = 15000
        total = int(response.json()["recenttracks"]["@attr"]["total"])
        if total > limit:
            progress_bar.empty()
            st.error(f"Too many scrobbles to process ({total}/{limit})", icon="🚨")
            st.stop()

        # extract pagination info
        page = int(response.json()["recenttracks"]["@attr"]["page"])
        total_pages = int(response.json()["recenttracks"]["@attr"]["totalPages"])

        # append response
        responses.append(response)

        # if it is not a cached result, sleep
        if not getattr(response, "from_cache", False):
            time.sleep(0.25)

        # update progress bar
        percent_complete = (page / total_pages) / 2
        progress_bar.progress(percent_complete)

        # increment the page number
        page += 1

    df = [json.loads(r.content.decode("utf-8")) for r in responses]
    return df

def set_table(df):

    # normalize data frame
    df_normalized = pd.json_normalize(
        df,
        record_path=["recenttracks", "track"],
        errors="ignore",
    )
    df = df_normalized[["date.uts", "artist.#text"]]

    # convert date format
    df["date"] = pd.to_datetime(df["date.uts"],unit="s")

    # filter date frame
    #mask = (df["date"] >= start_date) & (df["date"] <= end_date)
    #df = df.loc[mask]
    df["date"] = df["date"].dt.date

    # get min and max dates
    min_date = df["date"].min()
    max_date = df["date"].max()

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
    idx = pd.date_range(min_date, max_date)
    table = table.reindex(idx, fill_value=0)

    # cumulate daily scrobbles
    table = table.cumsum(axis = 0)

    return table

def optimize_table(table):

    # keep only top 15 columns per rows and set others to 0
    table = table.mask(table.rank(axis=1, method='min', ascending=False).gt(15), 0)

    # drop all columns where all values are zero 
    table = table.loc[:, table.any()]

    # replace zeros with last non-zero value for each column on multi-index dataframe
    table = table.mask(table == 0).ffill(downcast="infer").fillna(0).astype(int)

    return table

def create_bcr(table):

    # bar chart race parameters
    html_str = bcr.bar_chart_race(
        table,
        n_bars=10,
        fixed_order=False,
        fixed_max=True,
        period_label={
            "x": .99,
            "y": .25,
            "ha": "right",
            "va": "center"
        },
        period_summary_func=lambda v, r:{
            "x": .99,
            "y": .18,
            "s": f"Total: {v.nlargest(6).sum():,.0f}",
            "ha": "right",
            "size": 8
        },
        title=f"{username}'s scrobbles by artists",
    )

    # generate the video file
    start = html_str.find('base64,')+len('base64,')
    end = html_str.find('">')
    video = base64.b64decode(html_str[start:end])

    return video

def output(video, username, start_date, end_date):

    st.video(video) # display video in streamlit
    st.download_button("Download", video, f"{username}_{start_date}_{end_date}.mp4") # download link

def update_bar(current_stage, max_stage):
    percent_complete = current_stage / max_stage
    progress_bar.progress(percent_complete)

if __name__ == "__main__":

    # Streamlit page config & title
    title = "Last.fm Timelapse Generator"
    st.set_page_config(
        page_title=title,
        page_icon=":headphones:",
        menu_items={
            "About": "https://github.com/D62/lastfm-timelapse"
        }
    )
    st.title(title)

    api_key = st.secrets["api_key"]

    if "video" not in st.session_state:
        st.session_state["video"] = ""

    # input form
    with st.form(key="Form"):

        username = st.text_input("Enter Last.fm username")

        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)

        start_date = st.date_input("Enter start date", yesterday)
        end_date = st.date_input("Enter end date", today)

    # check dates after click on "Generate"

        if st.form_submit_button(label="Generate"):

            if start_date < end_date and start_date < today and end_date <= today:

                # start generating the animation if date requirements are met
                progress_bar = st.progress(0) # initialize progress bar

                with st.spinner("Fetching data from Last.fm..."):
                    df = get_data(api_key, username, start_date, end_date)

                with st.spinner("Preparing data frame..."):
                    table = set_table(df)
                    update_bar(3, 5)

                with st.spinner("Optimizing data frame..."):
                    table = optimize_table(table)
                    update_bar(4, 5)
                
                with st.spinner("Creating animation..."):
                    st.session_state["video"] = create_bcr(table)
                    update_bar(5, 5)

                progress_bar.empty()

            else:
                st.error("Date Error", icon="🚨")

    if len(st.session_state["video"]) !=0:
        output(st.session_state["video"], username, start_date, end_date)
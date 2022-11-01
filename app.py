import bar_chart_race as bcr
import base64
import datetime
import json
import requests
import pandas as pd
import streamlit as st
import time

def lastfm_get(method, username, page):

    # add API key and format to the payload
    payload = {
        "method": method,
        "api_key": st.secrets["api_key"],
        "user": username,
        "format": "json"
    }

    if method == "user.getRecentTracks":
        payload |= {
        "from": 1665792000,
        "limit": 200,
        "page": page
    }

    # define headers and URL
    headers = {"user-agent": "test"}
    url = "https://ws.audioscrobbler.com/2.0/"

    response = requests.get(url, headers=headers, params=payload)
    return response

def username_check(username):

    # make the API call
    response = lastfm_get("user.getInfo", username, 0)

    # behavior when no username entered
    if username == "":
        st.error("No username entered", icon="🚨")
        return False

    # if we get an error, print the response and halt the loop
    elif response.status_code != 200:
        st.error(response.json()["message"], icon="🚨")
        return False

    # if user found    
    else:
        #userpic = str(response.json()["user"]["image"][0]["#text"])
        st.success("User " + response.json()["user"]["name"] + " found", icon="✅")
        #st.image(userpic, caption=None, width=None, use_column_width=None, clamp=False, channels="RGB", output_format="auto")
        return True

def get_data(username):

    responses = []
    page = 1
    total_pages = 99999 # dummy number so the loop starts

    while page <= total_pages:

        # make the API call
        response = lastfm_get("user.getRecentTracks", username, page)

        # if we get an error, print the response and halt the loop
        if response.status_code != 200:
            st.error(response.text, icon="🚨")
            break

        # extract pagination info
        page = int(response.json()["recenttracks"]["@attr"]["page"])
        total_pages = int(response.json()["recenttracks"]["@attr"]["totalPages"])

        # append response
        responses.append(response)

        # if it is not a cached result, sleep
        if not getattr(response, "from_cache", False):
            time.sleep(0.25)

        # update progress bar
        percent_complete = (page / total_pages) / 3
        progress_bar.progress(percent_complete)

        # increment the page number
        page += 1

    df = [json.loads(r.content.decode("utf-8")) for r in responses]
    return df

def prepare_table(df):

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

    # update progress bar
    percent_complete = 2 / 3
    progress_bar.progress(percent_complete)

    return table

def bar_chart_race(table):

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

    start = html_str.find('base64,')+len('base64,')
    end = html_str.find('">')

    video = base64.b64decode(html_str[start:end])
    st.video(video)
    st.download_button("Download", video)

    # update progress bar
    percent_complete = 1
    progress_bar.progress(percent_complete)

# Streamlit page title
st.title("Last.fm Timelapse Generator")

# username input

st.header("1) Enter Last.fm username")

with st.form(key="username"):

    username = st.text_input("Enter Last.fm username", label_visibility="collapsed")

    # check username after click on "Submit"
    if st.form_submit_button(label="Submit"):
        if not username_check(username):
            username = ""

# date range input

st.header("2) Enter date range")

with st.form(key="daterange"):

    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    start_date = st.date_input("Start date", today, disabled=username=="")
    end_date = st.date_input("End date", tomorrow, disabled=username=="")

# check dates after click on "Submit"

    if st.form_submit_button(label="Submit", disabled=username==""):

        if start_date < end_date:
            st.success("Start date: `%s`\n\nEnd date:`%s`" % (start_date, end_date), icon="✅")

        else:
            st.error("Error: End date must fall after start date.", icon="🚨")

st.header("3) Generate timelapse animation")

if st.button(label="Run", disabled=username==""):

    progress_bar = st.progress(0) # initialize progress bar

    with st.spinner("Downloading data from Last.fm..."):
        df = get_data(username)

    with st.spinner("Preparing data frame..."):
        table = prepare_table(df)
    
    with st.spinner("Creating animation..."):
        bar_chart_race(table)

    progress_bar.empty()
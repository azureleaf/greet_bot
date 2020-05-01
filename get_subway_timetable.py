from bs4 import BeautifulSoup
import urllib.request
import pandas as pd
import constants
import sqlite3
import time


def get_soup(root_url):

    try:
        html = urllib.request.urlopen(root_url)
    except urllib.error.URLError as e:
        print("URLを開けませんでした", e.reason)
        return -1
    return BeautifulSoup(html, "html.parser")


def soup2dfs(soup, dfs):
    """
    Extract the timetable info from the soup, save as dataframes.

    Args:
        BeautifulSoup soup for a single station.
        A soup contains timetable(s).
        Every timetable has schedule for both weekdays & holidays.
    Returns:
        Dict of 2 dataframes.
        One is for weekdays, another is for holidays
    """

    # Find timetable(s) in the soup
    # Find 4 at Sendai station, find 1 at terminal stations
    tables = soup.find_all(
        "table", {"class": "timetable_l_s"})

    station = soup.find("h2").string

    for table in tables:
        # Get destination
        # Note that target text is following to the 1st <br> tag
        dst_td = table.find("tr", {"id": "dest"}).td
        dst = clean_text(dst_td.find_all("br")[0].next_sibling)

        # A dict retains all-hour timetables for the route of the station
        route_weekday = {"sta": station, "dst": dst}
        route_holiday = {"sta": station, "dst": dst}

        # Get trains
        hr_trs = table.find_all("tr", {"id": ""})
        for hr_tr in hr_trs:

            # Hour of this row: 5, 6, ... 24
            hr = clean_text(hr_tr.find("td", {"id": "time"}).string)

            # Note that <td> for weekdays always come before that of holidays
            [td_weekday, td_holiday] = hr_tr.find_all(
                "td", {"id": "timetable"})

            # Split "12 15 18 21" style string into a list,
            # then join with "," symbol to store in the SQLite
            trains_list = td_weekday.string.split()
            route_weekday[str(hr)] = ",".join(trains_list)
            trains_list = td_holiday.string.split()
            route_holiday[str(hr)] = ",".join(trains_list)

        # Save the dict in the df
        dfs["holiday"] = dfs["holiday"].append(
            route_holiday, ignore_index=True)
        dfs["weekday"] = dfs["weekday"].append(
            route_weekday, ignore_index=True)

    return dfs


def list_urls():
    """Create the list of target URLs to be analyzed"""

    base_url = (f"https://www.navi.kotsu.city.sendai.jp/"
                f"dia/bustime/subway/subway_result_l.cgi?SubwayCode=")
    urls = [base_url + str(9285)]  # Sendai station
    urls += [base_url + str(1222)]  # Kitasendai station
    urls += [base_url + str(975)]  # Nagamchi station
    urls += [base_url + str(i) for i in range(6646, 6659 + 1)]  # Namboku
    urls += [base_url + str(i) for i in range(9727, 9738 + 1)]  # Tozai
    return urls


def clean_text(str):
    '''
    Remove unnecessary symbols from the string:
        whitespace, tab, line break
    '''
    return str \
        .replace("\n", "") \
        .replace("\t", "") \
        .replace(" ", "") \
        .replace("　", "")


def create_df():
    """Create empty dataframes to be filled by other functions"""

    df_columns = ["sta", "dst"]  # station & destination
    df_columns += [str(i) for i in range(5, 24 + 1)]  # hours

    df = pd.DataFrame(columns=df_columns)
    return df


def dfs2sqlite(dfs):
    """
    Get the dict of 2 dataframes,
    save them into corresponding SQLite3 tables
    """
    conn = sqlite3.connect(constants.DB_PATH)

    for day_type in ["weekday", "holiday"]:
        dfs[day_type].to_sql(
            "timetable_subway_" + day_type,
            conn,
            if_exists='replace',
            index=None)

    conn.close()
    return 0


def get_sample_soup():
    """
    Cook the soup from the downloaded sample HTML file.
    For debugging.
    """
    with open("./raw/sendaista.html", mode="r", encoding="shift_jis") as f:
        soup = BeautifulSoup(f, "html.parser")
    return soup


def wrapper():

    dfs = {}
    dfs["weekday"] = create_df()
    dfs["holiday"] = create_df()

    for url in list_urls():
        # Sleep not to put a strain on the server
        print("Sleeping before access to:", url)
        time.sleep(5)

        soup = get_soup(url)
        dfs = soup2dfs(soup, dfs)
        dfs2sqlite(dfs)


if __name__ == "__main__":
    wrapper()

    '''Debug'''
    # sample_soup = get_sample_soup()
    # dfs = soup2dfs(sample_soup)
    # dfs2sqlite(dfs)

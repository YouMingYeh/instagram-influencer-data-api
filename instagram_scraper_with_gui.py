"""
# Instagram Influencer Scraper
"""

from instagrapi import Client
from instagrapi.exceptions import LoginRequired
import pandas as pd
import streamlit as st

from dotenv import load_dotenv
import os

load_dotenv()

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

number_of_posts = st.slider("Number of Posts", 1, 100, 5)
number_of_influencers = st.slider("Number of Influencers", 1, 100, 5)


USERNAME = "cocha.app"
PASSWORD = "Ym930509"

client = Client()

try:
    session = client.load_settings("session.json")
except:
    session = None

login_via_session = False
login_via_pw = False

if session:
    try:
        client.set_settings(session)
        client.login(USERNAME, PASSWORD)

        # check if session is valid
        try:
            client.get_timeline_feed()
        except LoginRequired:
            st.warning("Session is invalid, need to login via username and password")

            old_session = client.get_settings()

            # use the same device uuids across logins
            client.set_settings({})
            client.set_uuids(old_session["uuids"])

            client.login(USERNAME, PASSWORD)
            client.dump_settings("session.json")

        login_via_session = True
    except Exception as e:
        st.warning("Couldn't login user using session information: %s" % e)

if not login_via_session:
    try:
        st.warning(
            "Attempting to login via username and password. username: %s" % USERNAME
        )
        if client.login(USERNAME, PASSWORD):
            client.dump_settings("session.json")
            login_via_pw = True
    except Exception as e:
        st.warning("Couldn't login user using username and password: %s" % e)
else:
    st.info("Logged in via session")

if not login_via_pw and not login_via_session:
    st.error("Couldn't login user with either password or session")

# read influencer from csv
influencer = pd.read_csv("influencer.csv")


def get_user_id(username):
    try:
        return client.user_id_from_username(username)
    except:
        return None


def get_user_medias(user_id):
    try:
        return client.user_medias(user_id, number_of_posts)
    except:
        return None


def main():
    for index, row in influencer.iterrows():
        if index >= number_of_influencers:
            break

        display_name = row["display_name"]
        username = row["username"]
        user_id = get_user_id(username)
        if user_id is None:
            st.write(f"User {username} not found")
            continue
        medias = get_user_medias(user_id)
        if medias is None:
            st.write(f"Media for {username} not found")
            continue

        st.title(f"{username}")

        # Create DataFrame from media data
        df = pd.DataFrame(
            {
                "taken_at": [media.taken_at for media in medias],
                "media_type": [media.media_type for media in medias],
                "image_versions2": [str(media.image_versions2) for media in medias],
                "resources": [
                    ", ".join(
                        [
                            str(resource.thumbnail_url)
                            for resource in getattr(media, "resources", [])
                        ]
                    )
                    for media in medias
                ],
                "comment_count": [
                    getattr(media, "comment_count", None) for media in medias
                ],
                "like_count": [getattr(media, "like_count", None) for media in medias],
                "play_count": [getattr(media, "play_count", None) for media in medias],
                "caption_text": [
                    getattr(media, "caption_text", None) for media in medias
                ],
                "accessibility_caption": [
                    getattr(media, "accessibility_caption", None) for media in medias
                ],
                "thumbnail_url": [
                    getattr(media, "thumbnail_url", None) for media in medias
                ],
                "usertags": [
                    ", ".join(
                        [
                            usertag.user.username
                            for usertag in getattr(media, "usertags", [])
                        ]
                    )
                    for media in medias
                ],
                "sponsor_tags": [
                    ", ".join(
                        [
                            sponsor_tag.username
                            for sponsor_tag in getattr(media, "sponsor_tags", [])
                        ]
                    )
                    for media in medias
                ],
                "video_url": [getattr(media, "video_url", None) for media in medias],
                "view_count": [getattr(media, "view_count", None) for media in medias],
                "title": [getattr(media, "title", None) for media in medias],
            }
        )

        # Display the DataFrame
        df


main()

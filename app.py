import streamlit as st
import smtplib
import requests
import json
import threading
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Constants for SMTP
FROM_EMAIL = 'chaitanya@syncmedia.io'
FROM_PASSWORD = 'txwg klfe zxln izvz'
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
VIDEO_FILE = 'videos.json'  # File to store the latest video ids
API_KEY = 'AIzaSyAkNKObjLO7WdOjEMzFcUo-aHkdvCVCk_k'  # Replace with your actual API key

# Function to fetch the latest video from the channel
def get_latest_videos(channel_id):
    url = f'https://www.googleapis.com/youtube/v3/search?key={API_KEY}&channelId={channel_id}&part=snippet,id&order=date&maxResults=1'
    response = requests.get(url)
    data = response.json()
    
    if 'items' in data:
        video_id = data['items'][0]['id']['videoId']
        video_title = data['items'][0]['snippet']['title']
        video_url = f'https://www.youtube.com/watch?v={video_id}'
        return video_id, video_title, video_url
    else:
        print(f"Error fetching data for channel {channel_id}: {data}")
        return None, None, None

# Load video data from JSON file
def load_video_data():
    try:
        with open(VIDEO_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Save video data to JSON file
def save_video_data(video_data):
    with open(VIDEO_FILE, 'w') as f:
        json.dump(video_data, f)

# Send email to the list of recipients
def send_email(subject, body, to_emails):
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = ", ".join(to_emails)  # Add all email recipients here
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(FROM_EMAIL, FROM_PASSWORD)
        server.sendmail(FROM_EMAIL, to_emails, msg.as_string())  # Send to all emails at once
        print('Emails sent successfully')

# Main function to check for new videos and send emails
def main(channel_ids, to_emails):
    current_videos = load_video_data()
    new_videos = {}
    email_body = ""

    for channel_id in channel_ids:
        video_id, video_title, video_url = get_latest_videos(channel_id)
        
        if video_id and (channel_id not in current_videos or current_videos[channel_id] != video_id):
            # Found a new video
            new_videos[channel_id] = video_id
            email_body += f"New video uploaded: {video_title}\nWatch here: {video_url}\n\n"

    if new_videos:
        save_video_data({**current_videos, **new_videos})
        send_email("New YouTube Video Alert", email_body, to_emails)
    else:
        print("No new videos found.")

# Function to run the script every 5 hours
def schedule_task(channel_ids, to_emails):
    while True:
        main(channel_ids, to_emails)
        time.sleep(5)  # Wait for 5 hours

# Streamlit UI
st.title("YouTube Video Alert Emailer")

# Initialize session state for email and channel IDs
if 'channel_ids' not in st.session_state:
    st.session_state['channel_ids'] = []
if 'email_ids' not in st.session_state:
    st.session_state['email_ids'] = []

# Add and remove channel IDs
st.header("Manage YouTube Channel IDs")
new_channel = st.text_input("Add a YouTube Channel ID:")
if st.button("Add Channel"):
    if new_channel:
        st.session_state['channel_ids'].append(new_channel)

for channel_id in st.session_state['channel_ids']:
    st.write(channel_id)
    if st.button(f"Remove {channel_id}"):
        st.session_state['channel_ids'].remove(channel_id)

# Add and remove email IDs
st.header("Manage Email Recipients")
new_email = st.text_input("Add a recipient email:")
if st.button("Add Email"):
    if new_email:
        st.session_state['email_ids'].append(new_email)

for email in st.session_state['email_ids']:
    st.write(email)
    if st.button(f"Remove {email}"):
        st.session_state['email_ids'].remove(email)

# Button to start the process
if st.button("Start YouTube Video Monitoring"):
    channel_ids = st.session_state['channel_ids']
    email_ids = st.session_state['email_ids']
    if channel_ids and email_ids:
        st.write("Monitoring started. Emails will be sent every 5 hours.")
        threading.Thread(target=schedule_task, args=(channel_ids, email_ids)).start()
    else:
        st.write("Please add at least one channel ID and one email.")
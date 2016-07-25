#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import json
import pyaudio, wave
import warnings
import urllib.request
import os, sys
from acrcloud.recognizer import ACRCloudRecognizer

def Record():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 16000
    RECORD_SECONDS = 15
    WAVE_OUTPUT_FILENAME = "output.wav"

    p = pyaudio.PyAudio()

    stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

    print("Recording...")

    frames = []

    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("Finding events...")

    stream.stop_stream()
    stream.close()
    p.terminate()

    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

try:

    if __name__ == '__main__':

        config = {
            'host': """<Your host>""",
            'access_key': """<You ACRCloud access key>""",
            'access_secret': """<Your ACRCloud access secret>""",
            'debug': False,
            'timeout': 40  # seconds
        }

        flag = 1
        while flag:
            '''This module can recognize ACRCloud by most of audio/video file.
            Audio: mp3, wav, m4a, flac, aac, amr, ape, ogg ...
            Video: mp4, mkv, wmv, flv, ts, avi ...'''
            re = ACRCloudRecognizer(config)

            # Use file from arguments and if there is no file, then record music from mic

            if len(sys.argv) > 1:
               buf = open(sys.argv[1], 'rb').read()
               flag = 0
            else:
                Record()
                buf = open("output.wav", 'rb').read()

            # Recognize by file_audio_buffer that read from file path or mic, and skip 0 seconds from the beginning.
            data_content = re.recognize_by_filebuffer(buf, 0)

            # Transform received json to object
            data = json.loads(data_content)

            # In case of success print information
            if data["status"]["code"] == 0:
                # Print Success message
                print(data["status"]["msg"])
                print()
                # Print recognised information about artist
                print("Artist:", data["metadata"]["music"][0]["artists"][0]["name"])
                print("Title:", data["metadata"]["music"][0]["title"])
                if "album" in data["metadata"]["music"][0]:
                    print("Album:", data["metadata"]["music"][0]["album"]["name"])
                if "label" in data["metadata"]["music"][0]:
                    print("Label:", data["metadata"]["music"][0]["label"])
                if "youtube" in data["metadata"]["music"][0]["external_metadata"]:
                    str_youtube = "Youtube: https://www.youtube.com/watch?v=" + data["metadata"]["music"][0]["external_metadata"]["youtube"]["vid"]
                    print(str_youtube)
                print()

                # Form URL for Discovery API
                artist = data["metadata"]["music"][0]["artists"][0]["name"]
                artist_for_url = artist.replace(" ", "%20")

                # Temporal API key is used to get access to Ticketmaster Discovery API, please your own.
                url = "http://app.ticketmaster.com/discovery/v2/events.json?apikey=7elxdku9GGG5k8j0Xm8KWdANDgecHMV0&size=100&keyword=" + artist_for_url

                # Launch Discovery API with formed URL
                discovery_response = urllib.request.urlopen(url).read().decode('utf8')
                discovery_data = json.loads(discovery_response)

                # Print information about found events of the artist
                print(discovery_data["page"]["totalElements"], "events found Ticketmaster Discovery API.")

                if discovery_data["page"]["totalElements"] > 0:
                    i = 0
                    events_on_page = discovery_data["page"]["totalElements"]
                    if discovery_data["page"]["totalElements"] > 100:
                        events_on_page = 100
                    while i < events_on_page:
                        event_name = discovery_data["_embedded"]["events"][i]["name"]
                        if "url" in discovery_data["_embedded"]["events"][i]:
                            event_url = discovery_data["_embedded"]["events"][i]["url"]
                        event_date = discovery_data["_embedded"]["events"][i]["dates"]["start"]["localDate"]
                        event_time = discovery_data["_embedded"]["events"][i]["dates"]["start"]["localTime"]
                        if "city" in discovery_data["_embedded"]["events"][i]["_embedded"]["venues"][0]:
                            event_venue_city = discovery_data["_embedded"]["events"][i]["_embedded"]["venues"][0]["city"]["name"]
                        else:
                            event_venue_city = "..."
                        print(event_date, event_time, " - ", event_name, "in", event_venue_city, event_url)
                        i += 1
            # No informaiton is found
            else:
                print(data["status"]["msg"])
                print()

except KeyboardInterrupt:
    print("Exception")


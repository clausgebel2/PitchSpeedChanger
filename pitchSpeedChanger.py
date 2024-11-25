"""
Author: Claus Gebel

Pitch and Speed Changer
Copyright (C) 2024 Claus Gebel

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import sys
import gi
import argparse
from gi.repository import GLib

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GObject

Gst.init(None)


def play_mp3(filename, pitch=None, speed=None):
    global loop
    pipeline = Gst.Pipeline.new("audio-player")
    source = Gst.ElementFactory.make("filesrc")
    source.set_property("location", filename)

    decode = Gst.ElementFactory.make("decodebin")
    convert = Gst.ElementFactory.make("audioconvert")
    pitch_element = Gst.ElementFactory.make("pitch")
    speed_element = Gst.ElementFactory.make("speed")

    sink = Gst.ElementFactory.make("autoaudiosink")

    if (
        not pipeline
        or not source
        or not decode
        or not convert
        or not pitch_element
        or not speed_element
        or not sink
    ):
        print("Error: audio file cannot be played.")
        return

    pipeline.add(source)
    pipeline.add(decode)
    pipeline.add(convert)
    pipeline.add(pitch_element)
    pipeline.add(speed_element)
    pipeline.add(sink)

    source.link(decode)
    decode.connect("pad-added", on_pad_added, convert, pitch_element, speed_element)
    convert.link(pitch_element)
    pitch_element.link(speed_element)
    speed_element.link(sink)

    if speed:
        speed_element.set_property("speed", speed)
        pitch = 1.0 / speed if pitch is None else pitch / speed
    if pitch:
        pitch_element.set_property("pitch", pitch)

    pipeline.set_state(Gst.State.PLAYING)

    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", on_message, pipeline)

    loop = GLib.MainLoop()
    loop.run()


def on_pad_added(decodebin, pad, convert, pitch, speed):
    sink_pad = convert.get_static_pad("sink")
    if not sink_pad.is_linked():
        pad.link(sink_pad)


def on_message(bus, message, pipeline):
    global loop
    if message.type == Gst.MessageType.EOS or message.type == Gst.MessageType.ERROR:
        pipeline.set_state(Gst.State.NULL)
        loop.quit()


if __name__ == "__main__":
    
    parser = argparse.ArgumentParser(
        description="Play an MP3 file with pitch and speed adjustments."
    )
    parser.add_argument("filename", type=str, help="The MP3 file to play.")
    parser.add_argument(
        "-p",
        "--pitch",
        type=float,
        help="Pitch adjustment, e.g., 0.5 for half pitch, 2.0 for double pitch.",
    )
    parser.add_argument(
        "-s",
        "--speed",
        type=float,
        help="Speed adjustment, e.g., 1.5 to speed up the audio file by 50%%.",
    )

    args = parser.parse_args()

    play_mp3(args.filename, args.pitch, args.speed)

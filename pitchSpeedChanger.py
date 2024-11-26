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
import signal
from gi.repository import GLib

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GObject

class AudioPlayer:
    def __init__(self, filename: str, speed: float, pitch: float):
        Gst.init(None)
        self.loop = None
        self.filename = filename
        self.pipeline = self.create_pipeline()
        self.source = self.set_source(self.filename)
        self.audio_decoder = self.create_audio_decoder()
        self.audio_converter = self.create_audio_converter()
        self.audio_pitch_element = self.create_audio_pitch_element()
        self.audio_speed_element = self.create_audio_speed_element()
        self.audio_output = self.create_output()

        self.add_elements_to_pipeline()
        self.connect_source_with_decoder()
        self.connect_decoder_with_converter_pitch_speed()
        self.play(speed, pitch)

        self.create_pipeline_bus()
        self.run_loop()
        


    def create_pipeline(self) -> Gst.Pipeline:
        pipeline = Gst.Pipeline.new("audio-player")
        if not pipeline:
            raise RuntimeError("Error: couldn't create GStreamer audio player pipeline.")
        return pipeline

    
    def set_source(self, filename: str) -> Gst.Element:
        source = Gst.ElementFactory.make("filesrc")
        source.set_property("location", filename)
        if not source:
            raise RuntimeError("Error: couldn't set GStreamer source file.")
        return source


    def create_audio_decoder(self) -> Gst.Element:     
        audio_decoder = Gst.ElementFactory.make("decodebin")
        if not audio_decoder:
            raise RuntimeError("Error: couldn't create GStreamer audio decoder.")
        return audio_decoder


    def create_audio_converter(self) -> Gst.Element:
        audio_converter = Gst.ElementFactory.make("audioconvert")
        if not audio_converter:
            raise RuntimeError("Error: couldn't create GStreamer audio converter.")
        return audio_converter


    def create_audio_pitch_element(self) -> Gst.Element:
        audio_pitch = Gst.ElementFactory.make("pitch")
        if not audio_pitch:
            raise RuntimeError("Error: couldn't create GStreamer audio pitch.")
        return audio_pitch


    def create_audio_speed_element(self) -> Gst.Element:
        audio_speed = Gst.ElementFactory.make("speed")
        if not audio_speed:
            raise RuntimeError("Error: couldn't create GStreamer audio speed.")
        return audio_speed


    def create_output(self) -> Gst.Element:
        audio_sink = Gst.ElementFactory.make("autoaudiosink")
        if not audio_sink:
            raise RuntimeError("Error: couldn't create GStreamer output element.")
        return audio_sink


    def add_elements_to_pipeline(self):
        self.pipeline.add(self.source)
        self.pipeline.add(self.audio_decoder)
        self.pipeline.add(self.audio_converter)
        self.pipeline.add(self.audio_pitch_element)
        self.pipeline.add(self.audio_speed_element)
        self.pipeline.add(self.audio_output)


    def connect_source_with_decoder(self):
        self.source.link(self.audio_decoder)


    def on_pad_added(self, decodebin: Gst.Element, pad: Gst.Pad, audio_converter: Gst.Element, pitch: Gst.Element, speed: Gst.Element):
        sink_pad = self.audio_converter.get_static_pad("sink")
        if not sink_pad.is_linked():
            pad.link(sink_pad)        


    def connect_decoder_with_converter_pitch_speed(self):
        self.audio_decoder.connect("pad-added", self.on_pad_added, self.audio_converter, self.audio_pitch_element, self.audio_speed_element)
        self.audio_converter.link(self.audio_pitch_element)
        self.audio_pitch_element.link(self.audio_speed_element)
        self.audio_speed_element.link(self.audio_output)


    def play(self, speed=None, pitch=None):
        if speed:
            self.audio_speed_element.set_property("speed", speed)
            pitch = 1.0 / speed if pitch is None else pitch / speed
        if pitch:
            self.audio_pitch_element.set_property("pitch", pitch)

        self.pipeline.set_state(Gst.State.PLAYING)


    def on_message(self, bus, message, pipeline):
        if message.type == Gst.MessageType.EOS or message.type == Gst.MessageType.ERROR:
            pipeline.set_state(Gst.State.NULL)
            self.loop.quit()


    def create_pipeline_bus(self) -> Gst.Bus:
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message, self.pipeline)
        signal.signal(signal.SIGINT, self.strg_c_or_strg_z_pressed) # Ctrl + C pressed
        signal.signal(signal.SIGTSTP, self.strg_c_or_strg_z_pressed) # Ctrl + Z pressed
        return bus


    def run_loop(self):
        loop = GLib.MainLoop()
        loop.run()


    def strg_c_or_strg_z_pressed(self, sig, frame):
        print("\rAudio stopped.")
        if self.loop is not None: 
            self.loop.quit()
        if self.pipeline is not None: 
            self.pipeline.set_state(Gst.State.NULL)
        exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Play an MP3 file with pitch and speed adjustments."
    )
    parser.add_argument("filename", type=str, help="The MP3 file to play.")
    parser.add_argument("-p", "--pitch", type=float, help="Modifies audio pitch, e.g., 0.5 for half pitch, 2.0 for double pitch.",)
    parser.add_argument("-s", "--speed", type=float, help="Modifies audio speed, e.g., 1.5 to speed up the audio file by 50%%.",)

    args = parser.parse_args()

    AudioPlayer(args.filename, args.speed, args.pitch)

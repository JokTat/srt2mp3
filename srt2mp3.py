#!/usr/bin/env python3
import locale
import sys
import re
from gtts import gTTS
import os

class Subtitle:
    def __init__(self, line_number, text, start_time, end_time, duration):
        self.line_number = line_number
        self.text = text
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration



def parse_srt(srt_file):
    """
    Parse an SRT file and extract subtitle information.

    Args:
    srt_file (str): Path to the SRT file.

    Returns:
    list: List of Subtitle objects.
    """
    subtitles = []
    with open(srt_file, 'r', encoding='utf-8') as file:
        lines = file.readlines()
        line_number = 0
        text = ""
        start_time = 0
        end_time = 0
        duration = 0
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+$', line):
                # Line number
                if text != "":
                    subtitle = Subtitle(line_number, text, start_time, end_time, duration)
                    subtitles.append(subtitle)
                line_number = int(line)
                text = ""
            elif re.match(r'^\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+$', line):
                # Timecode
                start_time, end_time = line.split(" --> ")
                start_time_ms = time_to_milliseconds(start_time)
                end_time_ms = time_to_milliseconds(end_time)
                duration = end_time_ms - start_time_ms
            elif line == "":
                # Empty line indicates end of subtitle
                continue
            else:
                # Text
                text += line + " "
        # Add last subtitle
        if text != "":
            subtitle = Subtitle(line_number, text, start_time, end_time, duration)
            subtitles.append(subtitle)
    return subtitles

def silent_file(durata,fileName):
    if durata < 1: return None
    # Creo un segmento audio vuoto della durata desiderata (in millisecondi)

    segmento_vuoto = AudioSegment.silent(duration=durata)

    # Salvo il segmento vuoto come file MP3
    segmento_vuoto.export(fileName, format="mp3")
    return fileName

# Function to convert time to milliseconds since midnight
def time_to_milliseconds(time_str):
    """
    Convert a time string in the format "hh:mm:ss,sss" to milliseconds since midnight.

    Args:
    time_str (str): Time string in the format "hh:mm:ss,sss".

    Returns:
    int: Milliseconds since midnight.
    """
    hours, minutes, seconds_milliseconds = time_str.split(":")
    seconds, milliseconds = seconds_milliseconds.split(",")

    hours = int(hours)
    minutes = int(minutes)
    seconds = int(seconds)
    milliseconds = int(milliseconds)

    return (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds





def subtitle2mp3(subtitle,lang):
    """
    Convert subtitle text to MP3 audio and return the file path.

    Args:
    subtitle (Subtitle): Subtitle object containing text and line number.

    Returns:
    str: Path and file name of the generated MP3 audio.
    """
    # Genera il nome del file MP3 utilizzando il numero di linea del sottotitolo
    mp3_filename = f"Temp_{subtitle.line_number}.mp3"

    # Converti il testo del sottotitolo in MP3
    tts = gTTS(text=subtitle.text, lang=lang)

    # Salva il file MP3
    tts.save(mp3_filename)

    # Restituisci il percorso e il nome del file MP3
    return mp3_filename

from pydub import AudioSegment

import subprocess

def adjust_mp3_playtime(input_file, target_playtime_ms):
    """
    Adjust the speed of an MP3 file using FFmpeg to match the target playtime.

    Args:
    input_file (str): Path to the input MP3 file.
    target_playtime_ms (int): Target playtime in milliseconds.

    Returns:
    None
    """

    # Carica il file MP3
    audio = AudioSegment.from_mp3(input_file)

    # Calcola la durata attuale del file MP3
    duration_ms = len(audio)

    # Calcola il fattore di velocità necessario per raggiungere il tempo di riproduzione desiderato
    speed_factor = duration_ms/target_playtime_ms

    # Costruisci il comando FFmpeg per regolare la velocità dell'audio
    output_file = "adjusted.mp3"
    ffmpeg_command = [
        "ffmpeg",
        "-i", input_file,
        "-filter:a", f"atempo={speed_factor}",
        output_file
    ]

    # Esegui il comando FFmpeg
    subprocess.run(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Sovrascrivi il file MP3 originale con il file regolato
    if os.path.exists(output_file):
        os.rename(output_file, input_file)

import subprocess

def concatenate_mp3(input_files, output_file):
    """
    Concatenate multiple MP3 files into one.

    Args:
    input_files (list): List of input MP3 files.
    output_file (str): Output file name for the concatenated MP3.

    Returns:
    None
    """
    # Costruisci l'elenco dei file di input per FFmpeg con i percorsi quotati
    input_args = " ".join(['-i "{}"'.format(f) for f in input_files])

    # Comando FFmpeg per concatenare i file MP3
    ffmpeg_command = 'ffmpeg {} -filter_complex "concat=n={}:v=0:a=1" -c:a libmp3lame "{}"'.format(input_args, len(input_files), output_file)

    # Esegui il comando FFmpeg
    subprocess.run(ffmpeg_command, shell=True)


def inserisci_audio(input_video, input_audio, output_video):
    # Comando ffmpeg per inserire la seconda traccia audio
    ffmpeg_command = [
        "ffmpeg",
        "-i", input_video,
        "-i", input_audio,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_video
    ]

    # Esegui il comando ffmpeg utilizzando subprocess
    subprocess.run(ffmpeg_command)


def show_help():
    help_text = """
Usage: python srt2mp3.py [options] <input_file.srt> <input_file.mp4>

    Options:
    -h, --help            Show this help message and exit.
    -m, --merge           Merge the generated audio track with the input video.
    -xx, --language xx    Specify the language code for subtitle-to-audio conversion using GTTS.
                          Replace 'xx' with the desired language code.

    Arguments:
    <input_file.srt>      The subtitle file in SRT format.
    <input_file.mp4>      The input video file in MP4 format to merge with the MP3 output.

    Description:
    This program processes an SRT subtitle file to generate corresponding audio tracks, 
    and optionally merges these audio tracks with an MP4 video file.

    Steps:
    1. Provide the SRT file and the MP4 video file as arguments.
    2. Optionally, specify the language code for subtitle-to-audio conversion.
    3. The program will generate silent audio files for the durations between subtitle entries.
    4. The program will convert subtitle text to audio and adjust the duration.
    5. All generated audio files will be concatenated into a single MP3 file.
    6. If the --merge option is provided, the final MP3 file will be merged 
       with the input MP4 video file to create a new video file.

    Examples:
    python srt2mp3.py subtitles.srt
                    or
    python srt2mp3.py subtitles.srt -m video.mp4
                    or
    python srt2mp3.py -m -en subtitles.srt video.mp4

    Note:
    Ensure ffmpeg is installed and available in your system PATH.
    """
    print(help_text)



def clear_screen():
    if os.name == "posix":
        os.system("clear")
    else:
        os.system("cls")


def get_lang():
    # Ottieni la lingua locale corrente
    language_code, encoding = locale.getlocale()
    if language_code:
        # Estrai solo il codice della lingua (prima parte del codice)
        language_code = language_code.split('_')[0]
    return language_code


def main():
    language_codes = [
        "af", "sq", "am", "ar", "hy", "as", "ay", "az", "ba", "eu", "bn", "dz",
        "bh", "bi", "br", "bg", "my", "be", "km", "ca", "zh", "co", "hr", "cs",
        "da", "nl", "en", "eo", "et", "fo", "fj", "fi", "fr", "fy", "gl", "ka",
        "de", "el", "kl", "gn", "gu", "ha", "he", "hi", "hu", "is", "id", "ia",
        "ie", "ga", "it", "ja", "jw", "kn", "ks", "kk", "rw", "ky", "rn", "ko",
        "ku", "lo", "la", "lv", "ln", "lt", "mk", "mg", "ms", "ml", "mt", "mi",
        "mr", "mo", "mn", "na", "ne", "no", "oc", "or", "om", "ps", "fa", "pl",
        "pt", "pa", "qu", "rm", "ro", "ru", "sm", "sg", "sa", "sr", "sh", "st",
        "tn", "sn", "sd", "si", "ss", "sk", "sl", "so", "es", "su", "sw", "sv",
        "tl", "tg", "ta", "tt", "te", "th", "bo", "ti", "to", "ts", "tr", "tk",
        "tw", "uk", "ur", "uz", "vi", "vo", "cy", "wo", "xh", "yi", "yo", "zu"
    ]
    my_lang =get_lang()
    input_video = ""
    srt_file_path = None
    merge = False
    if len(sys.argv) < 2:
        show_help()

        sys.exit(1)

    for arg in sys.argv:
        if arg.upper() == "-H" or arg.upper() == "--HELP":
            show_help()
            sys.exit(0)
        if arg.upper() == "-M" or arg.upper() == "--MERGE":
            merge = True
        if arg.endswith(".srt"):
            srt_file_path = arg
        if  arg[1] == '-' and arg[-2:] in language_codes:
            my_lang = arg

        if arg.endswith(".mp4"):
            input_video = arg

    if srt_file_path is None:
        clear_screen()
        show_help()
        sys.exit(1)

    subtitles = parse_srt(srt_file_path)
    print("Subtitles found in the SRT file:")
    fileslist=[]
    for i in range(len(subtitles)):
        subtitle = subtitles[i]
       # next_subtitle = subtitles[i+1] if i<len(subtitles)-1 else None
        prev_subtitle = subtitles[i-1] if i > 0 else None
        if prev_subtitle is not None:
            durata =time_to_milliseconds(subtitle.start_time) - time_to_milliseconds(prev_subtitle.end_time)
            space_file = silent_file(durata ,f"between_{i}")

            print("spazio tra le traccie",
                  f"{time_to_milliseconds(prev_subtitle.end_time)
                     - time_to_milliseconds(subtitle.start_time)}")
        else:

            space_file = silent_file(time_to_milliseconds(subtitle.start_time),f"between_{i}")
            print("spazio tra le traccie",
                  f"{time_to_milliseconds(subtitle.start_time)}")

        if space_file is not None:
            fileslist.append(space_file)
        clear_screen()

        #print("spazio tra le traccie",
        #      f"{time_to_milliseconds(prev_subtitle.end_time)
         #        -time_to_milliseconds(subtitle.start_time)}")

        print("nome spazio file:", f"{space_file}")
        print("Text:", subtitle.text)
        print("Start Time:", subtitle.start_time)
        print("End Time:", subtitle.end_time)
        print("Duration:", subtitle.duration)
        print("Progress..", f"{i}/{len(subtitles)}")
        #  subtitle=subtitles[1]

        file_name = subtitle2mp3(subtitle, my_lang)
        adjust_mp3_playtime(file_name, subtitle.duration * 1)

        fileslist.append(file_name)

    # Ottieni la parte della stringa esclusi gli ultimi tre caratteri
    outputfile = srt_file_path[:-4]
    videoutput = outputfile+"OUT.mp4"
    outputfile +=".mp3"
    print("concatenazione dei files")
    concatenate_mp3(fileslist, outputfile)
    for file in fileslist:
        os.remove(file)
    print("converted done !!")

    # Utilizzo della funzione



    if merge:
        inserisci_audio(input_video, outputfile, videoutput)
        print ("inserita la nuova traccia audio nel video")

if __name__ == "__main__":

    main()

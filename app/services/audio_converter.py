

import subprocess
import os

class AudioConverter:

    @staticmethod
    def webm_to_wav(input_path):

        output_path = input_path.replace(".webm", ".wav")

        ffmpeg_path = r"C:\Users\Srushti Sambare\Downloads\ffmpeg-8.1.2-essentials_build\ffmpeg-8.1.2-essentials_build\bin\ffmpeg.exe"

        subprocess.run(
            [
                ffmpeg_path,
                "-y",          # overwrite if file exists
                "-i", input_path,
                output_path
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        print("WAV created:", os.path.exists(output_path))

        return output_path
import json
import requests

from flask import current_app
from app.services.audio_converter import AudioConverter

class TranscriptionService:

    @staticmethod
    def transcribe(filepath):
        
        if filepath.endswith(".webm"):
            filepath = AudioConverter.webm_to_wav(filepath)

        with open(filepath, "rb") as f:
            audio = f.read()

        headers = {
            "x-api-key": current_app.config["GRADIUM_API_KEY"],
            "Content-Type": "audio/wav"
        }

        params = {
            "json_config": json.dumps({
                "language": "en"
            })
        }
        print("Sending:", filepath)
        response = requests.post(
            "https://api.gradium.ai/api/post/speech/asr",
            headers=headers,
            params=params,
            data=audio,
            stream=True
        )

        print(response.status_code)
        print(response.text)

        response.raise_for_status()

        transcript = []

        for line in response.iter_lines(decode_unicode=True):

            if not line:
                continue

            msg = json.loads(line)
            print(msg)

            if msg["type"] == "text":
                transcript.append(msg["text"])
        return " ".join(transcript)
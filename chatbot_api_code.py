from fastapi import FastAPI, UploadFile, File, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import openai
import tempfile
# from pydub import AudioSegment
import os
from dotenv import load_dotenv
from pydub import AudioSegment

from prompt import SYSTEM_PROMPT

load_dotenv()

router = APIRouter(prefix="/api/chat")

openai.api_key = os.getenv("OPENAI_API_KEY")



# router.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


def get_chat_response(user_text):
    response = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ]
    )

    answer = response.choices[0].message.content.strip()

    if " " in answer:
        answer = answer.split()[0]

    return answer


def speech_to_text(audio_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        audio = AudioSegment.from_file(audio_bytes)
        audio.export(temp_audio.name, format="wav")
        path = temp_audio.name

    with open(path, "rb") as f:
        transcript = openai.audio.transcriptions.create(
            model="gpt-4o-mini-transcribe",
            file=f
        )
    return transcript.text


@router.post("/predict/text")
async def predict_text(payload: dict):
    user_text = payload.get("text", "")
    result = get_chat_response(user_text)
    return {"result": result}


@router.post("/predict/audio")
async def predict_audio(file: UploadFile = File(...)):
    # audio_bytes = await file.read()
    # with tempfile.NamedTemporaryFile(delete=False) as temp:
    #     temp.write(audio_bytes)
    #     temp_path = temp.name
    #
    # text = speech_to_text(temp_path)
    # result = get_chat_response(text)
    # return {"result": result}
    audio_bytes = await file.read()
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_path = temp_audio.name
        text = speech_to_text(temp_path)
        result = get_chat_response(text)
        return {"result": result, "transcript": text}
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)




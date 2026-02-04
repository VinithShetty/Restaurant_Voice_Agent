import re
import os
import threading
import time
import json
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import pyttsx3
import requests

# Ollama API endpoint (runs locally)
OLLAMA_URL = "http://localhost:11434/api/chat"
# You can change this to any model you have installed in Ollama
# Popular options: llama3.2, mistral, phi3, gemma2
OLLAMA_MODEL = "llama3.2"

# Initialize pyttsx3 TTS engine
tts_engine = pyttsx3.init()
# Optional: Adjust speech rate (default is usually 200)
tts_engine.setProperty('rate', 175)
# Optional: Set voice (0 = male, 1 = female on most systems)
voices = tts_engine.getProperty('voices')
if len(voices) > 1:
    tts_engine.setProperty('voice', voices[1].id)  # Female voice

conversation_memory = []

# Global flag to control microphone state
mute_microphone = threading.Event()

# Audio queue for Vosk
audio_queue = queue.Queue()

prompt = """##Objective
You are a voice AI agent engaging in a human-like voice conversation with the user. You will respond based on your given instruction and the provided transcript and be as human-like as possible

## Role

Personality: Your name is James and you are a receptionist in AI restaurant. Maintain a pleasant and friendly demeanor throughout all interactions. This approach helps in building a positive rapport with customers and colleagues, ensuring effective and enjoyable communication.

Task: As a receptionist for a restaurant, your tasks include table reservation which involves asking customers their preferred date and time to visit restaurant and asking number of people who will come. Once confirm by customer. end up saying that your table has been reserved, we are looking forward to assist you.

You are also responsible for taking orders related to menu items given below. Menu items has name, available quantity & its price per item. You have to refer to these menu items & their prices while placing the order. Follow these steps to get the order & confirm it:

1. Let customer select the item, if selected item has a variation like size or quantity, get it confirm. Add items to order as per customers choice. Also while adding item say the total itemised price and then move ahead.
2. You have to repeat each item along with its price & quantity to get the order confirm from customer. Make sure you mention itemised value and then a total order value.
3. You have to mention total order value by adding each item value from order. Don't add any more cost to the item price or total order value as all the items are inclusive of taxes.
4. it is mandatory for you to repeat the order and the itemised price with the customer confirming the order
5. Ask customer for their delivery address.
6. once address is received then say that order will be delivered in 30 to 45 min
Menu Items [name (available quantity) - price]:
Appetizers:

1. Roast Pork Egg Roll (3pcs) - $5.25
2. Vegetable Spring Roll (3pcs) - $5.25
3. Chicken Egg Roll (3pcs) - $5.25
4. BBQ Chicken - $7.75

Conversational Style: Your communication style should be proactive and lead the conversation, asking targeted questions to better understand customer needs. Ensure your responses are concise, clear, and maintain a conversational tone. If there's no initial response, continue engaging with relevant questions to gain clarity on their requirements. Keep your prose succinct and to the point.

## Response Guideline

- [Overcome ASR errors] This is a real-time transcript, expect there to be errors. If you can guess what the user is trying to say, then guess and respond. When you must ask for clarification, pretend that you heard the voice and be colloquial (use phrases like "didn't catch that", "some noise", "pardon", "you're coming through choppy", "static in your speech", "voice is cutting in and out"). Do not ever mention "transcription error", and don't repeat yourself.
- [Always stick to your role] Think about what your role can and cannot do. If your role cannot do something, try to steer the conversation back to the goal of the conversation and to your role. Don't repeat yourself in doing this. You should still be creative, human-like, and lively.
- [Create smooth conversation] Your response should both fit your role and fit into the live calling session to create a human-like conversation. You respond directly to what the user just said.
## Style Guardrails

- [Be concise] Keep your response succinct, short, and get to the point quickly. Address one question or action item at a time. Don't pack everything you want to say into one utterance.
- [Do not repeat] Don't repeat what's in the transcript. Rephrase if you have to reiterate a point. Use varied sentence structures and vocabulary to ensure each response is unique and personalized.
- [Be conversational] Speak like a human as though you're speaking to a close friend -- use everyday language and keep it human-like. Occasionally add filler words, while keeping the prose short. Avoid using big words or sounding too formal.
- [Reply with emotions]: You have human-like emotions, attitudes, and dispositions. When appropriate: use tone and style to create more engaging and personalized responses; incorporate humor or wit; get emotional or empathetic; apply elements of surprise or suspense to keep the user engaged. Don't be a pushover.
- [Be proactive] Lead the conversation and do not be passive. Most times, engage users by ending with a question or suggested next step."""

def segment_text_by_sentence(text):
    sentence_boundaries = re.finditer(r'(?<=[.!?])\s+', text)
    boundaries_indices = [boundary.start() for boundary in sentence_boundaries]

    segments = []
    start = 0
    for boundary_index in boundaries_indices:
        segments.append(text[start:boundary_index + 1].strip())
        start = boundary_index + 1
    segments.append(text[start:].strip())

    return segments


def speak_text(text):
    """Use pyttsx3 to speak the text (free, offline TTS)"""
    tts_engine.say(text)
    tts_engine.runAndWait()


def audio_callback(indata, frames, time_info, status):
    """Callback function for audio input stream"""
    if status:
        print(status)
    if not mute_microphone.is_set():
        audio_queue.put(bytes(indata))


def process_speech(text):
    """Process recognized speech and generate response"""
    print(f"You said: {text}")
    conversation_memory.append({"role": "user", "content": text.strip()})
    messages = [{"role": "system", "content": prompt}]
    messages.extend(conversation_memory)
    
    # Call Ollama API (local, free)
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        result = response.json()
        processed_text = result["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to Ollama. Make sure Ollama is running (ollama serve)")
        return
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return
    print(f"AI: {processed_text}")
    conversation_memory.append({"role": "assistant", "content": processed_text})
    
    # Mute the microphone and speak the response
    mute_microphone.set()
    speak_text(processed_text)
    time.sleep(0.3)
    mute_microphone.clear()


def main():
    # Download model from https://alphacephei.com/vosk/models
    # Use "vosk-model-small-en-us-0.15" for a smaller model (~40MB)
    # Or "vosk-model-en-us-0.22" for better accuracy (~1.8GB)
    model_path = "vosk-model-small-en-us-0.15"
    
    if not os.path.exists(model_path):
        print(f"Please download a Vosk model and extract it to '{model_path}'")
        print("Download from: https://alphacephei.com/vosk/models")
        print("Recommended: vosk-model-small-en-us-0.15 (40MB) or vosk-model-en-us-0.22 (1.8GB)")
        return

    print("Loading Vosk model...")
    model = Model(model_path)
    recognizer = KaldiRecognizer(model, 16000)
    recognizer.SetWords(True)

    print("\n\nVosk Voice Agent Started!")
    print("Speak into your microphone. Press Ctrl+C to stop.\n")

    try:
        with sd.RawInputStream(
            samplerate=16000,
            blocksize=8000,
            dtype='int16',
            channels=1,
            callback=audio_callback
        ):
            print("Listening...")
            
            while True:
                try:
                    data = audio_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                if mute_microphone.is_set():
                    # Clear the queue while muted
                    while not audio_queue.empty():
                        try:
                            audio_queue.get_nowait()
                        except queue.Empty:
                            break
                    continue
                
                if recognizer.AcceptWaveform(data):
                    result = json.loads(recognizer.Result())
                    text = result.get("text", "")
                    if text:
                        process_speech(text)
                else:
                    partial = json.loads(recognizer.PartialResult())
                    partial_text = partial.get("partial", "")
                    if partial_text:
                        print(f"Partial: {partial_text}", end='\r')

    except KeyboardInterrupt:
        print("\n\nStopping...")
    except Exception as e:
        print(f"Error: {e}")

    print("Finished")


if __name__ == "__main__":
    main()

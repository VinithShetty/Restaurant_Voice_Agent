# AI-Voice-Agent
Self-hosted AI voice agent - **100% FREE & Offline**

Open-source AI agent which can handle voice calls and respond back in real-time. Can be used for many use-cases such as sales calls, customer support etc.

This fork uses **completely free and offline** components:
- 🎤 **Vosk** - Free offline speech-to-text
- 🤖 **Ollama** - Free local LLM (Llama 3.2, Mistral, etc.)
- 🔊 **pyttsx3** - Free offline text-to-speech

### Original Tutorial
- Youtube Tutorial -> https://youtu.be/77xnx26dyYU
- Medium Article -> https://medium.com/@anilmatcha/ai-voice-agent-how-to-build-one-in-minutes-a-comprehensive-guide-032a79a1ac1e

---

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) installed
- Vosk speech recognition model

## Setup Instructions

### 1. Install Ollama

Download and install from [ollama.com](https://ollama.com)

Then pull a model:
```bash
ollama pull llama3.2
```

### 2. Download Vosk Model

Download [vosk-model-small-en-us-0.15](https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip) (~40MB)

Extract the folder to this directory so you have:
```
AI-Voice-Agent/
├── vosk-model-small-en-us-0.15/
├── app_vosk.py
├── requirements_vosk.txt
└── ...
```

For better accuracy, use [vosk-model-en-us-0.22](https://alphacephei.com/vosk/models) (~1.8GB)

### 3. Install Python Dependencies

Create a virtual environment and install dependencies:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

pip install -r requirements_vosk.txt
```

### 4. Run the App

```bash
python app_vosk.py
```

Speak into your microphone and the AI will respond!

---

## Configuration

### Change the LLM Model

Edit `app_vosk.py` line 13 to use different Ollama models:
```python
OLLAMA_MODEL = "llama3.2"  # or "mistral", "phi3", "gemma2"
```

### Change the Vosk Model

Edit `app_vosk.py` to point to a different model folder:
```python
model_path = "vosk-model-en-us-0.22"  # for better accuracy
```

### Adjust TTS Voice

Edit the pyttsx3 settings in `app_vosk.py`:
```python
tts_engine.setProperty('rate', 175)  # Speech speed
tts_engine.setProperty('voice', voices[0].id)  # 0=male, 1=female
```

---

## Original Version (Paid APIs)

To use the original version with Deepgram and OpenAI:

1. Create `.env` file with your API keys:
   ```
   DEEPGRAM_API_KEY=your_key
   OPENAI_API_KEY=your_key
   ```

2. Install original dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run:
   ```bash
   python app.py
   ```

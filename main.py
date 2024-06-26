import os
import random
import asyncio
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from google.cloud import speech_v1p1beta1 as speech
from google.cloud import translate_v2 as translate

# Initialize Translation client
translate_client = translate.Client()

# Initialize Speech-to-Text client
client = speech.SpeechClient()

def check_file_existence(func):
    def wrapper(file_path, *args, **kwargs):
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
        return func(file_path, *args, **kwargs)
    return wrapper

def supported_format(func):
    def wrapper(file_path, *args, **kwargs):
        _, file_extension = os.path.splitext(file_path)
        supported_formats = ['.txt', '.mp3', '.wav', '.docx']
        if file_extension.lower() not in supported_formats:
            print("Unsupported file format.")
            return None
        return func(file_path, *args, **kwargs)
    return wrapper

def detect_language(text):
    response = translate_client.detect_language(text)
    return response['language']

async def transcribe_audio(file_path):
    with open(file_path, 'rb') as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        language_code='en-US',
    )

    response = await client.recognize(config=config, audio=audio)
    transcript = ''.join(result.alternatives[0].transcript for result in response.results)
    return transcript

async def translate_file(file_path, target_language='ja'):
    _, file_extension = os.path.splitext(file_path)
    
    if file_extension.lower() == '.txt':
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        source_language = detect_language(content)
        if source_language != target_language:
            translated_content = translate_text(content, target_language)
        else:
            print("Input text is already in the target language.")
            return None
    else:
        transcript = await transcribe_audio(file_path)
        if not transcript:
            return None
        source_language = detect_language(transcript)
        if source_language != target_language:
            translated_content = translate_text(transcript, target_language)
        else:
            print("Input audio is already in the target language.")
            return None
    
    return translated_content

def save_translation(translated_content, output_file_path):
    with open(output_file_path, 'w', encoding='utf-8') as file:
        file.write(translated_content)
    print(f"Translated content saved to {output_file_path}")

async def batch_translate(file_paths, output_dir, progress_callback, target_language='ja'):
    tasks = [translate_file(file_path, target_language) for file_path in file_paths]
    translations = await asyncio.gather(*tasks)
    for i, (file_path, translation) in enumerate(zip(file_paths, translations)):
        if translation:
            file_name = os.path.basename(file_path)
            output_file_path = os.path.join(output_dir, f"translated_{file_name}")
            save_translation(translation, output_file_path)
        progress_callback(i + 1, len(file_paths))

def translate_text(text, target_language='ja', glossary=None, context=None):
    translation = translate_client.translate(text, target_language=target_language)
    return translation['translatedText']

def translate_conversation(input_text, target_language='ja'):
    source_language = detect_language(input_text)
    if source_language != target_language:
        translated_content = translate_text(input_text, target_language)
        return translated_content
    else:
        print("Input text is already in the target language.")
        return None

def translate_forum_post(input_text, target_language='ja'):
    source_language = detect_language(input_text)
    if source_language != target_language:
        translated_content = translate_text(input_text, target_language)
        return translated_content
    else:
        print("Input text is already in the target language.")
        return None

def get_daily_challenge():
    challenges = [
        "Write a short paragraph about your day in Japanese.",
        "Translate the following sentence to Japanese: 'I am learning Japanese to improve my skills.'",
        "Read a Japanese article and summarize it in English.",
        "Listen to a Japanese podcast or song and write down what you understand.",
        "Have a conversation with a digital pen pal about your hobbies in Japanese.",
        "Write a forum post in Japanese about your favorite book.",
        "Translate a cooking recipe from English to Japanese.",
        "Practice speaking by recording yourself introducing your family in Japanese."
    ]
    return random.choice(challenges)

class TranslatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Japanese Translation and Learning App")
        self.geometry("700x700")
        
        self.create_widgets()
        self.default_output_dir = os.path.expanduser("~")
        self.default_target_language = 'ja'

    def create_widgets(self):
        self.daily_challenge_label = tk.Label(self, text="Welcome! Here's your daily challenge:")
        self.daily_challenge_label.pack(pady=10)
        
        self.daily_challenge_text = tk.Label(self, text=get_daily_challenge(), wraplength=600)
        self.daily_challenge_text.pack(pady=10)
        
        self.option_label = tk.Label(self, text="Choose an option:")
        self.option_label.pack(pady=10)

        self.file_translate_frame = tk.Frame(self)
        self.file_translate_frame.pack(pady=5)
        self.translate_files_button = tk.Button(self.file_translate_frame, text="Translate Files", command=self.translate_files)
        self.translate_files_button.pack(side=tk.LEFT, padx=5)

        self.translate_conversation_button = tk.Button(self, text="Translate Conversation", command=self.translate_conversation)
        self.translate_conversation_button.pack(pady=5)

        self.translate_forum_post_button = tk.Button(self, text="Translate Forum Post", command=self.translate_forum_post)
        self.translate_forum_post_button.pack(pady=5)

        self.settings_button = tk.Button(self, text="Settings", command=self.open_settings)
        self.settings_button.pack(pady=5)

        self.quit_button = tk.Button(self, text="Quit", command=self.quit)
        self.quit_button.pack(pady=10)

        self.progress = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress, maximum=100)
        self.progress_bar.pack(pady=10, fill=tk.X)

        self.output_text = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=10)
        self.output_text.pack(pady=10, fill=tk.BOTH, expand=True)
        
        self.status_bar = tk.Label(self, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def set_status(self, message):
        self.status_bar.config(text=message)
        self.status_bar.update_idletasks()

    def translate_files(self):
        file_paths = filedialog.askopenfilenames(title="Select files to translate", filetypes=[("Text files", "*.txt"), ("Audio files", "*.mp3 *.wav")])
        if not file_paths:
            return

        output_dir = filedialog.askdirectory(title="Select output directory", initialdir=self.default_output_dir)
        if not output_dir:
            return

        target_language = self.default_target_language

        self.progress.set(0)
        self.output_text.delete(1.0, tk.END)

        def progress_callback(current, total):
            self.progress.set((current / total) * 100)
            self.set_status(f"Translating file {current} of {total}")

        def run_translation():
            asyncio.run(batch_translate(file_paths, output_dir, progress_callback, target_language))
            self.set_status("Translation complete")
            messagebox.showinfo("Info", "Translation complete")

        threading.Thread(target=run_translation).start()

    def translate_conversation(self):
        input_text = tk.simpledialog.askstring("Input", "Enter the text for your conversation:")
        if input_text:
            translated_content = translate_conversation(input_text, self.default_target_language)
            if translated_content:
                self.output_text.delete(1.0, tk.END)
                self.output_text.insert(tk.END, translated_content)
                messagebox.showinfo("Translated Text", translated_content)

    def translate_forum_post(self):
        input_text = tk.simpledialog.askstring("Input", "Enter the text for your forum post:")
        if input_text:
            translated_content = translate_forum_post(input_text, self.default_target_language)
            if translated_content:
                self.output_text.delete(1.0, tk.END)
                self.output_text.insert(tk.END, translated_content)
                messagebox.showinfo("Translated Text", translated_content)

    def open_settings(self):
        settings_window = tk.Toplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("400x200")

        tk.Label(settings_window, text="Default Output Directory:").pack(pady=5)
        self.output_dir_entry = tk.Entry(settings_window, width=50)
        self.output_dir_entry.pack(pady=5)
        self.output_dir_entry.insert(0, self.default_output_dir)
        tk.Button(settings_window, text="Browse", command=self.set_output_dir).pack(pady=5)

        tk.Label(settings_window, text="Default Target Language:").pack(pady=5)
        self.language_entry = tk.Entry(settings_window, width=5)
        self.language_entry.pack(pady=5)
        self.language_entry.insert(0, self.default_target_language)

        tk.Button(settings_window, text="Save", command=self.save_settings).pack(pady=10)

    def set_output_dir(self):
        directory = filedialog.askdirectory(title="Select default output directory", initialdir=self.default_output_dir)
        if directory:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, directory)

    def save_settings(self):
        self.default_output_dir = self.output_dir_entry.get()
        self.default_target_language = self.language_entry.get()
        messagebox.showinfo("Settings", "Settings saved successfully")

if __name__ == "__main__":
    app = TranslatorApp()
    app.mainloop()

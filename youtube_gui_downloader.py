import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk
from yt_dlp import YoutubeDL
import threading
import re

# Detect ffmpeg location (works both in .py and in .exe)
if getattr(sys, 'frozen', False):
    # Running as a PyInstaller bundle
    ffmpeg_path = os.path.join(sys._MEIPASS, 'ffmpeg.exe')
else:
    ffmpeg_path = os.path.join(os.getcwd(), 'ffmpeg.exe')

SAVE_FOLDER = r"D:\Youtube Downloads"
os.makedirs(SAVE_FOLDER, exist_ok=True)

cancel_flag = False  # Global flag to cancel downloads

def human_readable(size_bytes):
    if size_bytes is None:
        return "?"
    for unit in ['B', 'KiB', 'MiB', 'GiB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f}TiB"

def format_status(d):
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', '').strip().replace('%', '')
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
        total_size = human_readable(total_bytes or 0)
        speed = human_readable(d.get('speed') or 0)
        eta = d.get('eta')
        eta_str = f"{int(eta // 60)}m {int(eta % 60)}s" if eta else "?"
        frag_index = d.get('fragment_index')
        frag_count = d.get('fragment_count')
        frag_info = f"(frag {frag_index}/{frag_count})" if frag_index else ""
        return percent, f"{percent}% of ~ {total_size} at {speed}/s ETA {eta_str} {frag_info}"
    return "0", ""

def progress_hook(d):
    if d['status'] == 'downloading':
        percent, status = format_status(d)
        status_label.config(text=status)
        try:
            progress_bar["value"] = float(percent)
        except:
            progress_bar["value"] = 0
        app.update_idletasks()
    elif d['status'] == 'finished':
        status_label.config(text="✅ Merging streams...")
        app.update_idletasks()

def threaded_download():
    global cancel_flag
    cancel_flag = False
    threading.Thread(target=download_videos).start()

def cancel_download():
    global cancel_flag
    cancel_flag = True
    status_label.config(text="🚫 Cancelling after current video...")
    app.update_idletasks()

def download_videos():
    global cancel_flag
    urls = link_textbox.get("1.0", tk.END).strip().splitlines()
    if not urls:
        messagebox.showerror("Error", "Please enter at least one YouTube URL.")
        return

    total = len(urls)
    success = 0
    fail = 0
    progress_bar["value"] = 0
    progress_bar["maximum"] = 100
    status_text.delete("1.0", tk.END)

    for i, url in enumerate(urls):
        if cancel_flag:
            status_text.insert(tk.END, f"🛑 Cancelled at: {url}\n")
            break

        try:
            ydl_opts = {
                'outtmpl': os.path.join(SAVE_FOLDER, '%(title)s.%(ext)s'),
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
                'ffmpeg_location': os.path.join(os.getcwd(), 'ffmpeg.exe'),
                'quiet': True,
                'noplaylist': True,
                'progress_hooks': [progress_hook],
                'ffmpeg_location': ffmpeg_path,
                'no_color': True,  # 🚨 Add this line to disable ANSI colors
            }

            status_text.insert(tk.END, f"⬇️ Downloading: {url}\n")
            app.update_idletasks()

            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            success += 1
            status_text.insert(tk.END, f"✅ Success: {url}\n\n")
        except Exception as e:
            fail += 1
            status_text.insert(tk.END, f"❌ Failed: {url}\nReason: {e}\n\n")

        progress_bar["value"] = 0
        status_label.config(text="")
        app.update_idletasks()

    if not cancel_flag:
        status_text.insert(tk.END, f"🎉 All Done!\n✅ Success: {success} ❌ Failed: {fail}")
        messagebox.showinfo("Done", "Batch download completed!")
    cancel_flag = False

# GUI setup
app = tk.Tk()
app.title("YouTube Downloader - Jojo")
app.geometry("620x600")
app.resizable(False, False)

# URL input
tk.Label(app, text="Paste YouTube URLs (one per line):").pack(pady=5)
link_textbox = tk.Text(app, height=10, width=70)
link_textbox.pack(pady=5)

# Download/Cancel Buttons
btn_frame = tk.Frame(app)
btn_frame.pack(pady=5)

tk.Button(btn_frame, text="Download Videos", command=threaded_download,
          bg="#2196F3", fg="white", padx=10, pady=5).pack(side=tk.LEFT, padx=10)
tk.Button(btn_frame, text="Cancel", command=cancel_download,
          bg="#F44336", fg="white", padx=10, pady=5).pack(side=tk.LEFT)

# Progress
tk.Label(app, text="Download Progress:").pack()
progress_bar = ttk.Progressbar(app, orient="horizontal", length=500, mode="determinate")
progress_bar.pack(pady=5)

status_label = tk.Label(app, text="", fg="black")
status_label.pack()

# Status Output
tk.Label(app, text="Download Status:").pack()
status_text = tk.Text(app, height=12, width=70)
status_text.pack(pady=5)

# Save folder info
tk.Label(app, text=f"📁 All videos saved to:\n{SAVE_FOLDER}", fg="gray").pack(pady=5)

app.mainloop()

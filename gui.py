import customtkinter as ctk
from tkinter import filedialog
import subprocess
import os
import threading
import random
import sys
from PIL import Image
import shutil
import tempfile

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


def get_ffmpeg_path():
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'bin', 'ffmpeg.exe')
    return os.path.join(os.path.dirname(__file__), 'bin', 'ffmpeg.exe')


class AudioPlaylistApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Audio Playlist Builder")
        self.geometry("700x650")

        self.files = []
        self.output_file = ctk.StringVar()
        self.repeat_count = ctk.IntVar(value=2)

        # =========================
        # Album Cover
        # =========================
        self.cover_path = ctk.StringVar()

        ctk.CTkButton(self, text="Select Album Cover", command=self.select_cover).pack(pady=5)
        self.cover_label = ctk.CTkLabel(self, text="No cover selected")
        self.cover_label.pack()

        # =========================
        # File Selection
        # =========================
        ctk.CTkButton(self, text="Add Audio Files", command=self.add_files).pack(pady=10)

        self.file_box = ctk.CTkTextbox(self, height=150)
        self.file_box.pack(fill="x", padx=10)

        # =========================
        # Output
        # =========================
        ctk.CTkButton(self, text="Select Output File", command=self.select_output).pack(pady=10)
        self.output_label = ctk.CTkLabel(self, text="No output selected")
        self.output_label.pack()

        # =========================
        # Repeat Control
        # =========================
        ctk.CTkLabel(self, text="Repeat Count").pack(pady=5)
        slider_frame = ctk.CTkFrame(self)
        slider_frame.pack(fill="x", padx=20)

        ctk.CTkLabel(slider_frame, text="Repeat Count").pack(anchor="w")

        self.repeat_label = ctk.CTkLabel(slider_frame, text="1")
        self.repeat_label.pack(anchor="e")

        def update_slider(value):
            self.repeat_label.configure(text=str(int(value)))

        ctk.CTkSlider(
            slider_frame,
            from_=1,
            to=3,
            number_of_steps=2,  # ensures only 1–5
            variable=self.repeat_count,
            command=update_slider
        ).pack(fill="x")

        # =========================
        # Start Button
        # =========================
        ctk.CTkButton(self, text="Build Playlist", command=self.start).pack(pady=15)

        # =========================
        # Logs
        # =========================
        self.log_box = ctk.CTkTextbox(self, height=200)
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

    def log(self, text):
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")

    def select_cover(self):
        file = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
        )
        if file:
            self.cover_path.set(file)
            self.cover_label.configure(text=os.path.basename(file))

            img = Image.open(file)
            img = img.resize((100, 100))
            self.cover_img = ctk.CTkImage(light_image=img, dark_image=img, size=(100, 100))

            if hasattr(self, "cover_preview"):
                self.cover_preview.destroy()

            self.cover_preview = ctk.CTkLabel(self, image=self.cover_img, text="")
            self.cover_preview.pack()

    def add_files(self):
        files = filedialog.askopenfilenames(
            filetypes=[("Audio Files", "*.mp3 *.wav *.aac *.m4a")]
        )
        self.files = list(files)

        self.file_box.delete("1.0", "end")
        for f in self.files:
            self.file_box.insert("end", f + "\n")

    def select_output(self):
        file = filedialog.asksaveasfilename(
            defaultextension=".mp3",
            filetypes=[("Audio", "*.mp3 *.wav")]
        )
        if file:
            self.output_file.set(file)
            self.output_label.configure(text=file)

    # def rename_files(self):
    #     if not self.files:
    #         return

    #     self.log("✏️ Renaming files...")

    #     renamed_files = []

    #     for i, file_path in enumerate(self.files, start=1):
    #         folder = os.path.dirname(file_path)
    #         ext = os.path.splitext(file_path)[1]

    #         new_name = f"{i:02d}{ext}"
    #         new_path = os.path.join(folder, new_name)

    #         try:
    #             os.rename(file_path, new_path)
    #             renamed_files.append(new_path)
    #             self.log(f"Renamed: {os.path.basename(file_path)} → {new_name}")
    #         except Exception as e:
    #             self.log(f"❌ Rename failed: {file_path} | {e}")
    #             renamed_files.append(file_path)  # fallback

    #     self.files = renamed_files

    def prepare_temp_files(self):
        if not self.files:
            return None

        self.log("📁 Creating temporary workspace...")

        temp_dir = tempfile.mkdtemp(prefix="playlist_")
        temp_files = []

        for i, file_path in enumerate(self.files, start=1):
            ext = os.path.splitext(file_path)[1]
            new_name = f"{i:02d}{ext}"
            new_path = os.path.join(temp_dir, new_name)

            try:
                shutil.copy2(file_path, new_path)
                temp_files.append(new_path)
                self.log(f"Copied: {os.path.basename(file_path)} → {new_name}")
            except Exception as e:
                self.log(f"❌ Copy failed: {file_path} | {e}")

        return temp_dir, temp_files

    def build_playlist(self):

        if not self.files or not self.output_file.get():
            self.log("❌ Please select files and output.")
            return       
        
        if self.cover_path.get() and self.output_file.get().endswith(".wav"):
            self.log("⚠️ WAV does not support album art. Please use MP3.")
            return

        ffmpeg = get_ffmpeg_path() 
        
        temp_data = self.prepare_temp_files()

        if not temp_data:
            self.log("❌ Failed to prepare files.")
            return
        
        temp_dir, working_files = temp_data

        try:
            self.log("🎲 Shuffling files...")

            shuffled = working_files.copy()
            random.shuffle(shuffled)

            final_list = shuffled * int(self.repeat_count.get())

        

            self.log("📜 Final playlist order:")
            for f in final_list:
                self.log(os.path.basename(f))

            # Create temporary concat file
            list_file = "file_list.txt"
            with open(list_file, "w", encoding="utf-8") as f:
                for path in final_list:
                    f.write(f"file '{path}'\n")

            self.log("🔄 Building output file...")

            command = [
                ffmpeg,
                "-f", "concat",
                "-safe", "0",
                "-i", list_file
            ]

            # Add cover if selected
            if self.cover_path.get():
                self.log("🖼️ Adding album cover...")
                command += [
                    "-i", self.cover_path.get(),
                    "-map", "0:a",
                    "-map", "1:v",
                    "-c:a", "libmp3lame",
                    "-b:a", "320k",
                    "-c:v", "mjpeg",
                    "-id3v2_version", "3"
                ]
            else:
                command += [
                    "-c", "copy"
                ]

            command += ["-y", self.output_file.get()]

            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            for line in process.stderr:
                self.log(line.strip())

            process.wait()

            os.remove(list_file)

            if process.returncode == 0:
                self.log("✅ Playlist created successfully!")
            else:
                self.log("❌ Failed to create playlist.")
        finally:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                self.log("🧹 Temporary files cleaned up.")
                
        # except Exception as e:
        #     self.log(f"ERROR: {str(e)}")

    def start(self):
        thread = threading.Thread(target=self.build_playlist)
        thread.start()


if __name__ == "__main__":
    app = AudioPlaylistApp()
    app.mainloop()
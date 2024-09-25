import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
from PIL import Image, ImageTk
from converter import VideoToGifConverter
import os
import subprocess

class VideoToGifConverterGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Video to GIF Converter")
        self.converter = VideoToGifConverter()
        self.videos = []
        self.current_video = None
        self.cap = None
        self.fps = None
        self.preview_mode = "start"

        self.preview_width = 640
        self.preview_height = 480
        self.crop_rect = None
        self.crop_start = None
        self.dragging = None
        self.active_edge = None

        self.create_widgets()

    def create_widgets(self):
        # Create main frames
        left_frame = tk.Frame(self.master)
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        right_frame = tk.Frame(self.master)
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        bottom_frame = tk.Frame(self.master)
        bottom_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")

        # Left frame widgets (Video selection, cutting, etc.)
        self.create_left_frame_widgets(left_frame)

        # Right frame widgets (Preview, cropping)
        self.create_right_frame_widgets(right_frame)

        # Bottom frame widgets (Output directory, Convert button)
        self.create_bottom_frame_widgets(bottom_frame)

    def create_left_frame_widgets(self, frame):
        tk.Label(frame, text="Input Videos:").pack(anchor="w")
        self.video_listbox = tk.Listbox(frame, width=50, height=10)
        self.video_listbox.pack(fill=tk.BOTH, expand=True)
        self.video_listbox.bind('<<ListboxSelect>>', self.on_video_select)
        
        button_frame = tk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=5)
        tk.Button(button_frame, text="Add Videos", command=self.add_videos).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Remove Selected", command=self.remove_video).pack(side=tk.LEFT, padx=5)

        tk.Label(frame, text="Start Frame:").pack(anchor="w")
        self.start_frame = tk.Scale(frame, from_=0, to=100, orient=tk.HORIZONTAL, command=lambda x: self.update_preview("start"))
        self.start_frame.pack(fill=tk.X)

        tk.Label(frame, text="End Frame:").pack(anchor="w")
        self.end_frame = tk.Scale(frame, from_=0, to=100, orient=tk.HORIZONTAL, command=lambda x: self.update_preview("end"))
        self.end_frame.pack(fill=tk.X)

        preview_button_frame = tk.Frame(frame)
        preview_button_frame.pack(fill=tk.X, pady=5)
        tk.Button(preview_button_frame, text="Preview Start", command=lambda: self.update_preview("start")).pack(side=tk.LEFT, padx=5)
        tk.Button(preview_button_frame, text="Preview End", command=lambda: self.update_preview("end")).pack(side=tk.LEFT, padx=5)

    def create_right_frame_widgets(self, frame):
        self.preview_frame = tk.Frame(frame, width=self.preview_width, height=self.preview_height)
        self.preview_frame.pack(fill=tk.BOTH, expand=True)
        self.preview_canvas = tk.Canvas(self.preview_frame, width=self.preview_width, height=self.preview_height)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        self.preview_canvas.bind("<ButtonPress-1>", self.start_crop)
        self.preview_canvas.bind("<B1-Motion>", self.draw_crop)
        self.preview_canvas.bind("<ButtonRelease-1>", self.end_crop)

        tk.Label(frame, text="Crop (Left Top Right Bottom):").pack(anchor="w")
        self.crop = tk.Entry(frame)
        self.crop.pack(fill=tk.X)

    def create_bottom_frame_widgets(self, frame):
        # Output directory
        output_frame = tk.Frame(frame)
        output_frame.pack(fill=tk.X, pady=5)
        tk.Label(output_frame, text="Output Directory:").pack(side=tk.LEFT)
        self.output_dir = tk.Entry(output_frame, width=40)
        self.output_dir.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        self.output_dir.insert(0, "output_directory")
        tk.Button(output_frame, text="Browse", command=self.browse_output).pack(side=tk.LEFT)

        # Convert button
        tk.Button(frame, text="Convert", command=self.convert).pack(pady=10)

    def start_crop(self, event):
        x, y = event.x, event.y
        if self.crop_rect:
            x1, y1, x2, y2 = self.crop_rect
            tolerance = 10
            if abs(x - x1) < tolerance and abs(y - y1) < tolerance:
                self.dragging = "topleft"
            elif abs(x - x2) < tolerance and abs(y - y1) < tolerance:
                self.dragging = "topright"
            elif abs(x - x1) < tolerance and abs(y - y2) < tolerance:
                self.dragging = "bottomleft"
            elif abs(x - x2) < tolerance and abs(y - y2) < tolerance:
                self.dragging = "bottomright"
            elif abs(x - x1) < tolerance:
                self.dragging = "left"
            elif abs(x - x2) < tolerance:
                self.dragging = "right"
            elif abs(y - y1) < tolerance:
                self.dragging = "top"
            elif abs(y - y2) < tolerance:
                self.dragging = "bottom"
            else:
                self.dragging = "new"
        else:
            self.dragging = "new"
        self.crop_start = (x, y)

    def draw_crop(self, event):
        if self.dragging == "new":
            self.preview_canvas.delete("crop")
            self.crop_rect = (*self.crop_start, event.x, event.y)
            self.preview_canvas.create_rectangle(*self.crop_rect, outline="red", tags="crop")
        elif self.dragging:
            x1, y1, x2, y2 = self.crop_rect
            if self.dragging in ["topleft", "left", "bottomleft"]:
                x1 = event.x
            if self.dragging in ["topright", "right", "bottomright"]:
                x2 = event.x
            if self.dragging in ["topleft", "top", "topright"]:
                y1 = event.y
            if self.dragging in ["bottomleft", "bottom", "bottomright"]:
                y2 = event.y
            self.crop_rect = (x1, y1, x2, y2)
            self.preview_canvas.delete("crop")
            self.preview_canvas.create_rectangle(*self.crop_rect, outline="red", tags="crop")

        self.crop_start = (event.x, event.y)  # Update crop_start for continuous dragging

    def end_crop(self, event):
        if self.crop_rect:
            x1, y1, x2, y2 = self.crop_rect
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            self.crop_rect = (x1, y1, x2, y2)
            self.preview_canvas.delete("crop")
            self.preview_canvas.create_rectangle(*self.crop_rect, outline="red", tags="crop")

        self.dragging = None
        self.active_edge = None

        # Calculate crop values relative to original video size
        if self.crop_rect:
            video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            x1, y1, x2, y2 = self.crop_rect
            x1 = max(0, int(x1 * video_width / self.preview_width))
            y1 = max(0, int(y1 * video_height / self.preview_height))
            x2 = min(video_width, int(x2 * video_width / self.preview_width))
            y2 = min(video_height, int(y2 * video_height / self.preview_height))
            
            crop_values = (x1, y1, x2 - x1, y2 - y1)  # left, top, width, height
            self.videos[self.current_video]["crop"] = crop_values
            self.crop.delete(0, tk.END)
            self.crop.insert(0, " ".join(map(str, crop_values)))

    def update_preview(self, mode=None):
        if mode:
            self.preview_mode = mode

        if self.cap is not None:
            if self.preview_mode == "start":
                frame_number = int(self.start_frame.get())
            else:  # end mode
                frame_number = int(self.end_frame.get())

            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.resize(frame, (self.preview_width, self.preview_height))
                photo = ImageTk.PhotoImage(image=Image.fromarray(frame))
                self.preview_canvas.create_image(0, 0, image=photo, anchor=tk.NW)
                self.preview_canvas.image = photo

                # Add text to indicate which frame is being previewed
                self.preview_canvas.create_text(10, 10, anchor="nw", text=f"{self.preview_mode.capitalize()} Frame: {frame_number}", fill="white", font=("Arial", 12))

                # Draw crop rectangle if it exists
                if self.videos[self.current_video].get("crop"):
                    crop = self.videos[self.current_video]["crop"]
                    x1 = crop[0] * self.preview_width / int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    y1 = crop[1] * self.preview_height / int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    x2 = x1 + crop[2] * self.preview_width / int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    y2 = y1 + crop[3] * self.preview_height / int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    self.crop_rect = (x1, y1, x2, y2)
                    self.preview_canvas.delete("crop")
                    self.preview_canvas.create_rectangle(*self.crop_rect, outline="red", tags="crop")

            # Update and save the video data
            self.videos[self.current_video]["start"] = int(self.start_frame.get())
            self.videos[self.current_video]["end"] = int(self.end_frame.get())

    def add_videos(self):
        files = filedialog.askopenfilenames(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        for file in files:
            cap = cv2.VideoCapture(file)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            cap.release()
            self.videos.append({
                "path": file,
                "start": 0,
                "end": total_frames,
                "crop": None,
            })
            self.video_listbox.insert(tk.END, os.path.basename(file))

    def remove_video(self):
        selection = self.video_listbox.curselection()
        if selection:
            index = selection[0]
            self.video_listbox.delete(index)
            del self.videos[index]
            if self.current_video == index:
                self.current_video = None
                self.cap = None
                self.preview_canvas.delete("all")

    def on_video_select(self, event):
        selection = self.video_listbox.curselection()
        if selection:
            index = selection[0]
            self.current_video = index
            self.load_video(self.videos[index]["path"])

    def load_video(self, video_path):
        self.cap = cv2.VideoCapture(video_path)
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        video_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Calculate new dimensions to maintain aspect ratio
        ratio = min(self.preview_width / video_width, self.preview_height / video_height)
        self.preview_width = int(video_width * ratio)
        self.preview_height = int(video_height * ratio)

        self.preview_canvas.config(width=self.preview_width, height=self.preview_height)

        self.start_frame.config(to=total_frames)
        self.end_frame.config(to=total_frames)
        self.end_frame.set(total_frames)

        # Set the stored start and end frames
        self.start_frame.set(self.videos[self.current_video].get("start", 0))
        self.end_frame.set(self.videos[self.current_video].get("end", total_frames))

        # Set the crop values
        crop = self.videos[self.current_video].get("crop")
        if crop:
            self.crop.delete(0, tk.END)
            self.crop.insert(0, " ".join(map(str, crop)))
            self.redraw_crop_rectangle()
        else:
            self.crop.delete(0, tk.END)
            self.crop_rect = None

        self.update_preview()

    def redraw_crop_rectangle(self):
        if self.crop_rect:
            x1, y1, x2, y2 = self.crop_rect
            self.preview_canvas.delete("crop")
            self.preview_canvas.create_rectangle(x1, y1, x2, y2, outline="red", tags="crop")

    def browse_output(self):
        directory = filedialog.askdirectory()
        self.output_dir.delete(0, tk.END)
        self.output_dir.insert(0, directory)

    def convert(self):
        try:
            print("Starting conversion process...")
            self.converter.batch_add_videos([video["path"] for video in self.videos])

            for i, video in enumerate(self.videos):
                print(f"Processing video {i+1}/{len(self.videos)}")
                start_frame = video["start"]
                end_frame = video["end"]
                crop_area = video.get("crop")

                if crop_area:
                    print(f"Cropping video {i+1}")
                    cropped_video = self.converter.crop_video_frames(video["path"], crop_area)
                else:
                    cropped_video = video["path"]

                print(f"Cutting video {i+1}")
                cut_video = self.converter.cut_video_segment(cropped_video, start_frame, end_frame)
                print(f"Converting video {i+1} to GIF")
                self.converter.convert_video_to_gif(cut_video, "unchanged")

            print("GIF conversion completed")

            # Save GIFs
            output_directory = self.output_dir.get()
            print(f"Saving GIFs to {output_directory}")
            self.converter.save_gifs(output_directory)

            print("Conversion process completed successfully")
            messagebox.showinfo("Success", "Conversion completed successfully!")
            
            # Open the output folder in file explorer
            self.open_output_folder(output_directory)

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            messagebox.showerror("Error", str(e))

    def open_output_folder(self, path):
        if os.path.exists(path):
            if os.name == 'nt':  # For Windows
                os.startfile(path)
            elif os.name == 'posix':  # For macOS and Linux
                subprocess.call(['open', path])
        else:
            messagebox.showerror("Error", f"Output folder not found: {path}")
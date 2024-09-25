import os
import shutil
import ffmpeg
from PIL import Image, ImageSequence
from moviepy.editor import VideoFileClip
import cv2

class VideoToGifConverter:
    def __init__(self):
        self.videos = []
        self.gifs = []
        self.temp_dir = os.path.join(os.getcwd(), 'temp')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def __del__(self):
        # Clean up temporary directory when the object is destroyed
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def batch_add_videos(self, video_paths):
        self.videos.extend(video_paths)

    def cut_video_segment(self, video_path, start_frame, end_frame):
        output_path = os.path.join(self.temp_dir, f"{os.path.splitext(os.path.basename(video_path))[0]}_cut.mp4")
        stream = ffmpeg.input(video_path)
        stream = ffmpeg.trim(stream, start_frame=start_frame, end_frame=end_frame)
        stream = ffmpeg.setpts(stream, 'PTS-STARTPTS')
        stream = ffmpeg.output(stream, output_path, vcodec='libx264', acodec='aac')
        ffmpeg.run(stream, overwrite_output=True)
        return output_path

    def crop_video_frames(self, video_path, crop_area):
        output_path = os.path.join(self.temp_dir, f"{os.path.splitext(os.path.basename(video_path))[0]}_cropped.mp4")
        left, top, width, height = crop_area
        
        # Ensure width and height are positive
        width = abs(width)
        height = abs(height)
        
        # Ensure left and top are non-negative
        left = max(0, left)
        top = max(0, top)
        
        stream = ffmpeg.input(video_path)
        stream = ffmpeg.crop(stream, left, top, width, height)
        stream = ffmpeg.output(stream, output_path)
        ffmpeg.run(stream)
        return output_path

    def convert_video_to_gif(self, video_path, resize_value="auto"):
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        if base_name.endswith('_cut'):
            base_name = base_name[:-4]  # Remove '_cut' suffix
        output_path = os.path.join(self.temp_dir, f"{base_name}_converted.gif")
        
        print(f"Converting video to GIF: {video_path}")
        
        video = VideoFileClip(video_path)
        
        if video.duration > 10:
            speedup_factor = video.duration / 10
            video = video.speedx(speedup_factor)
        
        video = video.set_fps(10)
        
        original_size = video.size
        if resize_value == "auto":
            scale = 550 / original_size[1]
            new_size = (int(original_size[0] * scale), 550)
        elif resize_value != "unchanged":
            scale = float(resize_value) / 100
            new_size = (int(original_size[0] * scale), int(original_size[1] * scale))
        else:
            new_size = original_size
        
        video = video.resize(newsize=new_size)
        
        print(f"Resized video to {new_size}")
        
        print(f"Writing GIF to: {output_path}")
        video.write_gif(output_path, program='ffmpeg')
        
        video.close()
        
        print(f"Opening GIF for frame extraction: {output_path}")
        with Image.open(output_path) as img:
            frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
        
        print(f"Adding GIF to list with {len(frames)} frames")
        self.gifs.append({'frames': frames, 'name': base_name, 'duration': 100})

    def convert_video_to_frames(self, video_path):
        cap = cv2.VideoCapture(video_path)
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        cap.release()
        return frames

    def save_gifs(self, output_directory):
        os.makedirs(output_directory, exist_ok=True)
        for i, gif in enumerate(self.gifs):
            output_path = os.path.join(output_directory, f"{gif['name']}_converted.gif")
            print(f"Saving GIF {i+1}/{len(self.gifs)}: {output_path}")
            try:
                gif['frames'][0].save(
                    output_path,
                    save_all=True,
                    append_images=gif['frames'][1:],
                    loop=0,
                    duration=100,
                    disposal=2
                )
                print(f"Successfully saved GIF {i+1}")
            except Exception as e:
                print(f"Error saving GIF {i+1}: {str(e)}")
                print(f"Frames in GIF: {len(gif['frames'])}")
                print(f"First frame size: {gif['frames'][0].size}")
                raise
        print(f"Saved {len(self.gifs)} GIFs to {output_directory}")

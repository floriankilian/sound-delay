import numpy as np
import matplotlib.pyplot as plt
from mosqito.utils import load
from mosqito.sq_metrics import loudness_zwtv
import cv2
try:
    from moviepy.editor import VideoFileClip
except RuntimeError:
    print("Failed to initialize VideoFileClip. Ensure ffmpeg is installed.")
except ImportError:
    print("Failed to import VideoFileClip.")



def extract_audio_from_video(video_path):
    """Extract audio from the video."""
    try:
        # Check if VideoFileClip was imported
        if 'VideoFileClip' not in globals():
            raise RuntimeError("VideoFileClip is not imported. Ensure ffmpeg is installed and moviepy is imported successfully. You can still continue with providing your own soundfile as .wav")
        
        # Replace .mp4 with .wav (super simple)
        audio_path = video_path[:-3] + 'wav'

        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(audio_path, codec='pcm_s16le')
        audio.close()
        
        print("Audio extracted successfully!")
        return audio_path
    except Exception as e:
        print(f"Error encountered during audio extraction: {e}")
        return None



# Get input file paths
audio_path = input('Enter path of audio file: ')
video_path = input('Enter path of video file: ')

#
# Process Audio
#

print('Processing audio...')

# Load audio file
sig, fs = load(audio_path, wav_calib=2 * 2 **0.5)

# Compute loudness
loudness, N_spec, bark_axis, time_audio = loudness_zwtv(sig, fs, field_type="free")

#
# Process Video
#

print('Processing video...')

# Capture video
cap = cv2.VideoCapture(video_path)

# Count frames and pre-allocated array for red intensity
nframes = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
red_intensity = np.zeros(nframes)

# Print frame rate to screen
frame_rate = int(cap.get(cv2.CAP_PROP_FPS))
print(str(frame_rate) + ' frames/second')

# Loop through frames
frame_index = 0
while cap.isOpened():
    # Read in a frame
    ret, frame = cap.read()
    if not ret:
        break

    # Extract the red channel (OpenCV uses BGR order)    
    red_frame = frame[:, :, 2]  

    # Take mean of the red channel across all pixels
    red_intensity[frame_index] = red_frame.mean()

    # Increment frame index
    frame_index += 1

# Clean up 
cap.release()
cv2.destroyAllWindows()

#
# Plot signals
#

# Rescale red intensity amplitude to match audio signal amplitude
red_intensity = red_intensity - np.min(red_intensity) + np.min(loudness)
red_intensity = red_intensity*np.max(loudness)/np.max(red_intensity)

# Get min and max of time axis
time_min = time_audio[0]
time_max = time_audio[-1]

# Get min and max of amplitude axis
amp_min = np.min(red_intensity) - 0.1*( np.max(red_intensity) - np.min(red_intensity) )
amp_max = np.max(red_intensity) + 0.1*( np.max(red_intensity) - np.min(red_intensity) )

# Create time axis variable for video matching audio time axis
time_video = np.linspace(time_min, time_max, len(red_intensity))

# Plot
fig = plt.figure()
ax = fig.add_axes([0.1, 0.1, 0.8, 0.8])
ax.plot(time_audio, loudness, 'b-')
ax.plot(time_video, red_intensity, 'r-')
ax.legend(['loudness','red intensity'])
ax.set_xlim(time_min, time_max)
ax.set_ylim(amp_min, amp_max)
ax.set_yticks([])
ax.set_xlabel('Time [seconds]')
ax.set_ylabel('Amplitude')
plt.grid()
plt.show()


import subprocess

def download_youtube_video():
    try:
        # Get the YouTube URL from the user
        url = input("Enter the YouTube URL: ")

        # Download the video using yt-dlp
        print("Starting download...")
        subprocess.run([
            "yt-dlp",
            "--format", "best",  # Choose the best available format
            "--output", "%(title)s.%(ext)s",  # Save video with its title as filename
            url
        ], check=True)

        print("Download complete.")
    except subprocess.CalledProcessError as e:
        print("An error occurred during download:", str(e))
    except Exception as e:
        print("An unexpected error occurred:", str(e))

if __name__ == "__main__":
    download_youtube_video()

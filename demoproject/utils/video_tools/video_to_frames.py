from os.path import basename
from os.path import exists
from os.path import isfile
from pathlib import Path
from shutil import rmtree

import cv2


def video_to_frames(video_filename, output_dir, skip_if_dir_exists=False):
    print("Start extracting frames from {} to {}".format(video_filename, output_dir))
    output_dir_path = Path(output_dir)
    video_basename = basename(video_filename).split('.')[0]
    if skip_if_dir_exists is True and output_dir_path.exists():
        print(
            "Frame directory '{}' exists. "
            "Skipping extracting frames from {}".format(output_dir, video_filename)
        )
        return

    if output_dir_path.exists():
        rmtree(output_dir)

    output_dir_path.mkdir(0o777, parents=True, exist_ok=False)

    if exists(video_filename) and isfile(video_filename):
        print("File {} exists".format(video_filename))
    else:
        print("File {} does not exist!".format(video_filename))

    vidcap = cv2.VideoCapture(str(video_filename))
    print("VideoCapture of {} created? {}".format(video_filename, vidcap.isOpened()))

    if not vidcap.isOpened():
        raise IOError

    success, image = vidcap.read()
    count = 0
    print(
        "Extracting frames from video '{}' to folder '{}'...".format(
            video_filename, output_dir
        )
    )
    while success:
        cv2.imwrite(f"{output_dir}/{video_basename}_frame-{count:05d}.png", image)
        success, image = vidcap.read()
        count += 1

    print(f"{count} frames extracted")
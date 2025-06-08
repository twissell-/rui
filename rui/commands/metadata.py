import json
import logging
import os
from datetime import datetime
from os.path import abspath, basename, isdir

from Levenshtein import distance
from pymediainfo import MediaInfo
from rich import print
from rich.progress import track

from rui import anilist
from rui.anilist.model import ListEntry
from rui.common import config, fileManager

logger = logging.getLogger(__name__)
_metadata_file_name = "metadata.json"


def _get_anime_metadata(anime: ListEntry) -> dict:

    metadata = anilist.getAnimeById(anime.id)

    if metadata.get("coverImage"):
        metadata["coverImage"] = metadata["coverImage"]["extraLarge"]

    if metadata.get("relations"):
        metadata["relations"] = metadata["relations"]["edges"]

    return metadata


def _get_file_metadata(file_path: str) -> dict:
    try:
        logger.debug(f"Analizing {file_path}")
        media_info = MediaInfo.parse(file_path)
    except FileNotFoundError as e:
        logger.error(e)
        return None

    file_metadata = {}
    for track in media_info.tracks:
        try:
            if track.track_type == "General":
                file_metadata["file_name"] = track.file_name_extension
                file_metadata["format"] = track.format
                file_metadata["file_size"] = track.other_file_size[0]
                file_metadata["file_size_bytes"] = track.file_size
                file_metadata["duration"] = (
                    track.other_duration[0] if track.other_duration else None
                )
                file_metadata["duration_seconds"] = (
                    (float(track.duration) / 1000) if track.duration else None
                )  # to seconds
            elif track.track_type == "Video":
                file_metadata["video"] = {
                    "format": track.format,
                    "codec": track.codec_id,
                    "resolution": f"{track.width}x{track.height}",
                    "aspect_ration": track.other_display_aspect_ratio[0],
                    "frame_rate": track.frame_rate,
                }
            elif track.track_type == "Audio":
                if not file_metadata.get("audio"):
                    file_metadata["audio"] = []

                file_metadata["audio"].append(
                    {
                        "format": track.format,
                        "sampling_rate": track.other_sampling_rate[0],
                        "compression_mode": track.compression_mode,
                    }
                )
            elif track.track_type == "Text":
                if not file_metadata.get("subtitles"):
                    file_metadata["subtitles"] = []

                file_metadata["subtitles"].append(
                    {
                        "format": track.format,
                        "title": track.title,
                        "language": track.language,
                    }
                )
        except TypeError as e:
            logger.error(e)
            logger.error("Track data:")
            logger.error(track.to_data())

            raise e

    # file_metadata["raw_mediainfo"] = media_info.to_data()["tracks"]

    return file_metadata


def full_scan(
    directory: str, label: str = None, recreate: bool = False, verbose: bool = False
):
    absolute_path = abspath(directory)
    metadata = {}

    if label:
        metadata["label"] = label

    metadata = {
        **metadata,
        "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "original_directory": absolute_path,
        "directories": [],
        "failed_directories": [],
    }

    logger.info(f"Starting full scan for {absolute_path}")

    # for dir in next(os.walk(directory))[1]:
    for dir in track(
        next(os.walk(directory))[1],
        description="Generating metadata...",
        disable=not verbose,
    ):
        dir_path = os.path.join(absolute_path, dir)
        metadata_file_path = os.path.join(dir_path, _metadata_file_name)

        if not recreate and os.path.isfile(metadata_file_path):
            with open(metadata_file_path, "r") as metadata_file:
                dir_metadata = json.load(metadata_file)
        else:
            dir_metadata = generate(dir_path)

        if dir_metadata:
            metadata["directories"].append(dir_metadata)
        else:
            metadata["failed_directories"].append(dir_path)

    with open("./metadata.json", "w") as metadata_file:
        json.dump(metadata, metadata_file, indent=2, default=str)

    return metadata


def generate(directory: str, label: str = None, verbose: bool = False):
    absolute_path = abspath(directory)
    title = basename(absolute_path)
    score_limit = 2

    logger.info(f"Generating metadata for {absolute_path}")

    if not isdir(absolute_path):
        logger.error(
            f"Directory {absolute_path} does not exists or is not a directory."
        )
        return

    logger.debug("Getting show metadata from Anilist.")

    completed_entries = anilist.getCompletedListByUsername(
        config.get("anilist.username")
    )

    score, entry = min(
        [
            [distance(entry.title.lower(), title.lower()), entry]
            for entry in completed_entries
        ],
        key=lambda x: x[0],
    )

    if score > score_limit:
        logger.error(
            f"Lower score ({score} {entry}) higher that {score_limit} for {title}"
        )
        return None

    anime = anilist.getAnimeById(entry.id)

    metadata = {}

    if label:
        metadata["label"] = label

    metadata = {
        **metadata,
        "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "original_directory": absolute_path,
        "anime": anime.to_dict(),
        "files": [],
    }

    metadata["anime"]["score"] = entry.score
    metadata["anime"]["completedAt"] = entry.completedAt

    for episode in fileManager.getEpisodes(anime, absolute_path):
        logger.debug(f"Scanning episode {episode}.")
        file_path = fileManager.getEpisodePath(anime, episode, absolute_path)
        file_metadata = _get_file_metadata(file_path)
        if file_metadata:
            metadata["files"].append(file_metadata)

    logger.debug("Checing for extra files.")
    scanned_files = [
        os.path.join(absolute_path, f["file_name"]) for f in metadata["files"]
    ]
    extra_files = []
    for root, dirs, files in os.walk(absolute_path):
        for file in files:
            file_path = os.path.join(root, file)
            if file != _metadata_file_name and file_path not in scanned_files:
                extra_files.append(file_path)

    metadata["extra_files"] = extra_files

    with open(os.path.join(absolute_path, _metadata_file_name), "w") as data_file:
        json.dump(metadata, data_file, indent=2, default=str)

    verbose and print(metadata)
    return metadata

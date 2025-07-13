import csv
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
                        "title": track.title,
                        "language": track.language,
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


def _flat_anime_metadata(directory: dict, label: str = None) -> dict:
    anime = directory["anime"]

    anime.pop("titles")
    anime["extra_files"] = "\n".join(directory.get("extra_files", []))
    anime["generation_date"] = directory.get("generation_date")
    anime["original_directory"] = directory.get("original_directory")
    anime["tags"] = "\n".join(
        [f"{tag['name']} ({tag['rank']})" for tag in anime.get("tags", [])]
    )
    anime["spoilerTags"] = "\n".join(
        [f"{tag['name']} ({tag['rank']})" for tag in anime.get("spoilerTags", [])]
    )
    anime["adultTags"] = "\n".join(
        [f"{tag['name']} ({tag['rank']})" for tag in anime.get("adultTags", [])]
    )
    anime["label"] = label or ""

    return anime


def _flat_files_metadata(directory: dict, label: str = None) -> dict:
    anime = directory["anime"]
    files = []

    for file in directory["files"]:
        video = file["video"]
        file["video"] = (
            f"{video.get('format')} | {video.get('codec')} | {video.get('resolution')} | {video.get('aspect_ration')} | {video.get('frame_rate')}"
        )

        if file.get("audio"):
            audio = file["audio"]
            file["audio"] = "\n".join(
                [
                    f"{a.get('title')} ({a.get('language')}) | {a.get('format')} | {a.get('sampling_rate')} | {a.get('compression_mode')}"
                    for a in audio
                ]
            )

        if file.get("subtitles"):
            subtitles = file["subtitles"]
            file["subtitles"] = "\n".join(
                [
                    f"{s.get('title')} ({s.get('language')}) | {s.get('format')}"
                    for s in subtitles
                ]
            )

        file["anime_id"] = anime.get("id")
        file["label"] = label or ""

        files.append(file)

    return files


def _write_metadata_as_csv(inventory: dict, output_dir) -> None:
    label = inventory.get("label")
    generation_date = inventory.get("generation_date")
    anime_file = os.path.join(
        output_dir,
        f"inventory-{label + '-' if label else ''}{generation_date.replace(' ', '_') + '-' if generation_date else ''}anime.csv",
    )
    files_file = os.path.join(
        output_dir,
        f"inventory-{label + '-' if label else ''}{generation_date.replace(' ', '_') + '-' if generation_date else ''}files.csv",
    )
    failed_file = os.path.join(
        output_dir,
        f"inventory-{label + '-' if label else ''}{generation_date.replace(' ', '_') + '-' if generation_date else ''}failed.csv",
    )

    animes = [
        _flat_anime_metadata(directory, label) for directory in inventory["directories"]
    ]
    with open(anime_file, "w", newline="") as f:
        w = csv.DictWriter(f, animes[0].keys())
        w.writeheader()
        w.writerows(animes)

    files = []
    [
        files.extend(_flat_files_metadata(directory, label))
        for directory in inventory["directories"]
    ]
    with open(files_file, "w", newline="") as f:
        w = csv.DictWriter(f, files[0].keys())
        w.writeheader()
        w.writerows(files)

    failed = [
        {"failed_directories": directory}
        for directory in inventory["failed_directories"]
    ]
    with open(failed_file, "w", newline="") as f:
        w = csv.DictWriter(f, failed[0].keys())
        w.writeheader()
        w.writerows(failed)


def compile_inventory(
    directory: str,
    label: str = None,
    output_dir: str = ".",
    format: str = "json",
    recreate: bool = False,
    verbose: bool = False,
):
    absolute_path = abspath(directory)
    inventory = {}

    if label:
        inventory["label"] = label

    inventory = {
        **inventory,
        "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "original_directory": absolute_path,
        "directories": [],
        "failed_directories": [],
    }

    logger.info(f"Starting inventory scan for {absolute_path}")

    # for dir in next(os.walk(directory))[1]:
    for dir in track(
        next(os.walk(directory))[1],
        description="Generating inventory...",
        disable=not verbose,
    ):
        dir_path = os.path.join(absolute_path, dir)
        metadata_file_path = os.path.join(dir_path, _metadata_file_name)

        if not recreate and os.path.isfile(metadata_file_path):
            with open(metadata_file_path, "r") as metadata_file:
                dir_metadata = json.load(metadata_file)
        else:
            dir_metadata = generate_metadata(dir_path)

        if dir_metadata:
            inventory["directories"].append(dir_metadata)
        else:
            inventory["failed_directories"].append(dir_path)

    if format == "json":
        with open(os.path.join(output_dir, "metadata.json"), "w") as metadata_file:
            json.dump(inventory, metadata_file, indent=2, default=str)
    elif format == "csv":
        _write_metadata_as_csv(inventory, output_dir)

    return inventory


def generate_metadata(directory: str, label: str = None, verbose: bool = False):
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
    animes = anilist.searchAnime(title)

    if not animes:
        logger.error(f"No anime found for {title}.")
        return None

    score, anime = min(
        [[distance(anime.title.lower(), title.lower()), anime] for anime in animes],
        key=lambda x: x[0],
    )

    if score > score_limit:
        logger.error(
            f"Lower score ({score} {anime}) higher that {score_limit} for {title}"
        )
        return None

    entry = anilist.getListEntryByAnimeId(config.get("anilist.username"), anime.id)

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

    metadata["anime"]["progress"] = entry.progress if entry else None
    metadata["anime"]["score"] = entry.score if entry else None
    metadata["anime"]["completedAt"] = entry.completedAt if entry else None

    for episode in fileManager.getEpisodes(anime, absolute_path):
        logger.debug(f"Scanning episode {episode}.")
        file_path = fileManager.getEpisodePath(anime, episode, absolute_path)
        file_metadata = _get_file_metadata(file_path)
        if file_metadata:
            metadata["files"].append(file_metadata)

    logger.debug("Checking for extra files.")
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

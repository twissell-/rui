import datetime
import os.path


from core import anilist


def spec(anime_id):
    # TODO: Make this a configuration variable.
    basepath = "/home/damian/dev/notes/00-Inbox"

    media = anilist.getAnimeSpecById(anime_id)
    title = media["title"]["romaji"]

    specdata = get_spec(media)

    with open(os.path.join(basepath, title + ".md"), "w") as specfile:
        specfile.write(specdata)


def get_spec(media):
    roles_to_keep = [
        "Original Character Design",
        "Original Creator",
        "Director",
        "Music",
        "Character Design",
        "Series Composition",
        "Script",
    ]

    relations = ""
    for relation in filter(
        lambda r: r["relationType"] != "ADAPTATION" and r["node"]["type"] == "ANIME",
        media["relations"]["edges"],
    ):
        relations += "   - {relationType}: [[{title}]]\n".format(
            relationType=relation["relationType"],
            title=relation["node"]["title"]["userPreferred"],
        )

    staff = ""
    for person in filter(lambda p: p["role"] in roles_to_keep, media["staff"]["edges"]):
        staff += "   - {role}: [{name}](https://anilist.co/staff/{id})\n".format(
            role=person["role"],
            name=person["node"]["name"]["full"],
            id=person["node"]["id"],
        )

    anime_spec = """Created: {gendate}
Tags: [Anime](Anime)

---
# {romaji}

![conver]({cover})

## Tecnica
- Ingles: {english}
- Estreno: {date}
- Formato: #{format}
- Episodios: {episodes} x {duration}
- Source: #{source}
- Season: #{seasonYear}/{season}
- Staff:
{staff}
- Relations:
{relations}
## Notes

""".format(
        romaji=media["title"]["romaji"],
        english=media["title"]["english"],
        date=datetime.datetime(**media["startDate"]).date(),
        format=media["format"],
        episodes=media["episodes"],
        duration=media["duration"],
        source=media["source"],
        season=media["season"],
        seasonYear=media["seasonYear"],
        cover=media["coverImage"]["extraLarge"],
        relations=relations,
        staff=staff,
        gendate=datetime.datetime.now().strftime("%Y-%m-%-d %T"),
    )

    return anime_spec

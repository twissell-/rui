import datetime
import os.path

import click

from core import anilist

@click.command(help='Creates a spec file for a given anime.')
@click.argument('anime-id')
def spec(anime_id):
    basepath = '/home/damian/personal/test/test/'

    media = anilist.getAnimeSpecById(anime_id)
    title = media['title']['romaji']
    path = os.path.join(basepath, title + '.md')

    click.echo(path)

    specdata = get_spec(media)

    with open(os.path.join(basepath, title + '.md'), 'w') as specfile:
        specfile.write(specdata)

def get_spec(media):
    roles_to_keep = [
        'Original Character Design',
        'Original Creator',
        'Director',
        'Music',
        'Character Design',
        'Series Composition',
        'Script'
    ]
    click.echo(media)
    click.echo(media['staff']['edges'])

    relations = ''
    for relation in filter(
            lambda r: r['relationType'] != 'ADAPTATION' and r['node']['type'] == 'ANIME',
            media['relations']['edges']):
        relations += '   - {relationType}: [[{title}]]\n'.format(
            relationType=relation['relationType'],
            title=relation['node']['title']['romaji']
        )

    staff = ''
    for person in filter(lambda p: p['role'] in roles_to_keep ,media['staff']['edges']):
        staff += '   - {role}: [[{name}]]\n'.format(
            role=person['role'],
            name=person['node']['name']['full']
        )

    anime_spec = '''
## {romaji}

![conver]({cover})

### Specs
- Ingles: {english}
- Estreno: {date} 
- Formato: #{format}
- Episodios: {episodes} x {duration}
- Source: #{source}
- Season: #{season}_{seasonYear}
- Staff:
{staff}
- Relations:
{relations}
### Notes

---
Generated on: {gendate} 
    '''.format(
        romaji=media['title']['romaji'],
        english=media['title']['english'],
        date=datetime.datetime(**media['startDate']).date(),
        format=media['format'],
        episodes=media['episodes'],
        duration=media['duration'],
        source=media['source'],
        season=media['season'],
        seasonYear=media['seasonYear'],
        cover=media['coverImage']['extraLarge'],
        relations=relations,
        staff=staff,
        gendate=datetime.datetime.now().strftime('%Y-%m-%-d %T'),
    )

    return anime_spec

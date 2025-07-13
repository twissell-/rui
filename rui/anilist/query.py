ENDPOINT = "https://graphql.anilist.co"

LIST_BY_USERNAME_AND_STATUS = """
query ($username: String, $status: MediaListStatus) {
  MediaListCollection(userName: $username, type: ANIME, status: $status) {
    lists {
      name
      status
      entries {
        score
        customLists
        media {
          id
          title {
            english
            romaji
            native
            userPreferred
          }
          status
          episodes
          format
          startDate {
            year
          }
          endDate {
            year
          }
        }
        progress
        notes
        completedAt {
          day
          month
          year
        }
      }
    }
  }
}
"""

MEDIA_BY_ID = """
query ($id: Int) {
  Media(id: $id) {
    id
    title {
      romaji
      english
      native
      userPreferred
    }
    startDate {
      year
      month
      day
    }
    endDate {
      year
      month
      day
    }
    format
    episodes
    duration
    season
    seasonYear
    source
    status
    coverImage {
      extraLarge
      color
    }
  }
}
"""

MEDIA_SEARCH = """
query ($search: String, $format_not_in: [MediaFormat]) {
	Page {
    pageInfo {
      hasNextPage
    }
    media(search: $search, format_not_in:$format_not_in) {
      id
      title {
        romaji
        english
        native
        userPreferred
      }
      startDate {
        year
        month
        day
      }
      endDate {
        year
        month
        day
      }
      format
      episodes
      duration
      season
      seasonYear
      source
      status
      coverImage {
        extraLarge
        color
      }
      tags {
        id
        name
        isAdult
        isGeneralSpoiler
        isMediaSpoiler
        rank
      }
    }
  }
}
"""

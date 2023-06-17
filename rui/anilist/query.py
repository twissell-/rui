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
        format
        episodes
        duration
        season
        seasonYear
        source
        coverImage {
            extraLarge
            color
        }
        relations {
            edges {
            id
            relationType
            node {
                id
                type
                title {
                romaji
                userPreferred
                }
            }
            }
        }
        staff {
            edges {
            id
            role
            node {
                id
                name {
                full
                }
            }
            }
        }
        }
    }
"""

COMPLETED_BY_USERNAME_AND_SINCE = """
    query ($username: String, $since: FuzzyDateInt) {
        MediaListCollection(userName: $username, type: ANIME, status: COMPLETED, completedAt_greater: $since) {
        lists {
            name
            status
            entries {
            score(format: POINT_10_DECIMAL)
            media {
                id
                title {
                userPreferred
                }
                siteUrl
            }
            completedAt {
                year
                month
                day
            }
            }
        }
        }
    }
"""

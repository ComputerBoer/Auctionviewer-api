import datetime
import requests
from cache import Cache
from models.location import Auction, Auctionbrand, Countrycode
from utils.helperutils import log

AUCTIVO_GRAPHQL_URL = "https://graphql.auctivo.io/graphql?annoClient=2"
HEADERS = {"Authorization": "bogus"}

PREVIEW_QUERY = """query QueryPublicationPreviewsFrontPage($dateToday: AWSDateTime!, $channel: Channel!, $language: Language!, $numOpenAuctionsRequested: Int!) {
  openNow: queryPublicationPreviews(
    pagination: {itemsPerPage: $numOpenAuctionsRequested, page: 1}
    searchFilter: {
      publicationTypes: [INCREMENTAL_AUCTION, BLIND_AUCTION, DATA_ROOM]
      closingAt: {from: $dateToday}
      channels: [$channel]
      language: $language
    }
    sort: {sortField: CLOSING_ON, direction: ASCENDING}
  ) {
    publications {
      id
      title
      summary
      lotCount
      firstImage {
        url
      }
      __typename
    }
  }
}
"""

DETAILS_QUERY = """query GetIncrementalAuction($incrementalAuctionId: ID!, $language: Language!, $isAdminQuery: Boolean) {
  result: getIncrementalAuction(
    incrementalAuctionId: $incrementalAuctionId
    language: $language
    isAdminQuery: $isAdminQuery
  ) {
    closingOn
    closingAt
    createdOn
    description
    id
    publicationType
    images {
      imageSizes {
        c100
        c500
        __typename
      }
      description
      fileId
      order
      url
      isPublic
      rotation
      __typename
    }
    publishedChannels
    publishedLanguages
    displayLanguage
    visibleOn
    title
    startingOn
    projectId
    publicationNumber
    lastUpdatedOn
    isPublished
    lotCount
    summary
    events {
      retrievalByScheduledDate {
        events {
          id
          forkLiftMaxWeightKilogram
          endingOn
          endingOnLocalTime
          startingOn
          startingOnLocalTime
          forkliftAvailable
          comment
          commentMultiLanguage {
            language
            text
            __typename
          }
          __typename
        }
        address {
          id
          city
          countryCode
          houseNumber
          postalCode
          houseNumberSuffix
          street
          geoLocationUrl
          __typename
        }
        __typename
      }
      retrievalByAppointment {
        events {
          id
          forkLiftMaxWeightKilogram
          endingOn
          endingOnLocalTime
          startingOn
          startingOnLocalTime
          forkliftAvailable
          comment
          commentMultiLanguage {
            language
            text
            __typename
          }
          __typename
        }
        address {
          id
          city
          countryCode
          houseNumber
          postalCode
          houseNumberSuffix
          street
          geoLocationUrl
          __typename
        }
        __typename
      }
      retrievalByDelivery {
        events {
          id
          forkLiftMaxWeightKilogram
          endingOn
          endingOnLocalTime
          startingOn
          startingOnLocalTime
          forkliftAvailable
          comment
          commentMultiLanguage {
            language
            text
            __typename
          }
          __typename
        }
        address {
          id
          city
          countryCode
          houseNumber
          postalCode
          houseNumberSuffix
          street
          geoLocationUrl
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
}
"""

def getAuctivoGraphQLPayload(countrycode: Countrycode = Countrycode.NL, date_today: str = None):
    if date_today is None:
        date_today = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    return {
        "operationName": "QueryPublicationPreviewsFrontPage",
        "variables": {
            "numOpenAuctionsRequested": 100,
            "dateToday": date_today,
            "channel": "auctivo",
            "language": "NL"
        },
        "query": PREVIEW_QUERY
    }

def getAuctivoIncrementalAuctionPayload(incrementalAuctionId: str, language: str = "NL", isAdminQuery: bool = False):
    return {
        "operationName": "GetIncrementalAuction",
        "variables": {
            "incrementalAuctionId": incrementalAuctionId,
            "language": language,
            "isAdminQuery": isAdminQuery
        },
        "query": DETAILS_QUERY
    }

def fetch_auction_details(auction_id: str, language: str = "NL"):
    response = requests.post(
        AUCTIVO_GRAPHQL_URL,
        headers=HEADERS,
        json=getAuctivoIncrementalAuctionPayload(auction_id, language)
    )
    if response.status_code != 200:
        log(f"Auctivo detail GraphQL request failed: {response.status_code}")
        return {}
    return response.json().get("data", {}).get("result", {})

EVENT_TYPES = [
    "retrievalByScheduledDate",
    "retrievalByAppointment",
    "retrievalByDelivery",
]

def extract_event_addresses(publication):
    events = publication.get("events") or {}
    addresses = []

    for name in EVENT_TYPES:
        block = events.get(name)
        if not block:
            continue
        if isinstance(block, dict):
            block = [block]
        for item in block:
            address = item.get("address") or {}
            city = address.get("city")
            if not city:
                continue
            addresses.append({
                "type": name,
                "city": city.strip().lower(),
                "countryCode": address.get("countryCode"),
                "street": address.get("street", ""),
                "houseNumber": address.get("houseNumber", ""),
                "houseNumberSuffix": address.get("houseNumberSuffix", ""),
                "postalCode": address.get("postalCode", ""),
                "geoLocationUrl": address.get("geoLocationUrl", "")
            })

    return addresses

def getAuctivoAuctions(countrycode: Countrycode = Countrycode.NL):
    cachename = f"AuctivoAuctions_{countrycode.name}"
    cached = Cache.get(cachename)
    if cached:
        return cached

    response = requests.post(
        AUCTIVO_GRAPHQL_URL,
        headers=HEADERS,
        json=getAuctivoGraphQLPayload(countrycode)
    )
    if response.status_code != 200:
        log(f"Auctivo GraphQL request failed: {response.status_code}")
        return []

    publications = response.json().get("data", {}).get("openNow", {}).get("publications", [])
    auctions = []

    for pub in publications:
        if pub.get("__typename") != "IncrementalAuctionPreview":
            continue
        
        log(f"retrieving Auctivo detail GraphQL id: {pub["id"]}")

        details = fetch_auction_details(pub["id"], language="NL")
        if not details:
            continue

        addresses = extract_event_addresses(details)
        if not addresses:
            continue

        multiple_locations = len(addresses) > 1
        imageurl = ""
        first_image = pub.get("firstImage")
        if first_image and first_image.get("url"):
            imageurl = first_image["url"]

        for address in addresses:
            address_country = address.get("countryCode") or countrycode.name
            try:
                address_country = Countrycode[address_country.upper()]
            except KeyError:
                address_country = countrycode

            auctions.append(Auction(
                Auctionbrand.AUCT,
                address["city"],
                address_country,
                pub.get("title", ""),
                details.get("startingOn", None),
                details.get("closingOn", None),
                "/auctivo/" + str(pub.get("id", "")),
                imageurl,
                pub.get("lotCount", 0),
                None,
                multiple_locations,
            ))

    Cache.add(cachename, auctions)
    return auctions
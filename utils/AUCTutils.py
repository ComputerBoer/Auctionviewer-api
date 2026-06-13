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

DETAILS_QUERY = """query QueryIncrementalLots($searchFilter: IncrementalLotSearchFilter!, $pagination: Pagination!, $sort: [IncrementalLotSortOrder!]!) {
  queryIncrementalLots(
    pagination: $pagination
    searchFilter: $searchFilter
    sort: $sort
  ) {
    incrementalLots {
      closingOn
      createdOn
      currentBidAmount
      userHasFavorite
      description
      summary
      displayLanguage
      id
      publicationType
      images {
        description
        fileId
        order
        url
        isPublic
        rotation
        __typename
      }
      publicationLotAttributes {
        auctionCosts
        auctionCostsVat
        bpm
        marginRule
        subjectToAcceptance
        vat
        advertise
        __typename
      }
      category {
        externalId
        name
        parentId
        __typename
      }
      documentInfo {
        hasContent
        rootFolderId
        __typename
      }
      navigation {
        nextLotId {
          lotNumber
          externalId
          __typename
        }
        previousLotId {
          externalId
          lotNumber
          __typename
        }
        __typename
      }
      lastUpdatedOn
      lotId
      lotNumber
      publicationNumber
      minimumStartBidAmount
      projectId
      publicationId
      startingOn
      title
      isPublished
      priorityIndex
      totalFavorites
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
          lotOverride
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
          lotOverride
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
          lotOverride
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
        viewingByAppointment {
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
          lotOverride
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
        viewingByScheduledDate {
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
          lotOverride
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
    paginatedPageNumber
    paginatedPageSize
    paginatedTotalResults
    __typename
  }
}"""

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
        "operationName": "QueryIncrementalLots",
        "variables": {
            "searchFilter": {
                "categories": [],
                "language": language,
                "publicationId": incrementalAuctionId,
                "isAdminQuery": isAdminQuery
            },
            "pagination": {"itemsPerPage": 60, "page": 1},
            "sort": {"direction": "ASCENDING", "sortField": "LOT_NUMBER"}
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

    data = response.json().get("data", {}).get("queryIncrementalLots", {})
    lots = data.get("incrementalLots", []) or []
    if not lots:
        return {}

    # pick first lot for top-level fields and collect first available images
    first_lot = lots[0]
    images = []
    for lot in lots:
        imgs = lot.get("images") or []
        if imgs:
            images = imgs
            break

    # aggregate events across lots into lists per event type (keeps shape expected by extract_event_addresses)
    aggregated_events = {}
    for lot in lots:
        events = lot.get("events") or {}
        for name in EVENT_TYPES:
            block = events.get(name)
            if not block:
                continue
            aggregated_events.setdefault(name, []).append(block)

    return {
        "images": images,
        "events": aggregated_events,
        "startingOn": first_lot.get("startingOn"),
        "closingOn": first_lot.get("closingOn")
    }

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

        for parentitem in block:
            item = parentitem
            if isinstance(block, list):
              item = parentitem[0]

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

def get_event_image(details):
    imageurl = ""
    images = details.get("images") or []
    for img in images:
        if not img or not isinstance(img, dict):
            continue
        url = img.get("url")
        if not url:
            image_sizes = img.get("imageSizes") or {}
            url = image_sizes.get("c500") or image_sizes.get("c100")
        if url:
            imageurl = url
            break
    return imageurl

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
        
        id = pub.get("id", None)

        log(f"retrieving Auctivo detail GraphQL id: {id}")

        if id == None:
            continue

        details = fetch_auction_details(id, language="NL")
        if not details:
            continue

        addresses = extract_event_addresses(details)
        if not addresses:
            continue

        multiple_locations = len(addresses) > 1
        imageurl = get_event_image(details)

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
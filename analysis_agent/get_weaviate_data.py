import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Sort, Filter
import json

def get_data(ticker, weaviate_url, weaviate_api_key, verbose=False):
    client = weaviate.connect_to_weaviate_cloud(
        cluster_url=weaviate_url,
        auth_credentials=Auth.api_key(weaviate_api_key),
    )

    news = client.collections.get("News")

    response = news.query.fetch_objects(
        limit=5,
        filters=Filter.by_property("ticker").equal(ticker), 
        sort=[Sort.by_property("time", direction="desc", missing = "last")]
    )
    print(response)
    if not response.objects:
        return None
    data = []
    for obj in response.objects:
        props = obj.properties
        if verbose:
            print(json.dumps(props, indent=2))

    data.append({# update this when weaviate code is complete.
            "timestamp": props.get("timestamp", "no_timestamp"),
            "title": props.get("title", ""),
            "body": props.get("body", "")
        })

    client.close()

    return data
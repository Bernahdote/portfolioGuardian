import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.query import Filter
import os, json

weaviate_url = "v0721jeoraum1hsqk0lcwq.c0.europe-west3.gcp.weaviate.cloud"
weaviate_api_key = "WEx4cFlBd2tGUUt3d2RCRV9JUFJNQXJxdS85MldDS2t1TmNBbVB1L2NFOW9UT25tRVh1MU9LS2V2dnpZPV92MjAw"

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,                                    # Replace with your Weaviate Cloud URL
    auth_credentials=Auth.api_key(weaviate_api_key),             # Replace with your Weaviate Cloud key
)

news = client.collections.get("News")

response = news.query.fetch_objects(
    limit=5,
    filters=Filter.by_property("ticker").equal("NVDA")
)

for obj in response.objects:
    print(json.dumps(obj.properties, indent=2))

client.close()
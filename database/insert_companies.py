import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Property, DataType, Configure
import requests, json, os 

weaviate_url = "v0721jeoraum1hsqk0lcwq.c0.europe-west3.gcp.weaviate.cloud"
weaviate_api_key = "WEx4cFlBd2tGUUt3d2RCRV9JUFJNQXJxdS85MldDS2t1TmNBbVB1L2NFOW9UT25tRVh1MU9LS2V2dnpZPV92MjAw"

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,                                    # Replace with your Weaviate Cloud URL
    auth_credentials=Auth.api_key(weaviate_api_key),             # Replace with your Weaviate Cloud key
)

news = client.collections.get("News")

with news.batch.fixed_size(batch_size=20) as batch:
    batch.add_object({
        "ticker": "AAPL",
        "signal": "Positive", 
        "title": "Apple launches new iPhone",
        "body": "Apple announced the latest version of the iPhone with performance improvements.", 
        "time" : "2025-11-08"
    })

    batch.add_object({
        "ticker": "NVDA",
        "signal": "Positive", 
        "title": "NVIDIA earnings beat expectations",
        "body": "NVIDIA reported strong quarterly earnings driven by demand for AI chips.", 
        "time" : "2025-11-08"
    })

    batch.add_object({
        "ticker": "TSLA",
        "signal": "Negative",
        "title": "Tesla expands production in Berlin",
        "body": "Tesla announced increased capacity for its Berlin Gigafactory.", 
        "time": "2024-10-11"
    })

failed = news.batch.failed_objects
if failed:
    print("❌ Failed inserts:", failed)

client.close()

print("✅ Inserted sample news")
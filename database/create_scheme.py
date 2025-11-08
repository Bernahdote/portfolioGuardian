import os 
import weaviate
from weaviate.classes.init import Auth
from weaviate.classes.config import Property, DataType, Configure

weaviate_url = "https://v0721jeoraum1hsqk0lcwq.c0.europe-west3.gcp.weaviate.cloud"
weaviate_api_key = "WEx4cFlBd2tGUUt3d2RCRV9JUFJNQXJxdS85MldDS2t1TmNBbVB1L2NFOW9UT25tRVh1MU9LS2V2dnpZPV92MjAw"

client = weaviate.connect_to_weaviate_cloud(
    cluster_url=weaviate_url,
    auth_credentials=Auth.api_key(weaviate_api_key),
)

client.collections.create(
    name="News",
    vector_config=Configure.Vectors.text2vec_weaviate(),
    properties=[
        Property(name="ticker", data_type=DataType.TEXT),
        Property(name="signal", data_type = DataType.TEXT), #Positive, Neutral or Negative. 
        Property(name="title", data_type=DataType.TEXT),
        Property(name="body", data_type=DataType.TEXT),
        Property(name="time", data_type=DataType.TEXT),
    ],
)

print("News collection created")

client.close()

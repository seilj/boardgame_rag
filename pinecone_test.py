# Import the Pinecone library
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
import time
from dotenv import load_dotenv
import os
# Pinecone API Key 및 환경 설정
load_dotenv() # .env 파일을 로드
# Initialize a Pinecone client with your API key
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = "example-index"
def create_index():

    if not pc.has_index(index_name):
        pc.create_index(
            name=index_name,
            dimension=1536,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws", 
                region="us-west-1"
            ) 
        ) 

    # Wait for the index to be ready
    while not pc.describe_index(index_name).status['ready']:
        time.sleep(1)


def upsert_vector(data, embeddings, name):
    index = pc.Index(index_name)

    # Prepare the records for upsert
    # Each contains an 'id', the vector 'values', 
    # and the original text and category as 'metadata'
    records = []
    for d, e, f in zip(data, embeddings, name):
        records.append({
            "id": d["id"],
            "values": e,
            "metadata": {
                "source_text": d["text"],
                "name": f,
            }
        })

    # Upsert the records into the index
    index.upsert(
        vectors=records,
        namespace="example-namespace"
    )


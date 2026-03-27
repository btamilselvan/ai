""" ChromaDB search Demo """

import chromadb
from chromadb import Search, K, Knn
import os
from dotenv import load_dotenv

load_dotenv()

chroma_tenant = os.getenv("CHROMA_TENANT")
chroma_database = os.getenv("CHROMA_DATABASE")
chroma_cloud_api_key = os.getenv("CHROMA_CLOUD_API_KEY")

chroma_client = chromadb.CloudClient(tenant=chroma_tenant, database=chroma_database,
                                     api_key=chroma_cloud_api_key)

collection = chroma_client.get_collection(
    "rm_knowledge_collection_1")

message = "tell me about cooking guidelines specific to heating methods"

search = Search().rank(Knn(query=message)).limit(
    limit=5).select(K.ID, K.DOCUMENT, K.SCORE)

results = collection.search(search)

# print(f"results {results}")

print(f"metadata {collection.metadata}")

payloads = zip(results["ids"], results["documents"], results["scores"])

score_threshold = 0.9

for payload in payloads:
    ids, documents, scores = payload
    # print(f"payload {payload}")

    for id, doc, score in zip(ids, documents, scores):
        if score is not None and score <= score_threshold:
            print(f"id: {id}, document: {doc}, score: {score}")

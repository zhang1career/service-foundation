from threading import Lock

from common.components.singleton import Singleton


milvus_lock = Lock()


class LocalMilvusDriver(Singleton):

    def __init__(self, db_path: str):
        # lazy load
        from pymilvus import MilvusClient, model
        # If connection to https://huggingface.co/ failed, uncomment the following path
        # import os
        # os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
        self._client = MilvusClient(db_path)
        self.embedding_fn = model.DefaultEmbeddingFunction()

    def __del__(self):
        self._client.close()

    def create_collection_if_not_exist(self, collection_name: str, dimension: int):
        """
        Create a collection
        """
        if self._client.has_collection(collection_name):
            return
        self._client.create_collection(collection_name, dimension=dimension)
        index_params = self._client.prepare_index_params(field_name="vector", index_type="IVF_FLAT")
        self._client.create_index(collection_name, index_params=index_params)

    def drop_collection(self, collection_name: str):
        """
        Drop a collection
        """
        if not self._client.has_collection(collection_name):
            return
        self._client.drop_collection(collection_name)

    def insert(self, collection_name: str, subject: str, sentence_list: list[str]):
        global milvus_lock
        with milvus_lock:
            # prepare data
            vector_list = self.embedding_fn.encode_documents(sentence_list)

            stat = self._client.get_collection_stats(
                collection_name=collection_name)
            count = stat.get("row_count", 0)

            # Each entity has id, vector representation, raw text, and a subject label that we use
            # to demo metadata filtering later.
            data = [
                {"id": count + i, "vector": vector_list[i], "text": sentence_list[i], "subject": subject}
                for i in range(len(vector_list))
            ]
            # query
            res = self._client.insert(collection_name=collection_name, data=data)
            print(res)

    def search(self,
               collection_name: str,
               subject: str,
               sentence_list: list[str],
               limit: int) -> list[list[dict]]:
        # prepare data
        vector_list = self.embedding_fn.encode_documents(sentence_list)
        # query
        return self._client.search(
            collection_name=collection_name,
            data=vector_list,
            filter="subject=='{sub}'".format(sub=subject),
            limit=limit,
            output_fields=["text", "subject"],
        )

    def query_by_id_batch(self,
                          collection_name: str,
                          id_list: list[int]):
        # query by id
        return self._client.query(
            collection_name=collection_name,
            ids=id_list,
            output_fields=["text", "subject"],
        )

    def delete(self, collection_name: str):
        # delete by id
        res = self._client.delete(
            collection_name=collection_name,
            filter="subject == 'biology'",
        )
        print(res)

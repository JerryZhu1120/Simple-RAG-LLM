import json
from tqdm import tqdm
from concurrent import futures
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter


class TextPreprocesser:
    """
    Preprocess the text before it is inserted into vector database
    """

    def __init__(self, config, openai_key):
        self._config = config["preprocessor"]
        self._embeddings_model = OpenAIEmbeddings(openai_api_key=openai_key, model=self._config["embedding_model"])
        self._embedding_num_workers = self._config["embedding_num_workers"]
        self._embedding_max_retries = self._config["embedding_max_retries"]


    def preprocess(self, company_name_en, text=None, chunk_texts=None):
        """
        Preprocess the text before it is inserted into vector database:
            1. split into chunks
            2. create embeddings for each chunk

        Return:
            list of (embedding, chunk_text)
        """
        if text is None and chunk_texts is None:
            raise Exception("! Error: text and chunk_texts cannot be both None!")
        if chunk_texts is None:
            chunk_texts = self._split_text(text)
        embeddings = self._create_embedding(chunk_texts, company_name_en)
        return embeddings, chunk_texts


    def _split_text(self, text):
        """
        Split the text into chunks
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 1024,
            chunk_overlap  = 128,
            length_function = len,
            add_start_index = True,
        )

        split_texts = text_splitter.create_documents([text])
        return [each.page_content for each in split_texts]


    def _create_embedding(self, chunk_texts, company_name_en):
        """
        Create embeddings for each chunk
        """
        if len(chunk_texts) == 0:
            return []
        chunk_texts = [f"({company_name_en}){chunk_text}" for chunk_text in chunk_texts]

        for k in range(self._embedding_max_retries+1):
            try:
                embeddings = self._embeddings_model.embed_documents(chunk_texts)
                return embeddings
            except Exception as e:
                print(f"! Create embedding failed: {e}, retrying ...")
        
        print(f"After {self._embedding_max_retries} retries, there are still errors")
        raise Exception("! Error: create embeddings failed!")
    

    def create_query_embedding(self, query_text, max_retries):
        """
        Create the embedding for query text
        """
        for _ in range(max_retries+1):
            try:
                return self._embeddings_model.embed_query(query_text)
            except Exception as e:
                print(f"! Create embedding failed: {e}")
        print(f"After {max_retries} retries, there are still errors")
        raise Exception("! Error: create embeddings failed!")
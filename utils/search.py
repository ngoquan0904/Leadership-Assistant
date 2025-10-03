import pysolr
import json
import logging
import re
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
class SolrSearch:
    def __init__(self, core):
        self.solr = pysolr.Solr(f'http://127.0.0.1:8983/solr/{core}', timeout=30)
        logging.info(f"Connected to Solr core: {core}")
        # self.add_chunks(chunk_paths)

    def add_chunks(self, chunk_paths):
        import uuid
        self.delete_all_document()
        for file_path in chunk_paths:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            for chunk in data["chunks"]:
                chunk["task_id"] = str(uuid.uuid4())
            batch_size = 1000
            for i in range(0, len(data["chunks"]), batch_size):
                batch = data["chunks"][i:i+batch_size]
                try:
                    self.solr.add(batch, commit=False)
                except Exception as e:
                    logging.error(f"Failed to add batch: {e}")
            self.solr.commit()
            logging.info(f"Added {len(data['chunks'])} documents from {file_path}")
    
    def delete_all_document(self):
        self.solr.delete(q='*:*')
        logging.info("Deleted all documents in the core.")
    def get_relevant_context(self, query):
        chunks = self.search(query)
        results = ""
        for r in chunks:
            parts = []
            if r.get('heading'):
                parts.append(f"Heading: {r.get('heading')[0]}")
            if r.get('sub_heading_1'):
                parts.append(f"Sub heading 1: {r.get('sub_heading_1')[0]}")
            if r.get('sub_heading_2'):
                parts.append(f"Sub heading 2: {r.get('sub_heading_2')[0]}")
            if r.get('content'):
                parts.append(f"Nội dung: {r.get('content')[0]}")
            if r.get('form_urls', ''):
                parts.append(f"From URLs: {r.get('form_urls')[0]}")
            text = '\n'.join(parts) + '\n\n'
            results += text
        return results
    def clean_query(self, query):
        return query.replace(":", " ").lower()
    
    def search(self, query):
        logging.info(f"Searching with query: {query}")
        try:
            cleaned_query = self.clean_query(query)
            results = self.solr.search(cleaned_query, **{"rows": 15, "start": 0})
        except Exception as e:
            logging.error(f"Failed to search: {e}")
        logging.info(f"Found {len(results)} results.")
        return results
if __name__ == "__main__":
    chunk_paths = [r"D:\Document\Viettel\Agent for SE\chunking\data\input (1).json",
                   r"D:\Document\Viettel\Agent for SE\chunking\data\temp_data_18_9.json",
                   r"D:\Document\Viettel\Agent for SE\full_pipeline\prepare_form_metadata\bieumau.json"]
    solr_search = SolrSearch(core="se_documents")

    query = "4-step modeling process in software development"
    results = solr_search.get_relevant_context(query)
    print(results)
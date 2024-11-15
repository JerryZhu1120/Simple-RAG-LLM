import time
import faiss
import openai
import numpy as np
from openai import OpenAI
from datetime import datetime



class API:
    """
    response to api requests
    """

    def __init__(self, config, vecdb_instance, textdb_instance, openai_key):
        """
        init connections iwth textdb and vecdb
        """
        openai.api_key = openai_key
        self._client = OpenAI(api_key=openai.api_key)
        self._config = config["api"]

        self._vecdb = vecdb_instance
        self._textdb = textdb_instance


    def _verify_input(self, months):
        return_dict = {
            "Status": "Fail",
            "Message": ""
        }
                
        if months != []:
            for month in months:
                if month not in self._textdb.get_months():
                    return_dict["Message"] = f"Months {month} is not valid."
                    return return_dict
            
        return_dict["Status"] = "Success"
        return return_dict
    

    def _specify_filters(self, copyright_ids, company_ids, datatype_ids, months):
        """
        specify filters for vecdb query
        """
        raw_filters = []
        if copyright_ids != []:
            raw_filters.append( " (" + " or ".join([f"copyright == {copyright_id}" for copyright_id in copyright_ids]) + ") " )
        if company_ids != []:
            raw_filters.append( " (" + " or ".join([f"company == {company_id}" for company_id in company_ids]) + ") " )
        if datatype_ids != []:
            raw_filters.append( " (" + " or ".join([f"datatype == {datatype_id}" for datatype_id in datatype_ids]) + ") " )
        if months != []:
            raw_filters.append( " (" + " or ".join([f"month == {month}" for month in months]) + ") " )
        if raw_filters == []:
            return ""
        return " and ".join(raw_filters)


    def batch_embedding_search(self, embeddings, copyright_names, company_windcodes, datatype_names, months, top_k):

        # verify inputs
        return_dict = self._verify_input(months)
        if return_dict["Status"] == "Fail":
            return return_dict
        
        # obtain company ids
        company_ids = []
        for windcode in company_windcodes:
            company_id = self._textdb.get_company_id_by_windcode(windcode)
            if company_id is None:
                return_dict["Status"] = "Fail"
                return_dict["Message"] = f"Company {windcode} cannot be recognized."
                return return_dict
            company_ids.append(company_id)

        # obtain datatype ids
        datatype_ids = []
        try:
            for datatype_name in datatype_names:
                datatype_ids.append(self._textdb.get_datatype_id_by_name(datatype_name))
        except Exception as e:
            return_dict["Status"] = "Fail"
            return_dict["Message"] = e
            return return_dict

        # get copyright ids
        if copyright_names == []:
            copyright_names = self._config["allowed_copyrights"]
        copyright_ids = self._textdb.get_copyright_ids(copyright_names)
        copyright_ids = [each for each in copyright_ids if each != None]
        if (len(copyright_ids) == 0):
            return_dict["Status"] = "Fail"
            return_dict["Message"] = f"All copyrights cannot be recognized."
            return return_dict

        # obtain filters
        query_filter = self._specify_filters(copyright_ids, company_ids, datatype_ids, months)

        # query in vector db 
        try:
            result = self._vecdb.batch_embedding_search(embeddings, top_k, query_filter)
        except Exception as e:
            return_dict["Status"] = "Fail"
            return_dict["Message"] = f"Error when querying vector db: {e}\n- Query filter:{query_filter}"
            return return_dict
        
        # query in text db 
        try:
            result = self._textdb.get_batch_texts(result)
        except Exception as e:
            return_dict["Status"] = "Fail"
            return_dict["Message"] = f"Error when obtaining texts from text db: {e}"
            return return_dict

        return_dict["result"] = result
        return return_dict

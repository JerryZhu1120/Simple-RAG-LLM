# Text Data Schema

#### company

company_id: int64

windcode: string

company_name_en: string

company_name_cn: string

#### document

document_id: int64

document_str_id: string

document_title: string

datatype_id: int64

company_id: int64

date: string

month: int64 (eg, 202310)

text: string

chunk_ids: list of int64

url: string

copyright_id: int64

#### datatype

datatype_id: int64

datatype_name: string (eg, news)

#### chunk

chunk_id: int64

document_str_id: int64

chunk_text: string

embedding: list of float

#### chat

chat_id: string

chat_history: dictionary (i.e., json)

#### copyright

copyright_name: string

copyright_id: int64

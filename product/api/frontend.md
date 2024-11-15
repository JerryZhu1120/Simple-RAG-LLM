# 1系统前端文档管理接口

### 1.1 插入文档

Post请求：

```
http://47.106.252.91:63001/add_documents
```

**json传递数据：**

```json
{
    "documents_data": [
            {
                "document_str_id": xxx,
                "document_title": xxx,
                "datatype": xxx,
                "windcode": xxx,
                "company_name_en": xxx,
                "company_name_cn": xxx,
                "date": xxx,
                "month": xxx,
                "text": xxx,
                "chunk_texts": None,
                "num_workers": 4,
                "url": xxx,
                "copyright": xxx
            },
            ....
        ]
}
```
* documents_data：新上传文档的信息
* 如果用户没有指定windcode，windcode为'unknown', company_name_en为'unknown', company_name_cn为'未知'
* date: each['publishOn'], 示例: '2023-06-21'
* month: int(each['publishOn'][:4]+each['publishOn'][5:7]), 示例: '202306'
* research文件text为None, url为可下载research文件的链接，其他类型文件text需要传内容
* 每次请求document数量不要超过50个，数量太大会报错

**返回示例**

```json
{
    "Message": "",
    "Status": "Success"
}
```

Status为Success表示成功，否则Message这边会给出后端具体报错信息，也就是可能没成功插入。

### 1.2 删除文档

Post请求：

```
http://47.106.252.91:63001/delete_documents
```

**json传递数据：**

```json
{
    "documents_data": [
            {
                "document_str_id": "xxx",
                "copyright": "xxx"
            },
            ....
        ]
}
```
* documents_data：需要删除的文档信息

**返回示例**

```json
{
    "Message": "",
    "Status": "Success"
}
```

Status为Success表示全部删除成功, 如果列表中部分文档的copyright验证出错，会先把验证成功的文档删除，再报错Status为Fail，Message中包含出错文档id列表。

# 2 系统前端查询接口

### 2.1 可限定文档范围的查询

Post请求：

```
http://47.106.252.91:63001/query_with_doc_ids
```

**json传递数据：**

```json
{
    "query_text": "特斯拉这个季度股价表现如何",
    "chat_id": "asd478818959fd6578s88d969",
    "doc_str_ids": ["cicc_xxx", "jf_xxx"],
     // 以下均为optional参数
    "model_names": ["gpt-4", "gpt-4-1106-preview"],
    "top_k": 8,
    "copyrights": ["public", {user_company}, "jpmorgan", ...]
}
```

必传参数：

* query_text：用户输入的对话问题
* chat_id：标明对话id的随机生成的字符串，长为26。如果用户多次查询都在同一个聊天框内，则需要传递同一个chat_id，后端才能获取其之前的记录。
* doc_str_ids：限定范围的文档id列表

可选参数（可不传）:

* model_names：用户指定的总结模型列表，是meta信息获取的模型列表子集，非空。默认值：["gpt-4-1106-preview"]
* top_k：参考的文段个数。默认值：8

检索范围相关参数（可不传）：

* copyrights：用户有权访问的数据范围列表，包括"public"（公开信息）、用户公司名（允许其内部研报）、其购买的版权（如"jpmorgan"等），会使用数据源的copyright字段强制过滤。注意，哪怕提供了doc_str_ids，如果权限范围校验失败，则也不会包含给定的doc_str_ids。因此，如果是对用户上传的文档进行检索，那么这里一定需要包含用户的公司名，允许其访问。默认：["public"]

**返回示例**

```json
"Message": "",
    "Status": "Success",
    "references": [
        {
            "doc_id": "xxx",
            "texts": "一段相关的原文文本",
	    "chunk_ids": [1, 2, 3],
	    "datatype": "research"
        },
        {
            "doc_id": "xxx",
            "texts": "一段相关的原文文本",
	    "chunk_ids": [4],
	    "datatype": "research"
        },
        ...
    ],
    "summaries": [
        {
            "model": "gpt-4",
            "summary": "在这个季度中，特斯拉的股价表现并不好。在第三季度公布财报后，由于公司生产数量以及收益较预期有所下滑，导致股票价格出现大幅下滑。具体来说，特斯拉在本季度的产量从上一季度的479,700辆下降到了430,488辆（参考段落[2]，[3]）。虽然公司在第二季度的表现好于预期，但是在公布第三季度财报之后，股价在一周内下降了近10%并在一周内下降了约15%（参考段落[3]，[8]）。此外，该公司的财报也低于分析师的预期，报告的收入为233.5亿美元，低于预期的247.9亿美元，且每股的收益为0.66美元，低于预期的0.73美元（参考段落[1]，[7]）。总的来说，特斯拉在本季度的股价表现不佳。",
        },
        {
            "model": "gpt-4-1106-preview",
            "summary": "特斯拉在这个季度的股价表现是下跌的。第三季度，该公司的股票在宣布了比分析师预期更差的财务结果后交易量下降。尽管收入同比增加了8.9%，达到了233.5亿美元，但这低于分析师预期的24.79亿美元，并且每股收益也低于分析师的共识估计0.73美元，实际为0.66美元。此外，第三季度财报发布后，股价接近10%的下跌，并在随后的一周结束时下跌了15%，标志着该股票今年最差的周表现（参见[3]段和[7]段和[8]段）。此外，特斯拉在第三季度的车辆生产量下降，这与分析师预期的455,000辆相比也有所减少（参见[2]段和[6]段）。\n\n综上所述，特斯拉本季度的第三季度财报未能满足市场分析师的预期，导致其股价出现明显下滑。在CEO Elon Musk在财报电话会议上对经济表达出悲观的情绪后，分析师们变得更加谨慎，这进一步加剧了市场对股价的担忧（参见[8]段）。",
        }
    ],
```

Status为Success表示成功，否则Message这边会给出后端具体报错信息。

* references：检索出来的文档片段列表，每项中texts为搜索到的相关文段字符串，doc_id表示文档id（注意保持顺序并从1开始标号，对应着总结里面的引用段），chunk_ids为该文档中一或多个文段切片的id列表，datatype表示文档类型
* summaries：总结模型得到的结果列表，每项中model指总结模型，summary表示总结文本

### 2.2 可限定版权范围的查询

Post请求：

```
http://47.106.252.91:63001/query
```

**json传递数据：**

```json
{
    "query_text": "特斯拉这个季度股价表现如何",
    "chat_id": "asd478818959fd6578s88d969",
    // 以下均为optional参数
    "model_names": ["gpt-4", "gpt-4-1106-preview"],
    "auto_filter": true,
    "top_k": 8,
    "copyrights": ["public", {user_company}, "jpmorgan", ...],
    "company_ids": [1, 2],
    "datatype_ids": [1, 2],
    "months": [202311, 202312]
}
```

必传参数：

* query_text：用户输入的对话问题
* chat_id：标明对话id的随机生成的字符串，长为26。如果用户多次查询都在同一个聊天框内，则需要传递同一个chat_id，后端才能获取其之前的记录。

可选参数（可不传）:

* model_names：用户指定的总结模型列表，是meta信息获取的模型列表子集，非空。默认值：["gpt-4-1106-preview"]
* auto_filter：是否由GPT自动指定检索过滤条件。默认值：True
* top_k：参考的文段个数。默认值：8

检索范围相关参数（可不传）：

* copyrights：用户有权访问的数据范围列表，包括"public"（公开信息）、用户公司名（允许其内部研报）、其购买的版权（如"jpmorgan"等），会使用数据源的copyright字段强制过滤。默认：["public"]
* company_ids：公司id列表，是meta信息获取的模型列表中的id子集，如果为空则代表全选所有公司，auto_filter为True时不起作用。默认：[]
* datatype_ids：数据源id列表，是meta信息获取的数据源中的id子集，如果为空则代表全选所有数据源，auto_filter为True时不起作用。默认：[]
* months：检索月份范围列表，是meta信息获取的月份子集，如果为空则代表全选所有月份，auto_filter为True时不起作用。默认：[]

**返回示例**

```json
{
    "Message": "",
    "Status": "Success",
    "references": [
        {
            "doc_id": "xxx",
            "texts": "一段相关的原文文本",
	    "chunk_ids": [1, 2, 3],
	    "datatype": "research"
        },
        {
            "doc_id": "xxx",
            "texts": "一段相关的原文文本",
	    "chunk_ids": [4],
	    "datatype": "news"
        },
        ...
    ],
    "summaries": [
        {
            "model": "gpt-4",
            "summary": "在这个季度中，特斯拉的股价表现并不好。在第三季度公布财报后，由于公司生产数量以及收益较预期有所下滑，导致股票价格出现大幅下滑。具体来说，特斯拉在本季度的产量从上一季度的479,700辆下降到了430,488辆（参考段落[2]，[3]）。虽然公司在第二季度的表现好于预期，但是在公布第三季度财报之后，股价在一周内下降了近10%并在一周内下降了约15%（参考段落[3]，[8]）。此外，该公司的财报也低于分析师的预期，报告的收入为233.5亿美元，低于预期的247.9亿美元，且每股的收益为0.66美元，低于预期的0.73美元（参考段落[1]，[7]）。总的来说，特斯拉在本季度的股价表现不佳。",
        },
        {
            "model": "gpt-4-1106-preview",
            "summary": "特斯拉在这个季度的股价表现是下跌的。第三季度，该公司的股票在宣布了比分析师预期更差的财务结果后交易量下降。尽管收入同比增加了8.9%，达到了233.5亿美元，但这低于分析师预期的24.79亿美元，并且每股收益也低于分析师的共识估计0.73美元，实际为0.66美元。此外，第三季度财报发布后，股价接近10%的下跌，并在随后的一周结束时下跌了15%，标志着该股票今年最差的周表现（参见[3]段和[7]段和[8]段）。此外，特斯拉在第三季度的车辆生产量下降，这与分析师预期的455,000辆相比也有所减少（参见[2]段和[6]段）。\n\n综上所述，特斯拉本季度的第三季度财报未能满足市场分析师的预期，导致其股价出现明显下滑。在CEO Elon Musk在财报电话会议上对经济表达出悲观的情绪后，分析师们变得更加谨慎，这进一步加剧了市场对股价的担忧（参见[8]段）。",
        }
    ],
}
```

Status为Success表示成功，否则Message这边会给出后端具体报错信息。

* references：检索出来的文档片段列表，每项中texts为搜索到的相关文段字符串，doc_id表示文档id（注意保持顺序并从1开始标号，对应着总结里面的引用段），chunk_ids为该文档中一或多个文段切片的id列表，datatype表示文档类型
* summaries：总结模型得到的结果列表，每项中model指总结模型，summary表示总结文本

# 3 开发前端专用

### 3.1 获取后端的Meta信息

Get请求

```
http://47.106.252.91:63001/get_meta
```

用于拉取目前库内的的信息，用于给用户手动指定范围。

**返回示例：**

```json
{
	"Message":"",
	"Status":"Success",
	"company_ids_and_names":[
		{"id":1,"name_cn":"拼多多","name_en":"pinduoduo"},
		{"id":9,"name_cn":"亚马逊","name_en":"amazon"},
		...
		],
	"datatype_ids_and_names":[
		{"id":1,"name":"Research"},
		{"id":2,"name":"News"},
		...
		],
	"model_names":[
		"gpt-3.5-turbo",
		"gpt-4",
		"gpt-4-1106-preview"
		],
	"months":[
		202312,
		202311,
		...
		]
}
```

Status为Success表示成功，否则Message这边会给出后端具体报错信息。

* company_ids_and_names是目前库内已有的公司id和列表
* datatype_ids_and_names是目前库内已有的数据源类型和列表（比如research、news）
* model_names是后端支持的总结模型的列表（比如gpt-3.5-turbo）
* months是库内所有信息发布的月份集合（数字，如202312）

### 3.2 开发人员调试查询

Post请求：

```
http://47.106.252.91:63001/query_full_mode
```

**json传递数据：**

```json
{
    "query_text": "特斯拉这个季度股价表现如何",
    "chat_id": "asd478818959fd6578s88d969",
    "model_names": ["gpt-4", "gpt-4-1106-preview"],
    "auto_filter": true,
    "company_ids": [1, 2],
    "datatype_ids": [1, 2],
    "months": [202311, 202312]
}
```

必传参数：

* query_text：用户输入的对话问题
* chat_id：标明对话id的随机生成的字符串，长为26。如果用户多次查询都在同一个聊天框内，则需要传递同一个chat_id，后端才能获取其之前的记录。必传参数：

可选参数（可不传）:

* model_names：用户指定的总结模型列表，是meta信息获取的模型列表子集，非空。默认值：["gpt-4-1106-preview"]
* auto_filter：是否由GPT自动指定检索过滤条件。默认值：True
* top_k：参考的文段个数。默认值：8

检索范围相关参数（可不传）：

* copyrights：用户有权访问的数据范围列表，包括"public"（公开信息）、用户公司名（允许其内部研报）、其购买的版权（如"jpmorgan"等），会使用数据源的copyright字段强制过滤。默认：["public"]
* company_ids：公司id列表，是meta信息获取的模型列表中的id子集，如果为空则代表全选所有公司，auto_filter为True时不起作用。默认：[]
* datatype_ids：数据源id列表，是meta信息获取的数据源中的id子集，如果为空则代表全选所有数据源，auto_filter为True时不起作用。默认：[]
* months：检索月份范围列表，是meta信息获取的月份子集，如果为空则代表全选所有月份，auto_filter为True时不起作用。默认：[]

**返回示例**

```json
{
    "Message": "",
    "Status": "Success",
    "embedding_time": 0.60286545753479,
    "references": [
        {
            "doc_id": "xxx",
	    "date": "2023-10-09 14:11:50",
            "texts": "Related Link: Here's How Many Vehicles Tesla Has Delivered, Produced In Each Quarter Since 2019 Monday morning, Wells Fargo analyst Colin Langan maintained Tesla with an Equal-Weight rating and lowered the price target from $265 to $260. Tesla is set to report third-quarter financial results after the market closes on Oct. 18. The company is expected to report quarterly earnings of 80 cents per share and revenue of $24.79 billion, according to estimates from Benzinga Pro. TSLA Price Action: Tesla shares were down 2.26% at $254.65 at the time of publication, per Benzinga Pro. Photo: courtesy of Tesla.",
            "title": "Tesla Stock Is Trading Lower: What's Going On?",
	    "url": "http://..."
        },
        {
            "doc_id": "xxx",
            "date": "2023-10-18 15:03:37",
            "texts": "Tesla produced 430,488 vehicles during the third quarter, down from the 479,700 the company produced in the second quarter. The EV giant said the decline in vehicle production was due to factory upgrades. Read more here... Ahead of the event, two analysts weighed in on Tesla stock Monday. Piper Sander maintained an Overweight rating on Tesla and lowered a price target from $300 to $290. Wedbush analyst Daniel Ives reiterated an Outperform rating and maintained a price target of $350. From a technical analysis perspective, Tesla’s stock looks bearish heading into the event, trading in a downtrend and breaking down from a bearish inside bar pattern. It should be noted that holding stocks or options over an earnings print is akin to gambling because stocks can react bullishly to an earnings miss and bearishly to an earnings beat. Traders and Investors looking to play the possible upside in Tesla stock but with diversification may choose to take a position in the AXS 2X Innovation ETF TARK.",
            "title": "Trading Strategies For Tesla Stock Before And After Q3 Earnings"，
            "url": "http://..."
        },
        ...
    ],
    "query_filter": " (company == 5)  and  (month == 202307 or month == 202308 or month == 202309 or month == 202310) ",
    "transformed_query_text": "How has the stock price of Tesla performed this quarter?",
    "search_textdb_time": 0.016914844512939453,
    "search_vecdb_time": 0.048415555549992266,
    "summaries": [
        {
            "model": "gpt-4",
            "summary": "在这个季度中，特斯拉的股价表现并不好。在第三季度公布财报后，由于公司生产数量以及收益较预期有所下滑，导致股票价格出现大幅下滑。具体来说，特斯拉在本季度的产量从上一季度的479,700辆下降到了430,488辆（参考段落[2]，[3]）。虽然公司在第二季度的表现好于预期，但是在公布第三季度财报之后，股价在一周内下降了近10%并在一周内下降了约15%（参考段落[3]，[8]）。此外，该公司的财报也低于分析师的预期，报告的收入为233.5亿美元，低于预期的247.9亿美元，且每股的收益为0.66美元，低于预期的0.73美元（参考段落[1]，[7]）。总的来说，特斯拉在本季度的股价表现不佳。",
            "time": 31.2778103351593
        },
        {
            "model": "gpt-4-1106-preview",
            "summary": "特斯拉在这个季度的股价表现是下跌的。第三季度，该公司的股票在宣布了比分析师预期更差的财务结果后交易量下降。尽管收入同比增加了8.9%，达到了233.5亿美元，但这低于分析师预期的24.79亿美元，并且每股收益也低于分析师的共识估计0.73美元，实际为0.66美元。此外，第三季度财报发布后，股价接近10%的下跌，并在随后的一周结束时下跌了15%，标志着该股票今年最差的周表现（参见[3]段和[7]段和[8]段）。此外，特斯拉在第三季度的车辆生产量下降，这与分析师预期的455,000辆相比也有所减少（参见[2]段和[6]段）。\n\n综上所述，特斯拉本季度的第三季度财报未能满足市场分析师的预期，导致其股价出现明显下滑。在CEO Elon Musk在财报电话会议上对经济表达出悲观的情绪后，分析师们变得更加谨慎，这进一步加剧了市场对股价的担忧（参见[8]段）。",
            "time": 22.414378881454468
        }
    ],
    "transform_time": 9.652528047561646
}
```

Status为Success表示成功，否则Message这边会给出后端具体报错信息。

* transform_time, embedding_time, search_textdb_time, search_vecdb_time：分别代表问题改写与转换时间、查询向量化时间、文本库内检索时间、向量库内检索时间（单位：秒）
* query_filter：GPT自动过滤后得到的过滤器，是个str（这一块只是用于debug校验，不一定要在前端展示）
* transformed_query_text：GPT自动改写后的查询文本，是个str（这一块只是用于debug校验，不一定要在前端展示）
* references：检索出来的文档片段列表，每项中title为其标题，texts表示文段、date表示文档发布日期，url表示文档链接
* summaries：总结模型得到的结果列表，每项中model指总结模型，summary表示总结文本，time表示总结时间（单位：秒）

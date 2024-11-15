### 目录说明

1. data：存放原始数据或临时数据
2. db：存放数据库文件
3. frontend: 前端代码
4. backend.vecdb：支持复杂的filter过滤，使用Milvus DB
5. backend.textdb:  存储各种mapping关系，文本切块和向量化，以及文本和embedding信息的备份
6. backend.respondent：处理用户查询请求
7. backend.document：插入单篇文档
8. data_update：插入更新数据
9. api：对外提供服务api接口

### 运行指导

1. 配置环境requirements.txt
2. 启动milvus向量数据库，参见cyz/milvus文件夹中的README.md
3. cd进backend，server.py，启动后端服务用于接受用户请求
4. cd进data_update，run_data_update.ipynb，用于更新数据

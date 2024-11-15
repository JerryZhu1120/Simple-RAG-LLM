<template>
  <v-app>
    <div>
      <v-card flat>
        <v-card-title>信息智能检索器Demo</v-card-title>
      </v-card>
      <v-tabs
        v-model="requestParams.company_id"
        color="primary"
      >
        <v-tab
          v-for="each in meta_data"
          :key="each.id"
          :value="each.id"
        >
          {{ each.company }}
        </v-tab>
      </v-tabs>
      <v-divider/>

      <v-container>
        <v-card flat class="mt-6">
          <v-card-text>共有{{requestParams.db_ids.length}}个{{meta_data[requestParams.company_id].company}}数据库</v-card-text>
            <v-container>
              <v-row>
                <v-card-subtitle flat
                  v-for="item in meta_data[requestParams.company_id].dbs"
                >{{item.name}}</v-card-subtitle>
              </v-row>
            </v-container>
            <v-card-text>请选择所需总结模型（已选择 {{requestParams.model_ids.length}} 个）</v-card-text>
            <v-container class="my-n6">
              <v-row>
                <v-checkbox
                  v-for="item in models"
                  :key="item.id"
                  v-model="requestParams.model_ids"
                  :label="item.name"
                  :value="item.id"
                ></v-checkbox>
              </v-row>
            </v-container>
        </v-card>
        <v-container>
          <v-text-field v-model="requestParams.query_text" :label="'想在' + meta_data[requestParams.company_id].company + '数据库中查询什么呢？'"></v-text-field>
          <v-btn @click="sendRequest" color="primary" :disabled="isLoading">
            查询
            <v-progress-circular
              v-if="isLoading"
              indeterminate
              size="18"
            ></v-progress-circular>
          </v-btn>
        </v-container>
        <v-card v-if="errorMessage" flat class="my-5">
          <v-card-text>
            出现错误：{{ errorMessage }}
          </v-card-text>
        </v-card>
        <v-card v-for="summary in summaries" :key="summary.model" flat class="my-5">
          <v-card-subtitle>模型: {{ summary.model }}，耗时：{{ summary.time }} s</v-card-subtitle>
          <v-card-text>
            {{ summary.summary }}
          </v-card-text>
        </v-card>
        <v-col v-for="reference in references" :key="reference.ref_id">
            <v-card>
              <v-card-title>[{{ reference.ref_id }}] {{ reference.title }}</v-card-title>
              <v-card-subtitle>id: {{ reference.id }} | publish: {{ reference.publishOn }}</v-card-subtitle>
              <v-card-text>... {{ reference.text }} ...</v-card-text>
              <v-card-actions>
                <v-btn text color="primary" @click="openUrl(reference.url)">
                  查看原文
                </v-btn>
              </v-card-actions>
            </v-card>
        </v-col>
        <v-divider class="my-6" v-if="references.length > 0"/>
        <v-card flat class="mt-6" v-if="references.length > 0">
          <v-card-subtitle>查询向量化: {{ encode_time }} s</v-card-subtitle>
          <v-card-subtitle>向量库搜索: {{ search_time }} s</v-card-subtitle>
          <v-card-subtitle>大模型总结: {{ respond_time }} s</v-card-subtitle>
        </v-card>
      </v-container>
    </div>
  </v-app>
</template>

<script>
import axios from 'axios';
// const meta_url = 'http://localhost:5000/get_meta';
// const query_url = 'http://localhost:5000/query';
const meta_url = 'http://47.106.236.106:63001/get_meta';
const query_url = 'http://47.106.236.106:63001/query';

export default {
  data() {
    return {
      meta_data: [{}],

      requestParams: {
        query_text: '',
        company_id: 0,
        db_ids: [0,1,2,3,4],
        model_ids: [1],
      },
      status: null,
      summaries: null,
      references: [],
      publishOn: null,
      encode_time: null,
      search_time: null,
      respond_time: null,

      errorMessage: null, // Add errorMessage property
      isLoading: false, // Add isLoading property
      models: [
        { id: 0, name: 'GPT-3.5-turbo' },
        { id: 1, name: 'GPT-4' },
      ],
    };
  },

  mounted() {
    axios
      .post(meta_url, {})
      .then(response => {
        this.meta_data = response.data.meta_data;
      })
      .catch(error => {
        console.error(error);
        this.errorMessage = '初始化数据失败，请刷新页面'; 
      });
  },
  
  methods: {
    sendRequest() {
      this.isLoading = true; // Show the loader
      this.errorMessage = null;
      axios
        .post(query_url, this.requestParams)
        .then(response => {
          this.status = response.message;
          this.summaries = response.data.summaries;
          this.references = response.data.references;
          this.publishOn = response.data.publishOn;
          this.encode_time = response.data.encode_time;
          this.search_time = response.data.search_time;
          this.respond_time = response.data.respond_time;
        })
        .catch(error => {
          console.error(error);
          this.errorMessage = 'An error occurred during the query. Please try again or change query.'; 
        })
        .finally(() => {
          this.isLoading = false; // Hide the loader
        });
    },

    openUrl(url) {
      window.open(url, '_blank');
    }
  }
};
</script>
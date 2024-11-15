<template>
  <v-container class="mt-n6">

    <!-- app bar with options -->
    <v-app-bar flat color="primary" density="compact">
      <v-app-bar-title>
        <v-icon icon="mdi-map-search" />
          Chat with Vector Database
      </v-app-bar-title>

      <!-- select options dialog -->
      <v-btn color="white">
        Edit Options
        <v-dialog v-model="option_dialog" activator="parent" class="mx-16">
          <v-card>

            <!-- select GPT models -->
              <v-card-title>GPT models for summary</v-card-title>
              <v-card-subtitle v-if="selected_model_names.length == 0" class="caption">
                If no model selected, only return vector search results without any summary
              </v-card-subtitle>
              <v-card-text>
                <v-select
                  v-model="selected_model_names"
                  :items="model_names"
                  label="Please select"
                  multiple
                  chips
                  small-chips
                  outlined
                  density="compact"
                  dense
                />
              </v-card-text>
            <v-divider/>
            
            <!-- whether to use auto filter -->
            <v-card-title>Auto Query Filter by GPT</v-card-title>
            <v-card-text>
              <v-switch
                v-model="auto_filter"
                hide-details
                color="primary"
                inset
                class="mt-n6"
                :label="auto_filter ? 'Curerntly is Yes, automatically determined by GPT' : 'Currently is No, you can manually select below'"
              ></v-switch>
            </v-card-text>
            <v-divider/>

            <div v-if="auto_filter == false">

              <!-- select company ids -->
              <v-card-title>Target Companys</v-card-title>
              <v-card-subtitle v-if="selected_company_names.length == 0" class="caption">
                If no company selected, all companys are allowed
              </v-card-subtitle>
              <v-card-text>
                <v-select
                  v-model="selected_company_names"
                  :items="company_names"
                  label="Please select"
                  multiple
                  chips
                  small-chips
                  outlined
                  dense
                  density="compact"
                />
              </v-card-text>
              <v-divider/>

              <!-- select datatypes -->
              <v-card-title>Target Data Types</v-card-title>
              <v-card-subtitle v-if="selected_datatype_names.length == 0" class="caption">
                If no datatype selected, all datatypes are allowed
              </v-card-subtitle>
              <v-card-text>
                <v-select
                  v-model="selected_datatype_names"
                  :items="datatype_names"
                  label="Please select"
                  multiple
                  chips
                  small-chips
                  outlined
                  dense
                  density="compact"
                />
              </v-card-text>
              <v-divider/>

              <!-- select months -->
              <v-card-title>Target Times</v-card-title>
              <v-card-subtitle v-if="selected_months.length == 0" class="caption">
                If no times selected, all times are allowed
              </v-card-subtitle>
              <v-card-text>
                <v-select
                  v-model="selected_months"
                  :items="months"
                  label="Please select"
                  multiple
                  chips
                  small-chips
                  outlined
                  dense
                  density="compact"
                />
              </v-card-text>
              <v-divider/>
            </div>

            <v-card-actions>
              <v-btn color="primary" block @click="option_dialog = false">OK</v-btn>
            </v-card-actions>
          </v-card>
        </v-dialog>
      </v-btn>
    </v-app-bar>

    <!-- init error dialog -->
    <v-dialog v-model="init_error_dialog" width="auto" persistent>
      <v-card class="pa-4">
        <v-card-title>Error: Fail to Initialize!</v-card-title>
        <v-card-text>{{ init_error_message }}</v-card-text>
        <v-card-text>Please refresh the page and try again!</v-card-text>
      </v-card>
    </v-dialog>

    <!-- init loading -->
    <v-overlay v-model="init_loading" class="align-center justify-center text-center">
      <v-progress-circular indeterminate size="64" color="primary"></v-progress-circular>
      <v-card-text class="text-h6 text-center" color="primary">Initializing ...</v-card-text>
    </v-overlay>

    <!-- each conversation box -->
    <v-card v-for="message in messages" :key="message.id" class="my-3" flat>
      <v-card-subtitle>{{ message.isBot ? 'Bot' : 'You' }}</v-card-subtitle>
      <v-card :color="message.isBot ? 'grey-lighten-4' : 'blue-lighten-5'">
        
        <!-- error message -->
        <v-card-text class="my-n2" v-if="message.error_message != null" style="color: red">
          {{ message.error_message }}
        </v-card-text>

        <!-- user input text -->
        <v-card-text class="my-n2" v-if="message.text != null">
          {{ message.text }}
        </v-card-text>

        <!-- user options -->
        <v-card-text class="my-n1" v-if="message.options != null && message.options.length != 0">
          <v-card-subtitle class="mt-n5">With options:</v-card-subtitle>
          <v-card-text class="mt-n4 mb-n6 mx-n2">
            <v-chip v-for="(option, option_idx) in message.options" :key="option_idx" class="mb-1 mx-1" density="compact" @click="option_dialog = !option_dialog" color="primary">
              {{ option }}
            </v-chip>
          </v-card-text>
        </v-card-text>

        <!-- summary from GPT -->
        <v-card-text class="my-n2" v-if="message.summaries != null && message.summaries.length != 0">
          <v-tabs v-model="message.activeTab" class="my-n2">
            <v-tab v-for="(summary, summary_idx) in message.summaries" :key="summary_idx" class="text-caption py-n2">{{ summary.model }}</v-tab>
          </v-tabs>
          <v-tab-item v-for="(summary, summary_idx) in message.summaries" :key="summary_idx" :value="summary_idx">
            <v-card-text v-if="message.activeTab === summary_idx" class="mt-n2 mb-n4">{{ summary.summary }}</v-card-text>
          </v-tab-item>
        </v-card-text>
        <v-card-text v-if="message.isBot && (message.summaries == null || message.summaries.length == 0)">
          <v-card-subtitle  class="mt-n2">
            [Warning] Only show vector search results, please select GPT models for summary in the options
          </v-card-subtitle>
        </v-card-text>

        <!-- reference articles -->
        <v-card-text class="my-n2" v-if="message.references != null && message.references.length != 0">
          <v-card-subtitle class="mt-n4">References</v-card-subtitle>
          <v-card-subtitle v-if="message.transformed_query_text != null">- Transformed query: {{message.transformed_query_text}}</v-card-subtitle>
          <v-card-subtitle v-if="message.auto_query_filter != null">- Auto query filter: {{message.auto_query_filter}}</v-card-subtitle>
          <v-expansion-panels>
            <v-expansion-panel 
              v-for="(groupText, reference_idx) in message.references" 
              :key="reference_idx" 
              class="py-n2"
              >
              <v-expansion-panel-title>
                [{{reference_idx+1}}] {{ groupText.title }}
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-row>
                  <v-card-text>... {{ groupText.texts }} ...</v-card-text>
                  <v-card-text>Publish Time: {{ groupText.date }}</v-card-text>
                  <v-btn variant="outlined" color="black" @click="openUrl(groupText.url)">原文链接</v-btn>
                </v-row>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </v-card-text>
        <v-card-text v-if="message.isBot && (message.references == null || message.references.length == 0)">
          <v-card-subtitle class="mt-n4 mb-n2">
            [warning] No reference articles can be found, please modify the filter options
          </v-card-subtitle>
        </v-card-text>

      </v-card>
    </v-card>
    <v-card flat class="my-12"/>

    <!-- input box -->
    <div class="input-container">
      <v-container class="mb-n6">
        <v-row>
            <v-text-field v-model="inputText" label="Type your questions ..." @keyup.enter="sendMessage" :disabled="send_loading" density="compact"></v-text-field>
          <v-btn @click="sendMessage" color="primary" class="mx-4 mt-2" :disabled="send_loading">
            Send
            <v-progress-circular
              v-if="send_loading"
              indeterminate
              size="18"
            ></v-progress-circular>
          </v-btn>
        </v-row>
      </v-container>
    </div>

  </v-container>
</template>

<script>
// const meta_url = 'http://localhost:5000/get_meta';
// const query_url = 'http://localhost:5000/query';
const meta_url = 'http://47.106.252.91:63001/get_meta';
const query_url = 'http://47.106.252.91:63001/query_full_mode';

export default {
  data() {
    return {

      // conversation messages
      messages: [],
      inputText: '',
      chat_id: null,

      // control dialogs
      option_dialog: true,
      init_error_dialog: false,
      init_error_message: null,

      // control loading
      init_loading: true,
      send_loading: false,

      // select summary model names
      model_names: [],
      selected_model_names: ['gpt-4-1106-preview'],

      // select company ids
      company_names: [],
      company_names_to_ids: {},
      selected_company_names: [],

      // select datatypes ids
      datatype_names: [],
      datatype_names_to_ids: {},
      selected_datatype_names: [],

      // select months
      months: [],
      selected_months: [],

      // auto filter
      auto_filter: true,
    };
  },

  created() {
    // generate chat id
    this.chat_id = Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);

    // fetch metadata from backend
    try {
      fetch(meta_url)
        .then(response => response.json())
        .then(data => {
          if (data.Status != 'Success') {
            throw new Error(data.Message);
          }

          // set metadata to component's data properties
          this.model_names = data.model_names;
          this.months = data.months;

          // set company names and ids
          for (var i in data.company_ids_and_names) {
            var each = data.company_ids_and_names[i];
            var name = each['name_en'] + " " + each['name_cn'];
            this.company_names.push(name);
            this.company_names_to_ids[name] = each['id'];
          }
          
          // set datatype names and ids
          for (var i in data.datatype_ids_and_names) {
            var each = data.datatype_ids_and_names[i];
            var name = each['name'];
            this.datatype_names.push(name);
            this.datatype_names_to_ids[name] = each['id'];
          }

          this.init_loading = false;
        })
        .catch(error => {
          this.init_loading = false;
          this.init_error_dialog = true;
          this.init_error_message = error;
        });
    } catch (error) {
      this.init_loading = false;
      this.init_error_dialog = true;
      this.init_error_message = error;
    }
  },

  methods: {
    async sendMessage() {
      this.send_loading = true;

      // process user options
      var options = []
      if (this.selected_model_names.length != 0)
        options.push("Model: " + this.selected_model_names.join(" | "));
      if (this.auto_filter)
        options.push("Use auto query filter by GPT")
      else {
        if (this.selected_company_names.length != 0)
          options.push("Company: " + this.selected_company_names.join(" | "));
        if (this.selected_datatype_names.length != 0)
          options.push("DataType: " + this.selected_datatype_names.join(" | "));
        if (this.selected_months.length != 0)
          options.push("Time: " + this.selected_months.join(" | "));
      }

      // show user input text
      const inputText = this.inputText;
      this.inputText = '';
      this.messages.push({ 
        id: Date.now(), 
        error_message: null,
        text: inputText, 
        options: options,
        summaries: null,
        references: null,
        isBot: false
      });

      try {

        // send request to backend
        const response = await fetch(query_url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            query_text: inputText,
            model_names: this.selected_model_names,
            company_ids: this.selected_company_names.map(name => this.company_names_to_ids[name]),
            datatype_ids: this.selected_datatype_names.map(name => this.datatype_names_to_ids[name]),
            months: this.selected_months,
            chat_id: this.chat_id,
            auto_filter: this.auto_filter,
          })
        });

        // handle response
        const data = await response.json();
        var error_message = null, summaries = null, references = null, transformed_query_text = null, auto_query_filter = null;
        if (response.ok) {
          const status = data.Status;
          if (status == 'Success') {
            summaries = data.summaries;
            references = data.references;
            transformed_query_text = data.transformed_query_text;
            auto_query_filter = data.query_filter;
            
            // log out times
            console.log("transform_time: " + data.transform_time + " s");
            console.log("embedding_time: " + data.embedding_time + " s");
            console.log("search_vecdb_time: " + data.search_vecdb_time + " s");
            console.log("search_textdb_time: " + data.search_textdb_time + " s");
            var each = data.summaries[0];
            console.log(each.model + ": " + each.time + " s");
          } else {
            error_message = "Execution Failed! " + data.Message;
          }
        } else {
          error_message = "Connection Failed! Cannot connect to the server!";
        }

        // show response from backend
        this.messages.push({ 
          id: Date.now() + 1, 
          error_message: error_message,
          summaries: summaries, 
          activeTab: 0,
          references: references,
          transformed_query_text: transformed_query_text,
          auto_query_filter: auto_query_filter,
          text: null,
          options: null,
          isBot: true 
        });
        this.send_loading = false;
      
      // handle error
      } catch (error) {
        this.messages.push({ 
          id: Date.now() + 1, 
          error_message: "Connection Failed! " + error.message,
          text: null,
          summaries: summaries, 
          references: references,
          options: null,
          isBot: true 
        });
        this.send_loading = false;
      }
    },

    openUrl(url) {
      window.open(url, '_blank');
    }
  }
};
</script>

<style scoped>
.input-container {
  position: fixed;
  bottom: 0;
  left: 0;
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 10px;
  background-color: white;
  box-shadow: 0px -2px 6px rgba(0, 0, 0, 0.1);
}
</style>
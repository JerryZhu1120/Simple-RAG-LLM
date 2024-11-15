import time
import openai


class Respondent:
    def __init__(self, openai_key):
        openai.api_key = openai_key
        self.all_models = ["gpt-3.5-turbo", "gpt-4"]
        
    def prompt(self, user_query, search_results):
        """
        Given user query and search results, obtain the summary
        """
        prompt = f"你是一个专业的投资者，阅读过很多文章。现在有人问你：'{user_query}'，你收集了相关资料并需要回答问题。\
                   由于提问中可能涉及类似于上一年、今年、这个月等时间信息，你是在2023年10月回答这个问题，相关资料里面出现的时间需要符合问题表述。\
                   现在，你通过查询相关资料得知以下一些可能相关的段落，每一段首先是一个文段id，接着是具体内容：\n"
        for i, each in enumerate(search_results):
            text = each["chunk_text"]
            prompt += f"【文段{i+1}】. {text}\n"
        prompt += "\n请你使用这些段落回答他的问题，且在回答中引用对应的文段id，格式是：（参考段落[id]）。\n"
        return prompt
    
    def summary(self, prompt, model_ids):
        """
        Provide prompt, obtain summarised results
        """
        
        outputs = []
        for model_id in model_ids:
            if model_id>=0 and model_id<len(self.all_models):
                start_time = time.time()
                model = self.all_models[model_id]
                completion = openai.ChatCompletion.create(model=model, messages=[{"role": "user", "content": prompt}])
                output = completion.choices[0].message.content
                outputs.append({
                    "model": model,
                    "summary": output,
                    "time": time.time() - start_time
                })

        return outputs
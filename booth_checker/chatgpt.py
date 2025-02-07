from openai import OpenAI

class openai_api:
    def __init__(self):
        self.client = OpenAI()

    def chat(self, message):
        messages = list()

        system_role = dict()
        system_role["role"] = "developer"
        system_role["content"] = """파일명, 파일상태값(Added, Deleted, Changed)를 주면 주요 변경점을 간단하게 한국어로 요약해줘"""

        user_role = dict()
        user_role["role"] = "user"
        user_role["content"] = message

        messages.append(system_role)
        messages.append(user_role)

        chatgpt_request = self.client.chat.completions.create(
            model = "gpt-4o-mini",
            messages = messages,
        )
        chatgpt_response = chatgpt_request.choices[0].message.content
        return(chatgpt_response)
from openai import OpenAI

class openai_api:
    def __init__(self):
        self.client = OpenAI()

    def chat(self, message):
        messages = list()

        system_role = dict()
        system_role["role"] = "developer"
        system_role["content"] = """너는 체인지 로그 요약 전문가야. 내가 줄 체인지 로그 내용을 핵심만 간결하게 한국어로 요약해. 그리고 제목 마크다운은 사용하면 안돼"""

        user_role = dict()
        user_role["role"] = "user"
        user_role["content"] = message

        messages.append(system_role)
        messages.append(user_role)

        chatgpt_request = self.client.chat.completions.create(
            model = "gpt-4o-mini",
            messages = messages,
            temperature = 0.2,
        )
        chatgpt_response = chatgpt_request.choices[0].message.content
        return(chatgpt_response)
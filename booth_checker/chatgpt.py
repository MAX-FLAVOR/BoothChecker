from openai import OpenAI

class openai_api:
    def __init__(self):
        self.client = OpenAI()

    def chat(self, message):
        messages = list()

        system_role = dict()
        system_role["role"] = "developer"
        system_role["content"] = """
        너는 파일 리스트 요약 전문가야. 
        내가 주는 리스트는 "{파일명} {Added/Deleted/Changed}" 형식이야.  
        Unity 관련 파일(unitypackage, fbx, prefab)이 포함되어 있다면 해당 파일 변경점을 우선적으로 요약해.
        만약 Unity 관련 파일이 없다면, 다른 파일의 변경점도 1024자 이내의 한국어로 요약해.
        요약할 파일이 적으면 "{파일명} 이 변경되었습니다."로 응답해.
        핵심만 간결하게 요약해서 응답해.
        """

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
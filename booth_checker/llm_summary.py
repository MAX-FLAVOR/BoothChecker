from google import genai
from google.genai import types

class google_gemini_api:
    def __init__(self, gemini_api_key):
        self.sys_instruct="""
            너는 파일 리스트 요약 전문가야. 한국어로 1024자 이내로 요약해.
            내가 주는 리스트는 "{파일명} {Added/Deleted/Changed}" 형식이야.  
            Unity 관련 파일(unitypackage, fbx, prefab)이 포함되어 있다면 해당 파일 변경점을 우선적으로 요약해.
            만약 Unity 관련 파일이 없다면, 다른 파일의 변경점도 요약해.
            요약할 파일이 적으면 "{파일명} 이 변경되었습니다."로 응답해.
            """
        self.client = genai.Client(api_key=gemini_api_key)

    def chat(self, message):
        response = self.client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=self.sys_instruct),
            contents=[message]
        )
        return response.candidates[0].content.parts[0].text
        
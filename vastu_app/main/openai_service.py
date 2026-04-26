# import openai
# from django.conf import settings
#
# openai.api_key = settings.OPENAI_API_KEY
#
# def vastu_ai_response(question):
#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=[
#             {
#                 "role": "system",
#                 "content": "You are a Vastu Shastra expert. Answer clearly and politely."
#             },
#             {
#                 "role": "user",
#                 "content": question
#             }
#         ]
#     )
#
#     return response["choices"][0]["message"]["content"]

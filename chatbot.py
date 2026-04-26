import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("❌ GROQ_API_KEY not found in .env")
    exit()

client = Groq(api_key=api_key)

print("🤖 Vastu AI Chatbot (Streaming Mode)")
print("Type 'quit', 'exit', or 'bye' to stop.\n")

while True:
    user_input = input("You: ")

    if user_input.lower() in ["quit", "exit", "bye"]:
        print("\n🤖 Chatbot: Goodbye!")
        break

    print("🤖 Chatbot: ", end="", flush=True)

    try:
        stream = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional Vastu Shastra consultant. Give clear, practical advice in simple language."
                },
                {
                    "role": "user",
                    "content": user_input
                }
            ],
            stream=True
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)

        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")


# import os
# from dotenv import load_dotenv
# from groq import Groq

# load_dotenv()

# client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# # Print available models
# models = client.models.list()

# print("Available Models:\n")
# for model in models.data:
#     print(model.id)
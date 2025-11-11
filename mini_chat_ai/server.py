from model import get_response

if __name__ == "__main__":
    print("Mini Chat AI Server started. Type 'quit' or 'exit' to stop.")
    while True:
        msg = input("You: ")
        if msg.lower() in ["quit", "exit"]:
            print("Goodbye!")
            break
        print("AI:", get_response(msg))

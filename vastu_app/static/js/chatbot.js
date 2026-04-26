document.addEventListener("DOMContentLoaded", function () {

    const modal = document.getElementById("chat-modal");
    const toggleBtn = document.getElementById("chat-toggle-btn");
    const closeBtn = document.getElementById("close-chat");
    const sendBtn = document.getElementById("chat-send");
    const inputField = document.getElementById("chat-input");
    const messagesArea = document.getElementById("chat-messages");
    /* suggestion button click */
    const suggestionBtns = document.querySelectorAll(".suggestion-btn");
//    /* LOAD CHAT HISTORY */
//    const savedChat = localStorage.getItem("vastu_chat_history");
//
//    if(savedChat){
//        messagesArea.innerHTML = savedChat;
//    }
//
//    if(savedChat){
//
//    messagesArea.innerHTML = savedChat;
//
//    const welcome = document.getElementById("chat-welcome");
//
//        if(welcome){
//            welcome.style.display = "none";
//        }
//
//    }

    suggestionBtns.forEach(btn => {

        btn.addEventListener("click", () => {

            const prompt = btn.getAttribute("data-prompt");

            document.getElementById("chat-welcome").style.display = "none";

            inputField.value = prompt;

            sendMessage();

        });

    });

    toggleBtn.addEventListener("click", () => {
        modal.style.display = "flex";
    });

    closeBtn.addEventListener("click", () => {
        modal.style.display = "none";
    });

    function appendMessage(text, sender) {
        const messageDiv = document.createElement("div");
        messageDiv.classList.add("message", sender);
        messageDiv.innerText = text;
        messagesArea.appendChild(messageDiv);
        messagesArea.scrollTo({top: messagesArea.scrollHeight,behavior: "smooth"});
        localStorage.setItem("vastu_chat_history", messagesArea.innerHTML);
    }

    async function sendMessage() {
        const message = inputField.value.trim();
        const welcome = document.getElementById("chat-welcome");
        if(welcome){
            welcome.style.display="none";
        }
        if (!message) return;

        appendMessage(message, "user");
        inputField.value = "";

        appendMessage("Typing...", "bot");

        try {
            const response = await fetch("/api/chat/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ message: message }),
            });

            const data = await response.json();

            messagesArea.lastChild.remove(); // remove typing

            if (response.ok) {
                appendMessage(data.reply, "bot");
            } else {
                appendMessage("Error: " + (data.error || "Something went wrong"), "bot");
            }

        } catch (error) {
            messagesArea.lastChild.remove();
            appendMessage("Server not responding.", "bot");
        }
    }

    sendBtn.addEventListener("click", sendMessage);

    inputField.addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
            sendMessage();
        }
    });

});
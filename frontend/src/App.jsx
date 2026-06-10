import { useState, useRef, useEffect } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploadedFile, setUploadedFile] = useState("");

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! Ask me anything 🚀 Upload a PDF and I can answer questions about it.",
    },
  ]);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages]);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];

    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      alert("Please upload a PDF file.");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      await axios.post(
        "http://127.0.0.1:8000/upload",
        formData
      );

      setUploadedFile(file.name);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `📄 Document uploaded successfully: ${file.name}`,
        },
      ]);
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "❌ PDF upload failed.",
        },
      ]);
    }
  };

  const newChat = () => {
    setMessages([
      {
        role: "assistant",
        content:
          "Hello! Ask me anything 🚀 Upload a PDF and I can answer questions about it.",
      },
    ]);

    setInput("");
    setUploadedFile("");
  };

  const generate = async () => {
    if (!input.trim()) return;

    const currentInput = input.trim();

    const userMessage = {
      role: "user",
      content: currentInput,
    };

    const updatedMessages = [...messages, userMessage];

    const imageKeywords = [
      "generate image",
      "create image",
      "draw",
      "make an image",
      "create a picture",
      "generate a picture",
      "create artwork",
      "make a drawing",
      "image of",
      "picture of",
      "generate a photo",
      "create a photo",
    ];

    const isImageRequest = imageKeywords.some((keyword) =>
      currentInput.toLowerCase().includes(keyword)
    );

    setMessages(updatedMessages);
    setInput("");

    try {
      setLoading(true);

      let response;

      if (isImageRequest) {
        response = await axios.post(
          "http://127.0.0.1:8000/generate-image",
          {
            prompt: currentInput,
          }
        );

        if (response.data.error) {
          throw new Error(response.data.error);
        }

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            image: response.data.image,
          },
        ]);
      } else {
        response = await axios.post(
          "http://127.0.0.1:8000/generate",
          {
            messages: updatedMessages,
          }
        );

        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              response.data.output ||
              "No response received.",
          },
        ]);
      }
    } catch (error) {
      console.error(error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content:
            error?.message ||
            "❌ Failed to connect to backend.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      generate();
    }
  };

  return (
    <div className="app">
      <div className="sidebar">
        <h2>🤖 AI</h2>

        <button
          className="new-chat"
          onClick={newChat}
        >
          + New Chat
        </button>

        <div className="file-box">
          <h3>📄 Document</h3>

          {uploadedFile ? (
            <p>{uploadedFile}</p>
          ) : (
            <p>No document uploaded</p>
          )}
        </div>

        <label className="upload-btn">
          Upload PDF

          <input
            type="file"
            accept=".pdf"
            onChange={handleFileUpload}
            hidden
          />
        </label>
      </div>

      <div className="main">
        <div className="header">
          <h1>🤖 AI Assistant</h1>
          <p>Powered by Qwen + FastAPI + RAG</p>
        </div>

        <div className="chat-container">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`message ${msg.role}`}
            >
              {msg.content && (
                <div>{msg.content}</div>
              )}

              {msg.image && (
                <img
                  src={`data:image/png;base64,${msg.image}`}
                  alt="Generated"
                  className="generated-image"
                />
              )}
            </div>
          ))}

          {loading && (
            <div className="message assistant">
              🤖 Thinking...
            </div>
          )}

          <div ref={messagesEndRef}></div>
        </div>

        <div className="input-area">
          <textarea
            placeholder="Ask something..."
            value={input}
            onChange={(e) =>
              setInput(e.target.value)
            }
            onKeyDown={handleKeyDown}
          />

          <button
            className="send-btn"
            onClick={generate}
            disabled={loading}
          >
            ➤
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
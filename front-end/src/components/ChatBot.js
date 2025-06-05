import React, { useState, useRef, useEffect } from "react";
import MessageBubble from "./MessageBubble";
import "./ChatBotModern.css";

// Accepts: chatHistory, setChatHistory (from App)
const ChatBot = ({ chatHistory, setChatHistory }) => {
  const [input, setInput] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | error
  const [error, setError] = useState(null);
  const [isTyping, setIsTyping] = useState(false);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory, status, isTyping]);

  // Only show "Typing.." in chat area while user is typing (do not add input to chatHistory)
  useEffect(() => {
    setIsTyping(!!input);
  }, [input]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    setStatus("loading");
    setError(null);
    setIsTyping(false);

    setChatHistory([
      ...chatHistory,
      { sender: "user", text: input }
    ]);

    try {
      // Simulate API call
      const response = await fetch("http://localhost:5000/llm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input })
      });
      const data = await response.json();
      setChatHistory([
        ...chatHistory,
        { sender: "user", text: input },
        { sender: "bot", text: data.reply }
      ]);
      setInput("");
      setStatus("idle");
    } catch (err) {
      setError("Failed to get response from server.");
      setStatus("error");
    }
  };

  return (
    <div className="modern-chat-area">
      <div className="modern-chat-scroll">
        {chatHistory.map((msg, idx) => (
          <MessageBubble key={idx} sender={msg.sender} text={msg.text} />
        ))}
        {(isTyping || status === "loading") && (
          <div className="d-flex justify-content-end mb-2">
            <div className="modern-typing-indicator">Typing<span className="modern-typing-dots">...</span></div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>
      <form onSubmit={handleSend} className="modern-chat-inputbar">
        <input
          className="form-control modern-chat-input"
          type="text"
          placeholder="Type your message…"
          value={input}
          onChange={e => setInput(e.target.value)}
          autoFocus
        />
        <button
          className="btn modern-send-btn"
          type="submit"
          disabled={status === "loading" || !input.trim()}
          aria-label="Send"
        >
          <svg width={22} height={22} fill="currentColor" viewBox="0 0 20 20">
            <path d="M2.94 2.94a.75.75 0 0 1 .79-.18l13 5a.75.75 0 0 1 0 1.38l-13 5a.75.75 0 0 1-.97-.97l2.45-6.53-2.45-6.54a.75.75 0 0 1 .18-.79z"/>
          </svg>
        </button>
      </form>
      {error && (
        <div className="text-danger text-center py-2">{error}</div>
      )}
    </div>
  );
};

export default ChatBot;
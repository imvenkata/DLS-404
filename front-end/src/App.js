import React, { useState } from "react";
import ChatBot from "./components/ChatBot";
import "bootstrap/dist/css/bootstrap.min.css";
import "./AppModern.css";

function App() {
  // Each chat has {id, history: [...]}
  const [chats, setChats] = useState([
    { id: Date.now(), history: [] }
  ]);
  const [activeChatId, setActiveChatId] = useState(chats[0].id);

  const createNewChat = () => {
    const newChat = { id: Date.now(), history: [] };
    setChats([newChat, ...chats]);
    setActiveChatId(newChat.id);
  };

  const updateChatHistory = (chatId, newHistory) => {
    setChats(prev =>
      prev.map(chat =>
        chat.id === chatId ? { ...chat, history: newHistory } : chat
      )
    );
  };

  return (
    <div className="modern-bg min-vh-100">
      {/* Section 1: Centered Heading and Subheading */}
      <section className="modern-header py-4 mb-2">
        <div className="text-center">
          <h2 className="fw-bold mb-1 modern-title">
            Knowledge Assistant
          </h2>
          <div className="modern-subtitle">
            AI Powered Knowledge Companion
          </div>
        </div>
      </section>
      {/* Section 2: Chat History Sidebar + Chat Area */}
      <section className="container modern-section">
        <div className="modern-section-content">
          <div className="modern-sidebar-col">
            <div className="d-flex flex-column h-100 modern-sidebar">
              <div className="mb-3 px-2">
                <button
                  className="btn modern-newchat w-100"
                  onClick={createNewChat}
                >
                  + New Chat
                </button>
              </div>
              <div className="flex-grow-1 overflow-auto pb-3 modern-sidebar-scroll">
                {chats.map(chat => (
                  <button
                    key={chat.id}
                    className={`modern-chat-tile w-100 text-start mb-3 px-3 py-2 ${
                      activeChatId === chat.id
                        ? "modern-chat-tile-active"
                        : ""
                    }`}
                    onClick={() => setActiveChatId(chat.id)}
                  >
                    <span className="modern-chat-tile-title">
                      {chat.history.length > 0
                        ? chat.history.find(m => m.sender === "user")?.text.slice(0, 30) + "..."
                        : "New Chat"}
                    </span>
                    <span className="modern-chat-tile-date">
                      {new Date(chat.id).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="modern-chat-col">
            <ChatBot
              key={activeChatId}
              chatHistory={chats.find(chat => chat.id === activeChatId)?.history || []}
              setChatHistory={history => updateChatHistory(activeChatId, history)}
            />
          </div>
        </div>
      </section>
    </div>
  );
}

export default App;
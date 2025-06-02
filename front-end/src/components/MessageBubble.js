import React from "react";
import "./MessageBubbleModern.css";

// User messages right aligned, bot messages left aligned.
const MessageBubble = ({ sender, text }) => (
  <div
    className={`d-flex ${
      sender === "user" ? "justify-content-end" : "justify-content-start"
    } mb-2`}
  >
    <div
      className={`${
        sender === "user"
          ? "modern-bubble-user"
          : "modern-bubble-bot"
      }`}
    >
      {text}
    </div>
  </div>
);

export default MessageBubble;
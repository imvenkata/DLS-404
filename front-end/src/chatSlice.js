import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

// Simulate LLM API call for demo; replace with real API in production.
export const sendMessage = createAsyncThunk(
  'chat/sendMessage',
  async (userMessage) => {
    // Replace this with your LLM API endpoint
    const response = await fetch('http://127.0.0.1:5000/llm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userMessage }),
    });
    const data = await response.json();
    // Assume API returns: { reply: "LLM response here" }
    return data.reply || "Sorry, I couldn't get a response.";
  }
);

const chatSlice = createSlice({
  name: 'chat',
  initialState: {
    history: [], // { sender: 'user' | 'bot', text: string }
    status: 'idle',
    error: null,
  },
  reducers: {
    addUserMessage: (state, action) => {
      state.history.push({ sender: 'user', text: action.payload });
    },
    addBotMessage: (state, action) => {
      state.history.push({ sender: 'bot', text: action.payload });
    },
    clearChat: (state) => {
      state.history = [];
      state.status = 'idle';
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.history.push({ sender: 'bot', text: action.payload });
        state.status = 'idle';
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.status = 'failed';
        state.error = 'Failed to get response from LLM.';
      });
  },
});

export const { addUserMessage, addBotMessage, clearChat } = chatSlice.actions;
export default chatSlice.reducer;
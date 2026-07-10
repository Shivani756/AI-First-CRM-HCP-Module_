import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { chatWithAgent } from '../services/api';

const INITIAL_HINT =
  'Log interaction details here (e.g., "Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure") or ask for help.';

const initialState = {
  messages: [{ role: 'assistant', content: INITIAL_HINT }],
  loading: false,
  error: null,
  sessionId: `session_${Date.now()}`,
  lastExtractedFields: null,
  lastInteractionId: null,
};

export const sendMessage = createAsyncThunk(
  'agent/sendMessage',
  async ({ message, sessionId }, { rejectWithValue }) => {
    try {
      const response = await chatWithAgent({ message, session_id: sessionId });
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to reach the AI agent.');
    }
  }
);

const agentSlice = createSlice({
  name: 'agent',
  initialState,
  reducers: {
    clearChat(state) {
      state.messages = [{ role: 'assistant', content: INITIAL_HINT }];
      state.lastExtractedFields = null;
      state.lastInteractionId = null;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state, action) => {
        state.loading = true;
        state.error = null;
        state.messages.push({ role: 'user', content: action.meta.arg.message });
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.loading = false;
        state.messages.push({ role: 'assistant', content: action.payload.reply });
        state.lastExtractedFields = action.payload.extracted_fields ?? null;
        state.lastInteractionId = action.payload.interaction_id ?? null;
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
        state.messages.push({
          role: 'assistant',
          content: `⚠ ${action.payload || 'Something went wrong. Please try again.'}`,
        });
      });
  },
});

export const { clearChat } = agentSlice.actions;
export default agentSlice.reducer;

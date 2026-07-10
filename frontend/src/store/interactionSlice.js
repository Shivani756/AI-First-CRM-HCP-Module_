import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { createInteraction, updateInteraction } from '../services/api';

const today = new Date().toISOString().split('T')[0];
const nowTime = new Date().toTimeString().slice(0, 5);

const initialFormState = {
  hcp_name: '',
  hcp_id: null,
  interaction_type: 'Meeting',
  date: today,
  time: nowTime,
  attendees: '',
  topics_discussed: '',
  materials_shared: [],
  samples_distributed: [],
  sentiment: 'Neutral',
  outcomes: '',
  follow_up_actions: '',
  ai_summary: '',
  ai_suggested_followups: [],
};

const initialState = {
  form: { ...initialFormState },
  submitting: false,
  submitSuccess: false,
  submitError: null,
  currentInteractionId: null,
};

export const submitInteraction = createAsyncThunk(
  'interaction/submit',
  async (formData, { rejectWithValue }) => {
    try {
      const response = await createInteraction(formData);
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to save interaction.');
    }
  }
);

export const saveInteractionUpdate = createAsyncThunk(
  'interaction/update',
  async ({ id, data }, { rejectWithValue }) => {
    try {
      const response = await updateInteraction(id, data);
      return response.data;
    } catch (err) {
      return rejectWithValue(err.response?.data?.detail || 'Failed to update interaction.');
    }
  }
);

const interactionSlice = createSlice({
  name: 'interaction',
  initialState,
  reducers: {
    updateField(state, action) {
      const { field, value } = action.payload;
      state.form[field] = value;
    },
    patchForm(state, action) {
      // Merge extracted AI fields into the form; only overwrite if value is non-empty
      const fields = action.payload;
      Object.keys(fields).forEach((key) => {
        if (key in state.form && fields[key] !== undefined && fields[key] !== null && fields[key] !== '') {
          state.form[key] = fields[key];
        }
      });
    },
    setAISuggestedFollowups(state, action) {
      state.form.ai_suggested_followups = action.payload;
    },
    setCurrentInteractionId(state, action) {
      state.currentInteractionId = action.payload;
    },
    clearSubmitStatus(state) {
      state.submitSuccess = false;
      state.submitError = null;
    },
    resetForm(state) {
      state.form = { ...initialFormState, date: new Date().toISOString().split('T')[0] };
      state.submitting = false;
      state.submitSuccess = false;
      state.submitError = null;
      state.currentInteractionId = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(submitInteraction.pending, (state) => {
        state.submitting = true;
        state.submitSuccess = false;
        state.submitError = null;
      })
      .addCase(submitInteraction.fulfilled, (state, action) => {
        state.submitting = false;
        state.submitSuccess = true;
        state.currentInteractionId = action.payload.id;
      })
      .addCase(submitInteraction.rejected, (state, action) => {
        state.submitting = false;
        state.submitError = action.payload;
      })
      .addCase(saveInteractionUpdate.fulfilled, (state, action) => {
        state.currentInteractionId = action.payload.id;
      });
  },
});

export const {
  updateField,
  patchForm,
  setAISuggestedFollowups,
  setCurrentInteractionId,
  clearSubmitStatus,
  resetForm,
} = interactionSlice.actions;

export default interactionSlice.reducer;

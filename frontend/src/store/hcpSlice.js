import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { searchHCPs } from '../services/api';

const initialState = {
  hcps: [],
  loading: false,
  error: null,
  selectedHCP: null,
};

export const fetchHCPs = createAsyncThunk('hcp/fetch', async (query = '', { rejectWithValue }) => {
  try {
    const response = await searchHCPs(query);
    return response.data;
  } catch (err) {
    return rejectWithValue(err.response?.data?.detail || 'Failed to fetch HCPs.');
  }
});

const hcpSlice = createSlice({
  name: 'hcp',
  initialState,
  reducers: {
    selectHCP(state, action) {
      state.selectedHCP = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchHCPs.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchHCPs.fulfilled, (state, action) => {
        state.loading = false;
        state.hcps = action.payload;
      })
      .addCase(fetchHCPs.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { selectHCP } = hcpSlice.actions;
export default hcpSlice.reducer;

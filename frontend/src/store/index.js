import { configureStore } from '@reduxjs/toolkit';
import interactionReducer from './interactionSlice';
import agentReducer from './agentSlice';
import hcpReducer from './hcpSlice';

export const store = configureStore({
  reducer: {
    interaction: interactionReducer,
    agent: agentReducer,
    hcp: hcpReducer,
  },
});

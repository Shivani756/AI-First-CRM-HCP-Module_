import React, { useState, useCallback, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import AsyncSelect from 'react-select/async';
import {
  updateField,
  submitInteraction,
  resetForm,
  clearSubmitStatus,
} from '../../store/interactionSlice';
import { fetchHCPs } from '../../store/hcpSlice';
import { searchMaterials } from '../../services/api';
import './LogInteractionForm.css';

const INTERACTION_TYPES = [
  'Meeting',
  'Phone Call',
  'Email',
  'Virtual Meeting',
  'In-Clinic Visit',
  'Conference',
  'Webinar',
];

const HCP_SELECT_STYLES = {
  control: (base, state) => ({
    ...base,
    borderColor: state.isFocused ? '#2563eb' : '#d1d5db',
    borderRadius: '6px',
    minHeight: '36px',
    boxShadow: state.isFocused ? '0 0 0 3px rgba(37,99,235,0.15)' : 'none',
    fontFamily: 'Inter, sans-serif',
    fontSize: '13px',
    '&:hover': { borderColor: '#9ca3af' },
  }),
  option: (base, state) => ({
    ...base,
    fontSize: '13px',
    backgroundColor: state.isSelected ? '#2563eb' : state.isFocused ? '#eff6ff' : 'white',
    color: state.isSelected ? 'white' : '#111827',
    padding: '8px 12px',
  }),
  placeholder: (base) => ({ ...base, color: '#9ca3af', fontSize: '13px' }),
  singleValue: (base) => ({ ...base, fontSize: '13px' }),
};

export default function LogInteractionForm() {
  const dispatch = useDispatch();
  const { form, submitting, submitSuccess, submitError, currentInteractionId } = useSelector(
    (s) => s.interaction
  );

  // Materials modal state
  const [showMatSearch, setShowMatSearch] = useState(false);
  const [matQuery, setMatQuery] = useState('');
  const [matResults, setMatResults] = useState([]);
  const [sampleInput, setSampleInput] = useState('');

  // Auto-clear success banner after 4 s
  useEffect(() => {
    if (submitSuccess) {
      const t = setTimeout(() => dispatch(clearSubmitStatus()), 4000);
      return () => clearTimeout(t);
    }
  }, [submitSuccess, dispatch]);

  // ── HCP async search ──────────────────────────────────────
  const loadHCPOptions = useCallback(
    (inputValue, callback) => {
      dispatch(fetchHCPs(inputValue)).then((action) => {
        if (action.payload) {
          callback(action.payload.map((h) => ({ value: h.id, label: h.name, hcp: h })));
        }
      });
    },
    [dispatch]
  );

  const handleHCPChange = (option) => {
    dispatch(updateField({ field: 'hcp_name', value: option?.label ?? '' }));
    dispatch(updateField({ field: 'hcp_id', value: option?.value ?? null }));
  };

  const handleChange = (field) => (e) => dispatch(updateField({ field, value: e.target.value }));

  // ── Materials ─────────────────────────────────────────────
  const handleSearchMaterials = async () => {
    try {
      const res = await searchMaterials(matQuery);
      setMatResults(res.data);
    } catch {
      setMatResults([]);
    }
  };

  const addMaterial = (mat) => {
    if (!form.materials_shared.find((m) => m.id === mat.id)) {
      dispatch(updateField({ field: 'materials_shared', value: [...form.materials_shared, mat] }));
    }
    setShowMatSearch(false);
    setMatQuery('');
    setMatResults([]);
  };

  const removeMaterial = (id) =>
    dispatch(updateField({ field: 'materials_shared', value: form.materials_shared.filter((m) => m.id !== id) }));

  // ── Samples ───────────────────────────────────────────────
  const addSample = () => {
    if (sampleInput.trim()) {
      dispatch(
        updateField({
          field: 'samples_distributed',
          value: [...form.samples_distributed, { id: Date.now(), name: sampleInput.trim() }],
        })
      );
      setSampleInput('');
    }
  };

  const removeSample = (id) =>
    dispatch(updateField({ field: 'samples_distributed', value: form.samples_distributed.filter((s) => s.id !== id) }));

  // ── Submit ────────────────────────────────────────────────
  const handleSubmit = (e) => {
    e.preventDefault();
    dispatch(submitInteraction(form));
  };

  return (
    <div className="lf-container">
      <div className="lf-section-header">Interaction Details</div>

      <form onSubmit={handleSubmit} className="lf-form">
        {/* ── Row 1: HCP Name + Interaction Type ── */}
        <div className="lf-row two-col">
          <div className="lf-group">
            <label className="lf-label">HCP Name</label>
            <AsyncSelect
              cacheOptions
              defaultOptions
              loadOptions={loadHCPOptions}
              onChange={handleHCPChange}
              placeholder="Search or select HCP..."
              isClearable
              styles={HCP_SELECT_STYLES}
            />
          </div>
          <div className="lf-group">
            <label className="lf-label">Interaction Type</label>
            <select
              value={form.interaction_type}
              onChange={handleChange('interaction_type')}
              className="lf-select"
            >
              {INTERACTION_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </div>
        </div>

        {/* ── Row 2: Date + Time ── */}
        <div className="lf-row two-col">
          <div className="lf-group">
            <label className="lf-label">Date</label>
            <input type="date" value={form.date} onChange={handleChange('date')} className="lf-input" />
          </div>
          <div className="lf-group">
            <label className="lf-label">Time</label>
            <input type="time" value={form.time} onChange={handleChange('time')} className="lf-input" />
          </div>
        </div>

        {/* ── Attendees ── */}
        <div className="lf-group full">
          <label className="lf-label">Attendees</label>
          <input
            type="text"
            value={form.attendees}
            onChange={handleChange('attendees')}
            placeholder="Enter names or search..."
            className="lf-input"
          />
        </div>

        {/* ── Topics Discussed ── */}
        <div className="lf-group full">
          <label className="lf-label">Topics Discussed</label>
          <div className="lf-textarea-wrap">
            <textarea
              value={form.topics_discussed}
              onChange={handleChange('topics_discussed')}
              placeholder="Enter key discussion points..."
              className="lf-textarea"
              rows={4}
            />
            <span className="lf-ai-icon" title="AI-enhanced field">✦</span>
          </div>
          <button type="button" className="lf-voice-btn">
            🎙 Summarize from Voice Note{' '}
            <span className="lf-consent">(Requires Consent)</span>
          </button>
        </div>

        {/* ── Materials Shared ── */}
        <div className="lf-group full">
          <div className="lf-subsection-header">
            <span className="lf-label">Materials Shared</span>
            <button type="button" className="lf-add-btn" onClick={() => setShowMatSearch((v) => !v)}>
              🔍 Search/Add
            </button>
          </div>

          {showMatSearch && (
            <div className="lf-mat-search">
              <div className="lf-mat-search-row">
                <input
                  type="text"
                  value={matQuery}
                  onChange={(e) => setMatQuery(e.target.value)}
                  placeholder="Search materials..."
                  className="lf-input"
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleSearchMaterials())}
                />
                <button type="button" onClick={handleSearchMaterials} className="lf-search-btn">
                  Search
                </button>
              </div>
              {matResults.length > 0 && (
                <ul className="lf-mat-results">
                  {matResults.map((m) => (
                    <li key={m.id} onClick={() => addMaterial(m)}>
                      <span>{m.name}</span>
                      <span className="lf-mat-type">{m.type}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {form.materials_shared.length === 0 ? (
            <p className="lf-empty">No materials added</p>
          ) : (
            <ul className="lf-tags">
              {form.materials_shared.map((m) => (
                <li key={m.id} className="lf-tag">
                  {m.name}
                  <button type="button" onClick={() => removeMaterial(m.id)}>×</button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* ── Samples Distributed ── */}
        <div className="lf-group full">
          <div className="lf-subsection-header">
            <span className="lf-label">Samples Distributed</span>
            <div className="lf-sample-row">
              <input
                type="text"
                value={sampleInput}
                onChange={(e) => setSampleInput(e.target.value)}
                placeholder="Sample name..."
                className="lf-input lf-sample-input"
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addSample())}
              />
              <button type="button" className="lf-add-btn" onClick={addSample}>
                + Add Sample
              </button>
            </div>
          </div>
          {form.samples_distributed.length === 0 ? (
            <p className="lf-empty">No samples added</p>
          ) : (
            <ul className="lf-tags">
              {form.samples_distributed.map((s) => (
                <li key={s.id} className="lf-tag">
                  {s.name}
                  <button type="button" onClick={() => removeSample(s.id)}>×</button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* ── Sentiment ── */}
        <div className="lf-group full">
          <label className="lf-label">Observed/Inferred HCP Sentiment</label>
          <div className="lf-sentiment-group">
            {['Positive', 'Neutral', 'Negative'].map((s) => (
              <label
                key={s}
                className={`lf-sentiment-opt ${form.sentiment === s ? 'selected' : ''}`}
              >
                <input
                  type="radio"
                  name="sentiment"
                  value={s}
                  checked={form.sentiment === s}
                  onChange={() => dispatch(updateField({ field: 'sentiment', value: s }))}
                />
                <span className={`lf-dot lf-dot-${s.toLowerCase()}`} />
                {s}
              </label>
            ))}
          </div>
        </div>

        {/* ── Outcomes ── */}
        <div className="lf-group full">
          <label className="lf-label">Outcomes</label>
          <textarea
            value={form.outcomes}
            onChange={handleChange('outcomes')}
            placeholder="Key outcomes or agreements..."
            className="lf-textarea"
            rows={3}
          />
        </div>

        {/* ── Follow-up Actions ── */}
        <div className="lf-group full">
          <label className="lf-label">Follow-up Actions</label>
          <textarea
            value={form.follow_up_actions}
            onChange={handleChange('follow_up_actions')}
            placeholder="Enter next steps or tasks..."
            className="lf-textarea"
            rows={3}
          />
        </div>

        {/* ── AI Suggested Follow-ups ── */}
        {form.ai_suggested_followups?.length > 0 && (
          <div className="lf-group full">
            <label className="lf-label lf-ai-label">✦ AI Suggested Follow-ups</label>
            <ul className="lf-suggestions">
              {form.ai_suggested_followups.map((s, i) => (
                <li key={i} className="lf-suggestion-item">
                  <span className="lf-arrow">→</span>
                  <span className="lf-suggestion-text">{s}</span>
                  <button
                    type="button"
                    className="lf-use-btn"
                    onClick={() =>
                      dispatch(
                        updateField({
                          field: 'follow_up_actions',
                          value: (form.follow_up_actions ? form.follow_up_actions + '\n' : '') + s,
                        })
                      )
                    }
                  >
                    Use
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* ── AI Summary (read-only) ── */}
        {form.ai_summary && (
          <div className="lf-group full">
            <label className="lf-label lf-ai-label">✦ AI Summary</label>
            <div className="lf-ai-summary">{form.ai_summary}</div>
          </div>
        )}

        {/* ── Status banners ── */}
        {submitError && <div className="lf-banner lf-banner-error">{submitError}</div>}
        {submitSuccess && (
          <div className="lf-banner lf-banner-success">
            ✓ Interaction logged successfully!{currentInteractionId ? ` (ID: ${currentInteractionId})` : ''}
          </div>
        )}

        {/* ── Actions ── */}
        <div className="lf-actions">
          <button type="button" onClick={() => dispatch(resetForm())} className="lf-btn lf-btn-secondary">
            Reset
          </button>
          <button type="submit" disabled={submitting} className="lf-btn lf-btn-primary">
            {submitting ? 'Saving...' : '💾 Save Interaction'}
          </button>
        </div>
      </form>
    </div>
  );
}

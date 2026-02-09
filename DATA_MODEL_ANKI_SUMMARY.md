# Data Model Updates & Anki Integration - Summary

## ✅ Completed

### 1. Database Status Enum Renamed
Successfully migrated the lemma status values:
- `staged` → `new` (ID: 1)
- `committed` → `synced` (ID: 2)  
- `pushed` → `learned` (ID: 3)

**Migrations applied:**
1. `add_new_status_enum_values` - Added new enum values to the type
2. `update_status_values` - Updated all existing records

### 2. Frontend Routes Updated
Updated `/app/page.tsx` to use new status names:
- `/status/new`
- `/status/synced`
- `/status/learned`

### 3. AnkiConnect Maturity Verification ✅
**Confirmed**: AnkiConnect API supports card maturity retrieval via `cardsInfo` action.

**How it works:**
- Call `cardsInfo` with card IDs
- Returns `interval` field for each card
- **Maturity rule**: `interval >= 21` days = mature card
- Negative interval values = cards in learning queue (seconds)

**Implementation approach:**
```javascript
// Example AnkiConnect request
{
  "action": "cardsInfo",
  "params": {
    "cards": [1234567890]
  }
}

// Response includes:
{
  "result": [{
    "cardId": 1234567890,
    "interval": 25,  // days until next review
    // ... other fields
  }]
}
```

## 📋 Next Steps

### A. Implement `/learn` Page
- [ ] Create `/app/learn/page.tsx`
- [ ] Fetch all sources from API
- [ ] For each source, display:
  - Source title and metadata
  - Multi-colored progress bar (new/synced/learned counts)
  - Coverage percentage calculation
- [ ] Add "Process Lemmata" button per source

### B. Database Schema Updates for `/learn` Page
Need to add fields to support coverage calculation:
- [ ] Add `word_count` to `source` table (total tokens in source)
- [ ] Add `position` to `lemma_context` table (token index in source)
- [ ] Verify we can calculate: `(max(position of learned lemmata) / source.word_count) * 100`

### C. Implement "Process Lemmata" UI
- [ ] Create `/app/learn/[sourceId]/process/page.tsx`
- [ ] Multi-select interface for new lemmata
- [ ] Actions: Discard (add to ignored) & Add to Anki
- [ ] Local caching with IndexedDB/localStorage
- [ ] Offline support with confirmation dialog
- [ ] Sync button to commit changes

### D. Anki Integration
- [ ] Create AnkiConnect client wrapper
- [ ] Implement `addCards` function
- [ ] Implement `cardsInfo` function to get maturity
- [ ] Update lemma status based on Anki card maturity
- [ ] Sync flow: new → synced (added to Anki) → learned (mature in Anki)

## 🔍 Technical Considerations

**Progress Bar Calculation:**
- Query counts: `SELECT status_id, COUNT(*) FROM lemma WHERE id IN (SELECT lemma_id FROM lemma_source WHERE source_id = ?) GROUP BY status_id`
- Coverage: Need to store position with first context, not lemma itself (since lemmata can appear in multiple sources)

**Anki Sync Strategy:**
- On page load: Fetch card IDs from Anki, check maturity, update DB
- On "Add to Anki": Create cards, update status to `synced`
- Periodic sync: Check maturity of `synced` cards, promote to `learned` if mature

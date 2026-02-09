# Quick Test Guide - Tool Matching Fix

## How to Test the Fix

### Prerequisites
- Backend running: `python -m uvicorn app.main:app --reload`
- Frontend running or access to http://localhost:3000
- CSV file with data (you have examples in `tmp/` folder)

### Test 1: Original Working Case
**Input:** "Generate summary statistics"
**File:** Upload any CSV
**Expected:** ✅ Works (matches exactly)

### Test 2: Informal Wording (NEW - Previously Broken)
**Input:** "give me data stats?"
**File:** Upload any CSV
**Expected:** ✅ Works now (fuzzy match finds the tool)

### Test 3: Missing Values with Typo
**Input:** "what are the missing values"
**File:** Upload any CSV with missing values
**Expected:** ✅ Works (matches "Detect missing values")

### Test 4: Abbreviated Request
**Input:** "summary"
**File:** Upload any CSV
**Expected:** ✅ Works (fuzzy match 70%+)

### Test 5: Check Console Logs
While running any test:
1. Open terminal where backend is running
2. Look for output like:
   ```
   Matched step 'generate summary stats' to tool 'Generate summary statistics' (score: 0.87)
   Executing tool: Generate summary statistics
   Tool Generate summary statistics executed successfully
   ```

### Test 6: Check for Graceful Fallback
**Input:** "do something random that doesn't match any tool"
**File:** Upload any CSV
**Expected:** 
- ✅ No crash/error
- ✅ Log shows "Could not find matching tool for step"
- ✅ Returns message about no matching tool

## How the Fix Works

### Before (Broken)
```
User: "give me data stats?"
LLM Plan: ["Generate summary statistics"]
Executor: Looks for exact phrase "summary statistics" ← FAILS
Result: ❌ No result shown
```

### After (Fixed)
```
User: "give me data stats?"
LLM Plan: ["Generate summary statistics"]
Executor: Uses fuzzy matching
  - Compares "generate summary statistics"
  - To available tools: ["Generate summary statistics", "Detect missing values"]
  - Finds 100% match
Result: ✅ Successfully executes the tool
```

## Monitoring the Fix

### Enable Debug Logging (Optional)
Edit `app/main.py`:
```python
logging.basicConfig(level=logging.DEBUG)  # Change from INFO to DEBUG
```

Then restart the server. You'll see even more detailed matching info.

### Key Log Messages to Expect

**Success:**
```
INFO: Matched step 'generate summary stats' to tool 'Generate summary statistics' (score: 0.87)
INFO: Executing tool: Generate summary statistics
INFO: Tool Generate summary statistics executed successfully
```

**Fallback:**
```
WARNING: Could not find matching tool for step: 'random action'
```

## Comparing with Before/After

### Scenario: User says "get me a summary"

**BEFORE (Broken Behavior):**
- LLM creates plan: `["Get data summary statistics"]`
- Executor searches for exact match of "summary statistics" → Not found
- Falls through without executing anything
- UI shows: "No result"
- Logs show: Nothing executed

**AFTER (Fixed Behavior):**
- LLM creates plan: `["Get data summary statistics"]`
- Executor fuzzy matches: `"Get data summary statistics"` → `"Generate summary statistics"` (score: 0.78)
- Tool executes successfully
- UI shows: Summary statistics table
- Logs show: Matched and executed

## Troubleshooting

If you don't see the fuzzy matching working:

1. **Check API key is set:**
   ```bash
   echo $OPENAI_API_KEY
   ```
   Should show your actual key, not empty

2. **Check server restarted:**
   ```bash
   # Stop the server (Ctrl+C) and restart
   python -m uvicorn app.main:app --reload
   ```

3. **Check CSV file exists:**
   Must upload a valid CSV file with data

4. **Check logs for errors:**
   Look for "Error calling OpenAI API" or similar

## Sample Test Data

Use the files in `tmp/` folder:
- `missing.csv` - Has missing values (test "Detect missing values")
- `test.csv` - Has complete data (test "Generate summary statistics")

## Expected Behavior Summary

| User Input | Tool Called | Result |
|-----------|------------|--------|
| "generate summary statistics" | Generate summary statistics | ✅ |
| "give me data stats?" | Generate summary statistics | ✅ (NEW) |
| "what are missing values?" | Detect missing values | ✅ (NEW) |
| "summarize the data" | Generate summary statistics | ✅ (NEW) |
| "find gaps in data" | Detect missing values | ✅ (NEW) |
| "random unrelated task" | No match | ⚠️ Graceful fallback |

The last row won't crash - it will log a warning and tell you no matching tool exists.


# AI CLI Process: Auto-Generate Test Case Spreadsheets

## How this works
You (the tester) give the AI **one input**: the component name (e.g. "Main Menu").
The AI never asks what to test — it only asks for the component name if missing.
Everything else below, the AI does on its own.

---

## STEP 1 — Take the component name
Input: a single component (e.g. `Main Menu`, `Inventory`, `Settings`).
Use this to build the Test Case ID prefix — first letters of the component, e.g.:
- Main Menu → `MM`
- Settings → `SNG`
- Inventory → `INV`

---

## STEP 2 — List all scenarios for that component
The AI brainstorms every distinct thing a user can DO in that component, and lists each as its own **scenario**. One scenario = one test case block = one sheet in the workbook.

Example, component = "Main Menu":
1. Starting a new game
2. Loading a saved game
3. Opening Settings (volume, sfx, theme)
4. Quitting the game
5. Navigating menu with keyboard vs mouse
6. Clicking outside a menu popup (does it close?)
7. Rapid double-clicking a button (does it break?)

Rule: include both normal (happy path) scenarios AND edge cases (invalid input, spam clicking, empty state, etc).

---

## STEP 3 — Build each scenario into a full test case block
For every scenario from Step 2, fill out this exact structure (matches your existing template):

| Field | Rule |
|---|---|
| Test Case ID | `{PREFIX}_{number}` e.g. `MM_001`, `MM_002` (increment per scenario) |
| Test Case Description | One line: what part of the component this test covers |
| Created By | Leave blank or use placeholder — tester fills in |
| Reviewed By | Leave blank |
| Version | `1.0` |
| QA Tester's Log | Leave blank |
| Tester's Name | Leave blank |
| Date Tested | Leave blank |
| Test Case (Pass/Fail/Not Executed) | `Not Executed` (default) |
| Prerequisites | Tools/state needed before testing (e.g. "pygame package", "save file exists") |
| Test Data | Inputs needed (e.g. "Mouse click", "Keyboard arrow keys", sample username/password) |
| Test Scenario | Short sentence describing the scenario (from Step 2) |

---

## STEP 4 — Write the steps + expected results
For each scenario, break it into individual steps. Each step needs:
- **Step No.** — sequential number
- **Step Details** — exact action to perform (be specific: which button, which click type, which direction)
- **Expected Results** — what should visibly happen if it works correctly
- **Actual Results** — leave blank (tester fills in after running)
- **Pass/Fail/Not Executed/Suspended** — default to `Not Executed`

Rule: one action per step. Don't combine two actions into one row.

---

## STEP 5 — Fill the spreadsheet using this exact cell map
Each test case gets its own sheet. Use this layout (matches `Settings_Testing.xlsx`):

| Cell | Content |
|---|---|
| A1 | `Test Case ID` |
| C1 | the ID (e.g. `MM_001`) |
| D1 | `Test Case Description` |
| F1 | description text |
| A2 | `Created By` |
| D2 | `Reviewed By` |
| H2 | `Version` / J2 = `1.0` |
| A4 | `QA Tester's Log` |
| A6 | `Tester's Name` / D6 `Date Tested` / H6 `Test Case (Pass/Fail/Not Executed)` |
| A8 | `S No.` / B8 `Prerequisites:` / G8 `S No.` / H8 `Test Data` |
| A9:A12 | 1–4 (prerequisite row numbers) / B9:B12 prerequisite text |
| G9:G12 | 1–4 (test data row numbers) / H9:H12 test data text |
| A14 | `Test Scenario` / B14 scenario sentence |
| A16 | `Step No.` / B16 `Step Details` / D16 `Expected Results` / F16 `Actual Results` / I16 `Pass / Fail / Not executed / Suspended` |
| A18+ | step rows: step number, step detail, expected result, (actual left blank), `Not Executed` |

Sheet name = the Test Case ID (e.g. `MM_001`).

---

## STEP 6 — Save and hand back
- One `.xlsx` file, one sheet per scenario, named after the component (e.g. `MainMenu_Testing.xlsx`).
- Recalculate/save with no formula errors.
- Tell the tester how many scenarios/test cases were generated.

---

## Example prompt to give the AI CLI
```
Using the process in AI_TestCase_Generation_Process.md, generate test cases 
for the component: "Main Menu". Base the format on Settings_Testing.xlsx.
```

That's the whole loop — you only ever type the component name.

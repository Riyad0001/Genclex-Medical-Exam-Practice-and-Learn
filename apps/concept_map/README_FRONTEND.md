# Concept Map API — Frontend Integration Guide

This guide explains how frontend developers (React, Vue, Flutter, or Vanilla JS) can integrate the **Clinical Concept Map (CARA)** API, render nodes with standard category colors, handle AI prompt edits, and manually add/edit nodes and edges.

---

## 1. API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/concept-map/` | Load user's saved map. Returns welcome message if no map exists (`404`). |
| `POST` | `/api/concept-map/generate/` | Generate a new map or update the current map using AI prompts. |
| `PUT` | `/api/concept-map/` | Directly save manual edits (nodes, colors, edges) made on the frontend. |

> **Header required for all requests:**
> ```http
> Authorization: Bearer <user_access_token>
> Content-Type: application/json
> ```

---

## 2. Node Category Color Mapping Guide

Every node contains a `category` string. Use this exact category to map node background colors, border colors, and badge tags on the canvas.

| Category Name | Typical Color Scheme | UI Meaning / Node Type |
| :--- | :--- | :--- |
| **`Central`** | **Gold / Amber / Dark Blue** | Primary condition & patient baseline |
| **`Risk Factor`** | **Orange / Amber** | History, age, underlying comorbidities |
| **`Subjective Data`** | **Teal / Cyan** | Patient-reported symptoms & feelings |
| **`Objective Data`** | **Purple / Violet** | Vitals, labs, diagnostic findings |
| **`Nursing Diagnosis`** | **Red / Rose** | NANDA nursing diagnosis |
| **`Intervention`** | **Green / Emerald** | Nursing actions & care protocols |
| **`Medication`** | **Indigo / Blue** | Drug classes, dosages & indications |
| **`Complication`** | **Crimson / Dark Red** | Disease risks & acute emergencies |

### CSS Color Palette Example:
```css
.node-central          { background-color: #1e3a8a; color: #ffffff; border-color: #3b82f6; }
.node-risk-factor      { background-color: #ffedd5; color: #9a3412; border-color: #f97316; }
.node-subjective-data  { background-color: #ccfbf1; color: #115e59; border-color: #14b8a6; }
.node-objective-data   { background-color: #f3e8ff; color: #6b21a8; border-color: #a855f7; }
.node-nursing-diagnosis{ background-color: #ffe4e6; color: #9f1239; border-color: #f43f5e; }
.node-intervention     { background-color: #dcfce7; color: #166534; border-color: #22c55e; }
.node-medication       { background-color: #e0e7ff; color: #3730a3; border-color: #6366f1; }
.node-complication     { background-color: #fee2e2; color: #991b1b; border-color: #ef4444; }
```

---

## 3. Frontend Workflow

### Step 1: Initial Page Load (`GET /api/concept-map/`)
When opening the Concept Map screen:
1. Call `GET /api/concept-map/`.
2. If response is `200 OK`:
   - Set `exists: true`.
   - Render `response.data.map.nodes` and `response.data.map.edges` on your visualizer graph library (e.g. React Flow, Vis.js, D3.js).
3. If response is `404 Not Found`:
   - Set `exists: false`.
   - Display CARA onboarding chat bubble with `response.data.welcome_message`.

```js
async function loadConceptMap() {
  const res = await fetch('/api/concept-map/', {
    headers: { Authorization: `Bearer ${token}` }
  });
  if (res.status === 200) {
    const data = await res.json();
    renderGraph(data.map.nodes, data.map.edges);
  } else if (res.status === 404) {
    const data = await res.json();
    showWelcomeScreen(data.welcome_message);
  }
}
```

---

### Step 2: AI Generation & Prompts (`POST /api/concept-map/generate/`)
When user submits a prompt in the input box:
1. Send prompt to `POST /api/concept-map/generate/`.
2. Backend calls AI, preserves existing nodes, applies the update, saves to DB, and returns full updated map.
3. Re-render the canvas graph using the returned `nodes` and `edges`.

```js
async function sendAiPrompt(userPromptText) {
  const res = await fetch('/api/concept-map/generate/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ prompt: userPromptText })
  });

  const fullUpdatedMap = await res.json();
  renderGraph(fullUpdatedMap.nodes, fullUpdatedMap.edges);
}
```

---

### Step 3: Manual Edit / Add Node on Frontend (`PUT /api/concept-map/`)
If the user clicks "+ Add Node" button or changes a node color dropdown on your canvas UI:

#### A. How to Add a New Node Manually:
Construct a new node object and push it into your local `nodes` array:

```js
function addNewNodeManually(label, details, category, parentNodeId) {
  const newNodeId = `n_custom_${Date.now()}`;
  
  const newNode = {
    id: newNodeId,
    label: label,         // e.g. "Monitor Vitals"
    details: details,     // e.g. "Check BP every 2 hours"
    category: category    // Must be one of the 8 valid category strings
  };

  const newEdge = {
    id: `e_${parentNodeId}_${newNodeId}`,
    source: parentNodeId,
    target: newNodeId,
    label: "managed by"
  };

  currentNodes.push(newNode);
  currentEdges.push(newEdge);

  // Trigger Save to backend
  saveConceptMapToBackend(currentTitle, currentNodes, currentEdges);
}
```

#### B. How to Change Node Color (Category):
To change node color, simply update its `category` property:
```js
function changeNodeColorCategory(nodeId, newCategory) {
  const node = currentNodes.find(n => n.id === nodeId);
  if (node) {
    node.category = newCategory; // e.g. "Medication"
    saveConceptMapToBackend(currentTitle, currentNodes, currentEdges);
  }
}
```

#### C. Save Current Canvas State to Database (`PUT /api/concept-map/`):
```js
async function saveConceptMapToBackend(title, nodes, edges) {
  const res = await fetch('/api/concept-map/', {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      title: title,
      nodes: nodes,
      edges: edges
    })
  });

  const responseData = await res.json();
  console.log("Map saved successfully:", responseData);
}
```

---

## 4. Node & Edge Data Structures

### Node Object Format:
```json
{
  "id": "n_dx_fluid",
  "label": "Excess Fluid Volume",
  "details": ". r/t compromised cardiac regulatory mechanisms . AEB crackles, 2+ edema",
  "category": "Nursing Diagnosis"
}
```

### Edge Object Format:
```json
{
  "id": "e_n_central_n_dx_fluid",
  "source": "n_central",
  "target": "n_dx_fluid",
  "label": "leads to"
}
```

---

## 5. Summary Flow Diagram

```
+-------------------------------------------------------------------+
|                         Frontend Canvas                           |
+-------------------------------------------------------------------+
       |                                      |               |
       | 1. Initial Load                      | 2. AI Prompt  | 3. Manual Edit
       v                                      v               v
  GET /api/concept-map/            POST /generate/   PUT /api/concept-map/
       |                                      |               |
       +------------------+-------------------+---------------+
                          |
                          v
               Backend Database & OpenAI
```

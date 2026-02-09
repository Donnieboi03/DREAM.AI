# NEXT STEPS - Action Items for You

## Immediate Setup (Do This First)

### 1. Install Missing Dependencies

```bash
cd c:\Users\Midhun\Desktop\Projects\DREAM.AI\dreamai

# Install backend dependencies
pip install -r requirements.txt
pip install fastapi uvicorn pillow
```

**Expected time**: 2-5 minutes

### 2. Test Backend Startup

```bash
cd c:\Users\Midhun\Desktop\Projects\DREAM.AI\dreamai
python -m backend.api.app
```

**Look for**:
```
Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
Starting DREAM.AI backend...
Environment initialized successfully
```

**If you see errors**:
- Check that all files were created correctly (see File Locations below)
- Ensure Python packages are installed
- Verify AI2-THOR is installed: `python -c "import ai2thor; print(ai2thor.__version__)"`

### 3. Test Health Endpoint

In a new terminal:
```bash
curl http://localhost:8000/health
```

**Expected response**:
```json
{
  "status": "ok",
  "environment_initialized": true,
  "connected_clients": 0
}
```

### 4. Install Frontend Dependencies

```bash
cd c:\Users\Midhun\Desktop\Projects\DREAM.AI\dreamai\frontend
npm install
```

**Expected time**: 2-3 minutes

### 5. Start Frontend

Keep backend running (from step 2), open a new terminal:

```bash
cd c:\Users\Midhun\Desktop\Projects\DREAM.AI\dreamai\frontend
npm run dev
```

**Look for**:
```
VITE v... ready in ... ms

➜  Local:   http://localhost:5173/
```

### 6. Open in Browser

Go to: **http://localhost:5173**

**You should see**:
- Header: "DREAM.AI - ProcTHOR Control Panel"
- Connection status (green "● Connected")
- Game canvas showing ProcTHOR environment
- Control buttons on the left sidebar
- Metrics display

---

## Common Issues & Fixes

### Issue: "ModuleNotFoundError: No module named 'backend'"

**Cause**: Running from wrong directory

**Fix**:
```bash
cd c:\Users\Midhun\Desktop\Projects\DREAM.AI
python -m dreamai.backend.api.app
```

---

### Issue: "failed to establish a new connection" (WebSocket)

**Cause**: Backend not running or port 8000 blocked

**Fix**:
```bash
# Check if backend is running
netstat -an | findstr 8000

# If nothing shows, start backend:
python -m backend.api.app

# If port is in use, kill the process:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

### Issue: Canvas is blank

**Cause**: Environment not initialized or frames not streaming

**Fix**:
1. Check backend console for initialization errors
2. Click "Reset" button in browser
3. Check browser console (F12) for JavaScript errors
4. Verify WebSocket messages in DevTools (Network tab)

---

### Issue: "npm: command not found"

**Cause**: Node.js not installed

**Fix**:
1. Install Node.js from https://nodejs.org/ (LTS version)
2. Restart terminal
3. Verify: `node --version`

---

## File Locations & What Was Created

All files are in `c:\Users\Midhun\Desktop\Projects\DREAM.AI\`

### Backend Files

```
dreamai/backend/api/
├── app.py                    (CREATED) - FastAPI app with WebSocket
├── websocket_stream.py       (CREATED) - Frame streaming logic
└── orchestrator_routes.py    (CREATED) - Task generation API

dreamai/backend/orchestrator/
└── task_generator.py         (CREATED) - Prompt to task conversion
```

### Frontend Files

```
dreamai/frontend/src/
├── App.tsx                   (MODIFIED) - Main layout
└── components/
    ├── GameViewport.tsx      (CREATED) - Canvas + WebSocket
    ├── UIOverlays.tsx        (CREATED) - Controls & prompts
    └── DetailedMetrics.tsx   (CREATED) - Metrics & graphs
```

### Documentation

```
└─ BROWSER_INTERFACE_SETUP.md  (CREATED) - Full setup guide
└─ IMPLEMENTATION_SUMMARY.md   (CREATED) - Technical overview
└─ NEXT_STEPS.md               (THIS FILE)
└─ start_browser_interface.bat (CREATED) - One-click launcher (Windows)
```

---

## Testing Workflow

### Test 1: Backend Connectivity

```bash
# Terminal 1: Start backend
python -m backend.api.app

# Terminal 2: Test health endpoint
curl http://localhost:8000/health

# Expected: JSON with status "ok"
```

---

### Test 2: Environment Initialization

Check backend console output:

```
Starting DREAM.AI backend...
Environment initialized successfully  # ← Look for this line
```

If you see errors like `failed to create house`, check:
- Is GPU available? (ProcTHOR needs GPU for rendering)
- Do you have enough disk space?
- Is Unity player installed?

---

### Test 3: WebSocket Streaming

1. Start backend & frontend (steps 2 & 5 above)
2. Open browser to http://localhost:5173
3. Watch for status indicator to turn green ("Connected")
4. Canvas should show the game environment
5. Click a control button and see metrics update

---

### Test 4: Action Control

1. With browser connected, click "Move Ahead" button
2. Watch the game canvas - agent should move
3. Check metrics - "Steps" counter should increment
4. Try other buttons to verify they work

---

### Test 5: Prompt Submission

1. In the "Task Prompt" box, type: `Go to the corner of the room`
2. Click "Submit Task"
3. Check browser console for response
4. Backend should log task generation

---

## Customization Checklist

### If you want to change...

**Frame resolution**:
Edit `backend/api/app.py`:
```python
game_env = make_procthor_env(width=400, height=400)  # Was 300x300
```

**Streaming frame rate**:
Edit `backend/api/websocket_stream.py`:
```python
await self.broadcast_frame(observation, self.current_metrics)
await asyncio.sleep(1.0 / 60)  # Was 1/30 for 30 FPS, now 60 FPS
```

**JPEG compression quality**:
Edit `backend/api/websocket_stream.py`:
```python
pil_image.save(jpeg_buffer, format="JPEG", quality=90)  # Was 85, higher = better
```

**Canvas size**:
Edit `frontend/src/components/GameViewport.tsx`:
```typescript
<canvas width={1024} height={768} />  # Was 800x600
```

**UI theme colors**:
Edit any `frontend/src/components/*.tsx` file:
```typescript
const styles = {
  container: {
    backgroundColor: "#1a1f3a",  // Dark blue, change this to any color
    // ...
  }
}
```

---

## Troubleshooting Decision Tree

```
Frontend shows "Disconnected"?
├─ Is backend running?
│  └─ No → Start: python -m backend.api.app
│  └─ Yes → Continue
├─ Is port 8000 open?
│  └─ No → Check firewall, restart backend
│  └─ Yes → Continue
└─ Check browser console (F12) for WebSocket errors

Canvas is blank?
├─ Is status "Connected"?
│  └─ No → Resolve connection issue above
│  └─ Yes → Continue
├─ Click "Reset" button
├─ Check backend logs for errors
└─ If still blank, may need to set GPU options in backend

Buttons don't work?
├─ Check browser console for errors
├─ Verify backend is receiving WebSocket messages
│  └─ Enable WebSocket debugging in browser DevTools
└─ Check that environment stepped correctly in backend logs

Slow performance?
├─ Reduce JPEG quality (backend/api/websocket_stream.py)
├─ Reduce target FPS (30 → 15)
├─ Reduce canvas resolution (800x600 → 640x480)
└─ Check network latency: ping localhost
```

---

## Next Steps After Getting It Running

1. **Verify Everything Works** (1-2 hours)
   - Follow the testing workflow above
   - Get all tests passing
   - Document any issues you encounter

2. **Integrate LLM for Better Task Generation** (2-4 hours)
   - Update `backend/orchestrator/task_generator.py`
   - Connect to `backend/llm/` module
   - Test with various natural language prompts

3. **Add Episode Storage** (1-2 hours)
   - Implement save/load in `backend/storage/`
   - Add replay functionality to frontend
   - Enable session persistence

4. **Enhance Metrics Display** (1-2 hours)
   - Add more graphs (success rate, action history)
   - Implement action heatmaps
   - Add failure reason categorization

5. **Production Deployment** (2-4 hours)
   - Set up HTTPS (certbot + nginx)
   - Add authentication if needed
   - Configure for remote access
   - Set up monitoring/logging

---

## Getting Help

If you encounter issues:

1. **Check the logs**
   - Backend: Look at console output when running `python -m backend.api.app`
   - Frontend: Open DevTools (F12) → Console tab
   - Network: DevTools → Network tab, check WebSocket messages

2. **Check the documentation**
   - `BROWSER_INTERFACE_SETUP.md` - Full setup guide
   - `IMPLEMENTATION_SUMMARY.md` - Technical overview
   - Code comments in generated files

3. **Common error patterns**
   - Module not found: Check imports and file locations
   - WebSocket errors: Check backend is running and listening
   - Environment errors: Verify AI2-THOR installation

---

## Success Indicators

When everything is working correctly, you should be able to:

- [ ] Start backend without errors
- [ ] Health endpoint returns valid response
- [ ] Frontend connects (green status indicator)
- [ ] See game environment in canvas
- [ ] Click buttons and see agent move
- [ ] Metrics update in real-time
- [ ] Reset button clears episode counter
- [ ] Prompt submission doesn't error
- [ ] All console logs are clean (no error messages)

---

## Quick Commands Reference

```bash
# Backend startup
cd c:\Users\Midhun\Desktop\Projects\DREAM.AI\dreamai && python -m backend.api.app

# Frontend startup
cd c:\Users\Midhun\Desktop\Projects\DREAM.AI\dreamai\frontend && npm run dev

# Health check
curl http://localhost:8000/health

# Kill backend (if stuck)
netstat -ano | findstr :8000 | findstr LISTENING
taskkill /PID <PID> /F

# Reinstall frontend deps
cd c:\Users\Midhun\Desktop\Projects\DREAM.AI\dreamai\frontend && rm -r node_modules && npm install

# Reinstall backend deps
cd c:\Users\Midhun\Desktop\Projects\DREAM.AI\dreamai && pip install --upgrade -r requirements.txt
```

---

**You're all set! Start with "Immediate Setup" and work through the tests. Let me know if you hit any issues.**

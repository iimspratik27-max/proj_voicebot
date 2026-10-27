# VoiceMeet — Shared Recordings Demo (Version 3)

This version adds a small Python server so each push-to-talk audio clip is uploaded to a shared `recordings` folder. The Host/Admin portal can see recordings uploaded by users; users can see their own recordings.

## Run on Windows using VS Code

1. Stop any old server running in the VS Code terminal with `Ctrl+C`.
2. In VS Code, open this `voicemeet_mvp` folder (the folder that contains `host.html`, `user.html`, and `server.py`).
3. Open **Terminal → New Terminal**.
4. Run:

   ```powershell
   python server.py
   ```

5. Keep the terminal open. Open these URLs in Chrome:
   - Host/Admin: http://localhost:8000/host.html
   - User: http://localhost:8000/user.html

6. Sign in, join a meeting, hold the microphone button to speak, then release it. Wait for the message that the clip was saved to the shared server.
7. Open the Host/Admin portal and select **Recordings**. It refreshes the shared recording list every five seconds while that page is open.

## Demo accounts

- Admin: `admin@voicemeet.local` / `Demo@123`
- User: `amit@example.com` / `Amit@123`
- User: `suman@example.com` / `Suman@123`

## Where audio is stored

Audio files are saved under `recordings/`; metadata is in `recordings/recordings.json`. Keep the Python server running for upload and playback. Back up this folder if you need to retain recordings.

## Important limitations

- This is a local development demo, not a production service. The server has no real authentication/authorization layer for the recording API. Do not expose it to the public internet or store sensitive recordings with it.
- Both portals must use the same server URL to share recordings. `localhost` works on this computer only; another device needs a LAN-accessible server address or deployed HTTPS service.
- It records each speaker's own microphone segment only. Live audio between participants and mixed meeting recordings are not implemented yet.
- Browser-generated audio is generally WebM/Opus. WhatsApp sharing options depend on the browser/device.

# Start Script Update - Production Mode Support

## Changes Made

Updated `start.sh` to automatically detect and run in **production mode** when `NEXT_PUBLIC_ENV_MODE=PRODUCTION` is set in `apps/frontend/.env.local`.

## How It Works

### Automatic Mode Detection

The script now:
1. **Checks** `apps/frontend/.env.local` for `NEXT_PUBLIC_ENV_MODE=PRODUCTION`
2. **If Production Mode**:
   - Builds the frontend first (`pnpm run build`)
   - Runs production server (`pnpm start`)
   - Binds to `0.0.0.0:3000` (for nginx compatibility)
3. **If Development Mode** (default):
   - Runs dev server (`pnpm run dev`)
   - Binds to `0.0.0.0:3000`

### Production Mode Benefits

✅ **No Turbopack indicator** - Clean production UI
✅ **Optimized builds** - Faster performance
✅ **Production optimizations** - Better caching, minification
✅ **No dev warnings** - Clean console

### Development Mode Benefits

✅ **Hot reload** - Instant updates on code changes
✅ **Fast refresh** - React component updates
✅ **Source maps** - Better debugging
✅ **Faster startup** - No build step needed

## Usage

### Start in Production Mode

1. **Set production mode** in `apps/frontend/.env.local`:
   ```bash
   NEXT_PUBLIC_ENV_MODE=PRODUCTION
   ```

2. **Run start script**:
   ```bash
   ./start.sh
   ```

   The script will:
   - Detect production mode
   - Build the frontend
   - Start production server
   - Show "PRODUCTION mode" in status

### Start in Development Mode

1. **Set development mode** (or remove the line) in `apps/frontend/.env.local`:
   ```bash
   NEXT_PUBLIC_ENV_MODE=LOCAL
   # or just remove NEXT_PUBLIC_ENV_MODE line
   ```

2. **Run start script**:
   ```bash
   ./start.sh
   ```

   The script will:
   - Detect development mode
   - Start dev server (no build needed)
   - Show "DEVELOPMENT mode" in status

## Status Output

The script now shows which mode is running:

```
Services:
  • Redis:        Running (Docker)
  • Frontend:     Running (PID: 12345) - PRODUCTION mode - http://localhost:3000
  • Backend:      Running (PID: 12346) - http://localhost:8000
  • Worker:       Running (PID: 12347)
```

## Important Notes

### Production Mode
- **First run**: Takes longer (builds frontend)
- **Subsequent runs**: Faster (reuses build if no changes)
- **Code changes**: Requires restart and rebuild
- **No hot reload**: Need to rebuild to see changes

### Development Mode
- **Fast startup**: No build step
- **Hot reload**: Changes appear instantly
- **Turbopack indicator**: Normal in dev mode

## Troubleshooting

### Build Fails
If production build fails:
1. Check `$LOGS_DIR/frontend-build.log` for errors
2. Fix any TypeScript/ESLint errors
3. Ensure all dependencies are installed (`pnpm install`)

### Port Already in Use
If port 3000 is in use:
- Script will attempt to free it automatically
- If it fails, manually stop the process:
  ```bash
  lsof -ti:3000 | xargs kill -9
  ```

### Switch Between Modes
To switch modes:
1. Update `apps/frontend/.env.local`
2. Stop services: `./stop.sh`
3. Start again: `./start.sh`

## Summary

✅ **Automatic mode detection** from `.env.local`
✅ **Production builds** when `NEXT_PUBLIC_ENV_MODE=PRODUCTION`
✅ **Development mode** as default/fallback
✅ **Clear status indicators** showing which mode is running
✅ **Nginx compatible** - binds to `0.0.0.0:3000` in both modes

The script now seamlessly handles both production and development modes! 🚀

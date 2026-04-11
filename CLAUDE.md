# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ShopMart is a React + Vite e-commerce shopping cart application with a Supabase backend. The UI is in Korean. All app source lives under `shop/`.

## Commands

All commands must be run from the `shop/` directory:

```bash
npm install       # Install dependencies
npm run dev       # Start dev server (http://localhost:5173)
npm run build     # Production build (output: dist/)
npm run preview   # Preview production build
npm run lint      # Run ESLint
```

No test framework is configured.

## Architecture

The app is a single-page React application with Supabase as the only backend.

**Component tree:**
- `App.jsx` — root component; owns all state (products, cart, filters, toasts) and all Supabase calls
  - `ProductCard` — renders one product; emits add-to-cart events up to App
  - `CartSidebar` — slide-in cart overlay; calls App handlers for quantity changes and removal

**Session model:** Anonymous users are identified by a UUID stored in `localStorage` via the `useSession()` hook (`src/useSession.js`). No authentication is required.

**Supabase tables:**
- `products` — catalog: `id, name, description, category, price, stock, image_url, created_at`
- `cart_items` — per-session cart: `id, session_id, product_id, quantity`

**Supabase client** is initialized once in `src/supabase.js` with hardcoded credentials and imported wherever needed.

## MCP Integration

The project is configured with the Supabase MCP server (`.mcp.json`), so Claude Code can query and manage the Supabase project directly via `mcp__supabase__*` tools.

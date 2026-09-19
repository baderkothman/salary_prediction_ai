import { cleanup } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { afterEach } from "vitest";

// Without `test.globals: true` (deliberately not set -- every test file
// imports describe/it/expect explicitly), @testing-library/react's
// automatic afterEach cleanup never registers, so DOM from a prior test
// silently accumulates and later assertions see duplicate elements. Wire
// it up explicitly instead of turning on globals mode.
afterEach(() => {
  cleanup();
});

// Tests never hit the real Supabase project -- lib/supabase.ts throws at
// import time if these are missing, and every test that needs controlled
// data mocks ../lib/queries directly rather than the network layer.
import.meta.env.VITE_SUPABASE_URL = "https://test.supabase.co";
import.meta.env.VITE_SUPABASE_ANON_KEY = "test-anon-key";

// jsdom doesn't implement ResizeObserver, which Recharts' ResponsiveContainer requires.
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverMock;

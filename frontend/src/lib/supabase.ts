import { createClient } from "@supabase/supabase-js";

const url = import.meta.env.VITE_SUPABASE_URL;
const anonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!url || !anonKey) {
  throw new Error(
    "Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY. Copy .env.example to .env and fill in the frontend values."
  );
}

// Only the public URL + anon key ever reach the browser. RLS on the
// database (supabase/migrations/) is what actually restricts this client
// to reading published data -- see security.md.
export const supabase = createClient(url, anonKey);

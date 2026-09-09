import { createClient } from "@supabase/supabase-js";

const supabaseUrl =
  process.env.NEXT_PUBLIC_SUPABASE_URL || "https://lhxbzflectkuysaklvji.supabase.co";
const supabaseAnonKey =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "sb_publishable_59E__jIIWr3HRG3XkV4Rcg_U0KZdYNH";

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://jgosmnofircqefmnoazt.supabase.co'
const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impnb3Ntbm9maXJjcWVmbW5vYXp0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzQ2ODI1ODYsImV4cCI6MjA5MDI1ODU4Nn0.rcvnrFTneGo-F-MBakzuyX2Z6_-mS9MeieFp3Ik1lOw'

export const supabase = createClient(supabaseUrl, supabaseKey)

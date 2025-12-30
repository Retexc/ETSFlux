import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY


// Import devStorage helper for IndexedDB operations
import { devStorage } from './devStorage.js';

let supabaseInstance

if (import.meta.env.DEV) {
  console.log('🔧 DEV MODE: Using Mock Supabase Client with IndexedDB Storage')
  
  // Mock User for Dev
  const mockUser = {
    id: 'dev-user-123',
    email: 'dev@etsflux.local',
    app_metadata: {},
    user_metadata: {},
    aud: 'authenticated',
    created_at: new Date().toISOString()
  }

  // Session Mock
  const mockSession = {
    access_token: 'mock-token',
    refresh_token: 'mock-refresh-token',
    expires_in: 3600,
    user: mockUser
  }

  supabaseInstance = {
    auth: {
      getUser: async () => ({ data: { user: mockUser }, error: null }),
      signInWithPassword: async () => ({ data: { user: mockUser, session: mockSession }, error: null }),
      signOut: async () => ({ error: null }),
      onAuthStateChange: (cb) => {
        // Immediately trigger signed in state
        setTimeout(() => cb('SIGNED_IN', mockSession), 0)
        return { data: { subscription: { unsubscribe: () => {} } } }
      },
      updateUser: async () => ({ data: { user: mockUser }, error: null })
    },
    storage: {
      from: () => ({
        // Upload now saves actual file to IndexedDB
        upload: async (path, file) => {
             console.log(`🔧 [MOCK] Saving file to IDB: ${path}`);
             try {
                await devStorage.saveFile(path, file);
                return { data: { path: path }, error: null };
             } catch (e) {
                console.error("MOCK UPLOAD ERROR", e);
                return { data: null, error: e };
             }
        },
        // Remove now deletes from IndexedDB
        remove: async (paths) => {
             console.log(`🔧 [MOCK] Removing files from IDB:`, paths);
             try {
                for (const path of paths) {
                  await devStorage.removeFile(path);
                }
                return { error: null }
             } catch (e) {
                return { error: e }
             }
        },
        download: async () => {
             console.warn('🔧 [MOCK] Storage Download failed (expected) to force local fallback');
             return { data: null, error: { message: 'Mock download failed' } }
        },
        // Public URL now returns just the path (store will resolve it later)
        getPublicUrl: (path) => ({ data: { publicUrl: path } })
      })
    }
  }
} else {
  // Production Real Client
  supabaseInstance = createClient(supabaseUrl, supabaseAnonKey)
}

export const supabase = supabaseInstance
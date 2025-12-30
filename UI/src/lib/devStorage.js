const DB_NAME = 'ETSFlux_Dev_DB';
const STORE_NAME = 'files';
const DB_VERSION = 1;

/**
 * Open the IDB connection
 */
const openDB = () => {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = (event) => reject('IndexedDB error: ' + event.target.error);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };

    request.onsuccess = (event) => resolve(event.target.result);
  });
};

export const devStorage = {
  /**
   * Save a file (Blob/File) to storage
   * @param {string} path 
   * @param {Blob|File} file 
   */
  async saveFile(path, file) {
    try {
      const db = await openDB();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readwrite');
        const store = transaction.objectStore(STORE_NAME);
        const request = store.put(file, path);

        request.onsuccess = () => resolve(path);
        request.onerror = (e) => reject(e.target.error);
      });
    } catch (err) {
      console.error('PROMISE ERROR SAVE', err);
      throw err;
    }
  },

  /**
   * Get a file (Blob) from storage
   * @param {string} path 
   * @returns {Promise<Blob|null>}
   */
  async getFile(path) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.get(path);

      request.onsuccess = () => resolve(request.result || null);
      request.onerror = (e) => reject(e.target.error);
    });
  },

  /**
   * Remove a file from storage
   * @param {string} path 
   */
  async removeFile(path) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.delete(path);

      request.onsuccess = () => resolve();
      request.onerror = (e) => reject(e.target.error);
    });
  }
};

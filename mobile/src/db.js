const DATABASE_NAME = "chiwas-liquor-pos";
const DATABASE_VERSION = 2;
const LOCAL_ACCOUNT_SETUP_KEY = "local-account-setup-v1";

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, DATABASE_VERSION);
    request.onupgradeneeded = () => {
      const database = request.result;
      if (!database.objectStoreNames.contains("products")) {
        database.createObjectStore("products", { keyPath: "id" });
      }
      if (!database.objectStoreNames.contains("operations")) {
        database.createObjectStore("operations", { keyPath: "id" });
      }
      if (!database.objectStoreNames.contains("settings")) {
        database.createObjectStore("settings", { keyPath: "key" });
      }
      if (!database.objectStoreNames.contains("local_users")) {
        database.createObjectStore("local_users", { keyPath: "username" });
      }
      if (!database.objectStoreNames.contains("local_categories")) {
        database.createObjectStore("local_categories", {
          keyPath: "id",
          autoIncrement: true,
        });
      }
      if (!database.objectStoreNames.contains("local_products")) {
        database.createObjectStore("local_products", {
          keyPath: "id",
          autoIncrement: true,
        });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function useStore(storeName, mode, operation) {
  const database = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = database.transaction(storeName, mode);
    const request = operation(transaction.objectStore(storeName));
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
    transaction.oncomplete = () => database.close();
    transaction.onerror = () => reject(transaction.error);
  });
}

export async function getSetting(key) {
  const record = await useStore("settings", "readonly", (store) => store.get(key));
  return record?.value;
}

export async function saveSetting(key, value) {
  await useStore("settings", "readwrite", (store) => store.put({ key, value }));
}

export async function getOpenTabs(ownerKey) {
  return (await getSetting(`open-tabs:${ownerKey}`)) || [];
}

export async function saveOpenTabs(ownerKey, tabs) {
  await saveSetting(`open-tabs:${ownerKey}`, tabs);
}

export async function deleteSetting(key) {
  await useStore("settings", "readwrite", (store) => store.delete(key));
}

export async function getProducts() {
  return useStore("products", "readonly", (store) => store.getAll());
}

export async function saveCatalog(products) {
  const database = await openDatabase();
  await new Promise((resolve, reject) => {
    const transaction = database.transaction("products", "readwrite");
    const store = transaction.objectStore("products");
    store.clear();
    products.forEach((product) => store.put(product));
    transaction.oncomplete = resolve;
    transaction.onerror = () => reject(transaction.error);
  });
  database.close();
}

export async function getOperations() {
  return useStore("operations", "readonly", (store) => store.getAll());
}

export async function saveOperation(operation) {
  await useStore("operations", "readwrite", (store) => store.put(operation));
}

export async function removeOperation(id) {
  await useStore("operations", "readwrite", (store) => store.delete(id));
}

export async function getLocalUser(username) {
  return useStore("local_users", "readonly", (store) => store.get(username));
}

export async function getLocalUserCount() {
  return useStore("local_users", "readonly", (store) => store.count());
}

export async function initializeLocalStore(users, categories) {
  const database = await openDatabase();
  try {
    await new Promise((resolve, reject) => {
      const transaction = database.transaction(
        ["local_users", "local_categories", "settings"],
        "readwrite",
      );
      users.forEach((user) => transaction.objectStore("local_users").add(user));
      categories.forEach((category) => {
        transaction.objectStore("local_categories").add(category);
      });
      transaction.objectStore("settings").put({
        key: LOCAL_ACCOUNT_SETUP_KEY,
        value: true,
      });
      transaction.oncomplete = resolve;
      transaction.onerror = () => reject(transaction.error);
      transaction.onabort = () => reject(
        transaction.error || new Error("Local account setup was aborted."),
      );
    });
  } finally {
    database.close();
  }
}

export async function migrateLocalAccounts(users) {
  const database = await openDatabase();
  try {
    return await new Promise((resolve, reject) => {
      const transaction = database.transaction(
        ["local_users", "settings"],
        "readwrite",
      );
      const localUsers = transaction.objectStore("local_users");
      const settings = transaction.objectStore("settings");
      let alreadyMigrated = false;
      const markerRequest = settings.get(LOCAL_ACCOUNT_SETUP_KEY);
      markerRequest.onsuccess = () => {
        if (markerRequest.result?.value) {
          alreadyMigrated = true;
          return;
        }
        users.forEach((user) => {
          const userRequest = localUsers.get(user.username);
          userRequest.onsuccess = () => {
            const existing = userRequest.result;
            localUsers.put({
              ...existing,
              ...user,
              created_at: existing?.created_at || user.created_at,
            });
          };
        });
        settings.put({ key: LOCAL_ACCOUNT_SETUP_KEY, value: true });
      };
      transaction.oncomplete = () => resolve(!alreadyMigrated);
      transaction.onerror = () => reject(transaction.error);
      transaction.onabort = () => reject(
        transaction.error || new Error("Local account update was aborted."),
      );
    });
  } finally {
    database.close();
  }
}

export async function getLocalCategories() {
  return useStore("local_categories", "readonly", (store) => store.getAll());
}

export async function saveLocalCategory(category) {
  return useStore("local_categories", "readwrite", (store) => store.add(category));
}

export async function getLocalProducts() {
  return useStore("local_products", "readonly", (store) => store.getAll());
}

export async function saveLocalProduct(product) {
  return useStore("local_products", "readwrite", (store) => store.add(product));
}

export async function replaceLocalBackup(backup) {
  const database = await openDatabase();
  const recordsByStore = {
    products: backup.catalog_products,
    operations: backup.operations,
    local_categories: backup.categories,
    local_products: backup.products,
  };
  const transaction = database.transaction(
    Object.keys(recordsByStore),
    "readwrite",
  );
  for (const [storeName, records] of Object.entries(recordsByStore)) {
    const store = transaction.objectStore(storeName);
    store.clear();
    records.forEach((record) => store.put(record));
  }
  await new Promise((resolve, reject) => {
    transaction.oncomplete = resolve;
    transaction.onerror = () => reject(transaction.error);
    transaction.onabort = () => reject(transaction.error || new Error("Backup restore was aborted."));
  });
  database.close();
}

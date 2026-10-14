import { Capacitor } from "@capacitor/core";
import { App } from "@capacitor/app";
import { Network } from "@capacitor/network";
import { SecureStorage } from "@aparajita/capacitor-secure-storage";
import logoPath from "../../static/images/chiwas-logo.svg";
import {
  getOperations,
  getLocalCategories,
  getLocalProducts,
  getLocalUser,
  getLocalUserCount,
  getOpenTabs,
  getProducts,
  getSetting,
  removeOperation,
  replaceLocalBackup,
  saveCatalog,
  saveLocalCategory,
  saveLocalProduct,
  saveLocalUser,
  saveOpenTabs,
  saveOperation,
  saveSetting,
} from "./db.js";
import "./style.css";

const $ = (selector) => document.querySelector(selector);
const loginPanel = $("#login-panel");
const localSetupPanel = $("#local-setup-panel");
const posPanel = $("#pos-panel");
const receiptPanel = $("#receipt-panel");
const loginForm = $("#login-form");
const loginMessage = $("#login-message");
const appMessage = $("#app-message");
const apiBaseInput = $("#api-base");
const loginMode = $("#login-mode");
const productList = $("#product-list");
const cartList = $("#cart-list");
const queueList = $("#queue-list");
const cartCount = $("#cart-count");
const queueCount = $("#queue-count");
const paymentMethod = $("#payment-method");
const paymentFields = $("#payment-fields");
const saleForm = $("#sale-form");
const completeSale = $("#complete-sale");
const restockPanel = $("#restock-panel");
const restockForm = $("#restock-form");
const customerSelect = $("#sale-customer");
const localManagementPanel = $("#local-management-panel");
document.querySelectorAll(".chiwas-logo").forEach((logo) => {
  logo.src = logoPath;
});
document.querySelector('link[rel="icon"]').href = logoPath;

let session = null;
let products = [];
let customers = [];
let cart = new Map();
let activeTabId = null;
let queueIsSyncing = false;
let networkConnected = navigator.onLine;
const DEFAULT_CATEGORIES = [
  "Spirits",
  "Beers",
  "Wines",
  "Ciders",
  "Soft Drinks/Mixers",
  "Food/Kitchen",
];

function isOnline() {
  return networkConnected;
}
const today = localDateKey(new Date().toISOString());
$("#local-report-start").value = today;
$("#local-report-end").value = today;

function normalizeApiBase(value) {
  return value.trim().replace(/\/+$/, "");
}

function isTrustedLanHost(hostname) {
  const octets = hostname.split(".").map(Number);
  if (octets.length !== 4 || octets.some((octet) => !Number.isInteger(octet) || octet < 0 || octet > 255)) {
    return hostname.endsWith(".local");
  }
  return octets[0] === 10 ||
    (octets[0] === 172 && octets[1] >= 16 && octets[1] <= 31) ||
    (octets[0] === 192 && octets[1] === 168);
}

function ownerKey() {
  return session.mode === "standalone"
    ? `standalone:${session.user_id}`
    : `${session.apiBase}:${session.user_id}`;
}

function encodeBase64(bytes) {
  return btoa(String.fromCharCode(...new Uint8Array(bytes)));
}

function readProductImage(file) {
  if (!file) return Promise.resolve("");
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error || new Error("Could not read product image."));
    reader.readAsDataURL(file);
  });
}

function readImageBlob(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error || new Error("Could not cache product image."));
    reader.readAsDataURL(blob);
  });
}

async function cacheCatalogImages(serverProducts) {
  const cachedProducts = await getProducts();
  const cachedImages = new Map(
    cachedProducts
      .filter((product) => product.image_data && product.image_url)
      .map((product) => [product.id, product]),
  );
  let failedImages = 0;
  const productsWithImages = await Promise.all(serverProducts.map(async (product) => {
    if (!product.image_url) return product;
    const cached = cachedImages.get(product.id);
    if (cached?.image_url === product.image_url) {
      return { ...product, image_data: cached.image_data };
    }
    try {
      const imageUrl = new URL(product.image_url, session.apiBase);
      if (imageUrl.origin !== new URL(session.apiBase).origin) return product;
      const response = await fetch(imageUrl, { credentials: "omit" });
      if (!response.ok) throw new Error(`Image request failed (${response.status}).`);
      const image = await response.blob();
      if (image.size > 5 * 1024 * 1024) {
        throw new Error("Image exceeds the 5 MB offline cache limit.");
      }
      return { ...product, image_data: await readImageBlob(image) };
    } catch (error) {
      failedImages += 1;
      console.warn(`Could not cache the image for ${product.name}: ${error.message}`);
      return product;
    }
  }));
  return { products: productsWithImages, failedImages };
}

async function hashLocalPassword(password, salt) {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(password),
    "PBKDF2",
    false,
    ["deriveBits"],
  );
  const derived = await crypto.subtle.deriveBits(
    {
      name: "PBKDF2",
      salt,
      iterations: 310000,
      hash: "SHA-256",
    },
    key,
    256,
  );
  return encodeBase64(derived);
}

function setLocalSetupVisible(visible) {
  loginPanel.classList.toggle("hidden", visible);
  localSetupPanel.classList.toggle("hidden", !visible);
  if (visible) $("#local-setup-username").focus();
}

async function refreshLocalData() {
  products = await getLocalProducts();
  const localCategories = await getLocalCategories();
  await saveSetting(`local-categories:${ownerKey()}`, localCategories);
  customers = [];
  renderCustomers();
}

async function renderLocalCategoryOptions() {
  if (session?.mode !== "standalone") return;
  const categories = await getLocalCategories();
  const options = categories.map((category) => (
    `<option value="${category.id}">${escapeHtml(category.name)}</option>`
  )).join("");
  $("#local-product-category").innerHTML = '<option value="">No category</option>' + options;
}

async function renderLocalReport() {
  if (session?.mode !== "standalone") return;
  const startDate = $("#local-report-start").value;
  const endDate = $("#local-report-end").value;
  const sales = (await currentOperations()).filter(
    (operation) => operation.type === "sale" &&
      operation.status === "local" &&
      (!startDate || localDateKey(operation.created_at) >= startDate) &&
      (!endDate || localDateKey(operation.created_at) <= endDate),
  );
  const total = sales.reduce((sum, sale) => sum + Number(sale.total_amount), 0);
  const units = sales.reduce(
    (sum, sale) => sum + sale.data.items.reduce((count, item) => count + item.quantity, 0),
    0,
  );
  const costKnown = sales.every((sale) => Array.isArray(sale.receipt_lines) &&
    sale.receipt_lines.every(
      (line) => Number.isFinite(Number(line.unit_cost)),
    ));
  const costOfGoods = sales.reduce((sum, sale) => sum + (sale.receipt_lines || []).reduce(
    (lineSum, line) => lineSum + Number(line.unit_cost || 0) * Number(line.quantity),
    0,
  ), 0);
  const totalsByPayment = new Map();
  sales.forEach((sale) => {
    const method = sale.data.payment_method;
    totalsByPayment.set(method, (totalsByPayment.get(method) || 0) + Number(sale.total_amount));
  });
  const paymentRows = ["till_number", "paybill", "send_money", "cash"].map((method) => `
    <tr><td>${escapeHtml(paymentLabel(method))}</td><td>KSh ${(totalsByPayment.get(method) || 0).toFixed(2)}</td></tr>
  `).join("");
  $("#local-report").innerHTML = `
    <p><strong>${sales.length}</strong> sales · <strong>${units}</strong> units · Revenue <strong>KSh ${total.toFixed(2)}</strong></p>
    <p>Cost of goods: KSh ${costOfGoods.toFixed(2)} · ${costKnown ? "Profit" : "Known-cost profit"}: KSh ${(total - costOfGoods).toFixed(2)}</p>
    ${costKnown ? "" : '<p class="queue-error">Some older local sales do not have cost snapshots; profit is incomplete.</p>'}
    <div class="table-responsive"><table><thead><tr><th>Payment method</th><th>Total</th></tr></thead><tbody>
      ${paymentRows || '<tr><td colspan="2">No sales in this date range.</td></tr>'}
    </tbody></table></div>`;
}

function localDateKey(timestamp) {
  const date = new Date(timestamp);
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${day}`;
}

function paymentLabel(method) {
  return {
    cash: "CASH",
    till_number: "TILL NUMBER",
    paybill: "PAYBILL",
    send_money: "SEND MONEY",
    mpesa: "M-Pesa",
    card: "Card",
  }[method] || method;
}

async function renderOpenTabs() {
  const tabs = await getOpenTabs(ownerKey());
  $("#open-tabs-list").innerHTML = tabs.map((tab) => `
    <li>
      <span>${escapeHtml(tab.name)} · ${tab.cart.length} item type(s) · ${new Date(tab.updated_at).toLocaleString()}${tab.id === activeTabId ? " · Active" : ""}</span>
      <span><button type="button" data-resume-tab="${escapeHtml(tab.id)}">Resume</button>
      <button type="button" data-delete-tab="${escapeHtml(tab.id)}">Delete</button></span>
    </li>
  `).join("") || '<li class="muted">No open tabs.</li>';
}

async function createLocalSession(username, displayName) {
  session = {
    mode: "standalone",
    user_id: username.toLowerCase(),
    username,
    display_name: displayName,
    role: "admin",
    can_adjust_stock: true,
    apiBase: "",
  };
  await saveSession(session);
  await refreshLocalData();
  setSessionView();
  await renderLocalReport();
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  })[character]);
}

function showMessage(element, message, isError = false) {
  element.textContent = message;
  element.classList.toggle("queue-error", isError);
}

async function scanBarcode(code) {
  const normalized = code.trim().toLowerCase();
  const product = products.find((item) => (
    item.sku.toLowerCase() === normalized ||
    String(item.barcode || "").toLowerCase() === normalized
  ));
  if (!product) {
    showMessage(appMessage, `No product matches barcode ${code}.`, true);
    return;
  }
  const item = cart.get(product.id) || { product, quantity: 0 };
  const availableStock = effectiveStock(product, await currentOperations());
  if (!product.is_service && availableStock <= item.quantity) {
    showMessage(appMessage, `${product.name} is out of stock.`, true);
    return;
  }
  item.quantity += 1;
  cart.set(product.id, item);
  showMessage(
    appMessage,
    !product.is_service && availableStock <= Number(product.low_stock_threshold ?? 5)
      ? `Scanned ${product.name}. Low stock: ${availableStock} remaining.`
      : `Scanned ${product.name}.`,
  );
  renderAll();
}

let barcodeBuffer = "";
let lastBarcodeKeyAt = 0;
let barcodeIsRapid = true;
document.addEventListener("keydown", (event) => {
  if (posPanel.classList.contains("hidden")) return;
  const target = event.target;
  if (target instanceof HTMLInputElement && target.id !== "product-search") {
    barcodeBuffer = "";
    return;
  }
  const now = Date.now();
  if (event.key === "Enter") {
    if (barcodeBuffer.length >= 3 && barcodeIsRapid && now - lastBarcodeKeyAt < 180) {
      event.preventDefault();
      scanBarcode(barcodeBuffer);
    }
    barcodeBuffer = "";
    barcodeIsRapid = true;
    return;
  }
  if (event.key.length !== 1 || event.ctrlKey || event.altKey || event.metaKey) return;
  if (!barcodeBuffer || now - lastBarcodeKeyAt > 250) {
    barcodeBuffer = "";
    barcodeIsRapid = true;
  } else if (now - lastBarcodeKeyAt > 100) {
    barcodeIsRapid = false;
  }
  barcodeBuffer += event.key;
  lastBarcodeKeyAt = now;
}, true);

["local-product-barcode", "local-restock-barcode"].forEach((id) => {
  $(`#${id}`).addEventListener("keydown", (event) => {
    if (event.key === "Enter") event.preventDefault();
  });
});

function setSessionView() {
  loginPanel.classList.add("hidden");
  localSetupPanel.classList.add("hidden");
  posPanel.classList.remove("hidden");
  const standalone = session.mode === "standalone";
  restockPanel.classList.toggle("hidden", standalone || !session.can_adjust_stock);
  localManagementPanel.classList.toggle("hidden", !standalone);
  $("#sync-button").classList.toggle("hidden", standalone);
  $("#connection-status").classList.toggle("hidden", standalone);
  $(".queue-panel h2").textContent = standalone ? "Local sales and stock history" : "Pending Changes";
  $(".queue-panel .muted").textContent = standalone
    ? "Saved on this device. Back up this device data regularly."
    : "Sales and restocks sync automatically when a connection returns.";
  $("#username").value = session.username;
  apiBaseInput.value = session.apiBase || "";
  renderAll();
  updateConnectionStatus();
}

async function loadSession() {
  const saved = await SecureStorage.get("chiwas-pos-session");
  return saved && typeof saved === "object" ? saved : null;
}

async function saveSession(nextSession) {
  session = nextSession;
  await SecureStorage.set("chiwas-pos-session", session);
}

async function clearSession() {
  await SecureStorage.remove("chiwas-pos-session");
  session = null;
}

async function apiRequest(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("Authorization", `Token ${session.token}`);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${session.apiBase}${path}`, {
    ...options,
    headers,
  });
  const data = response.status === 204 ? null : await response.json();
  if (!response.ok) {
    const error = new Error(data?.detail || `Request failed (${response.status}).`);
    error.status = response.status;
    throw error;
  }
  return data;
}

async function refreshCatalog() {
  if (!session || session.mode === "standalone" || !isOnline()) return;
  try {
    const response = await apiRequest("/api/pos/catalog/");
    const imageCache = await cacheCatalogImages(response.products);
    products = imageCache.products;
    customers = response.customers;
    await saveCatalog(products);
    await saveSetting(`catalog-customers:${ownerKey()}`, customers);
    renderCustomers();
    const refreshedAt = new Date().toISOString();
    await saveSetting(`catalog-updated:${ownerKey()}`, refreshedAt);
    $("#catalog-updated").textContent = `Updated ${new Date(refreshedAt).toLocaleString()}`;
    renderAll();
    if (imageCache.failedImages) {
      showMessage(
        appMessage,
        `Catalog updated, but ${imageCache.failedImages} product image(s) could not be cached for offline use.`,
        true,
      );
    }
  } catch (error) {
    if (error.status === 401) {
      showMessage(appMessage, "Session expired. Sign in again online to sync.", true);
    } else if (isOnline()) {
      showMessage(appMessage, `Inventory refresh failed: ${error.message}`, true);
    }
  }
}

function filteredOperations(operations) {
  return operations
    .filter((operation) => operation.owner_key === ownerKey())
    .sort((left, right) => Date.parse(left.created_at) - Date.parse(right.created_at));
}

async function currentOperations() {
  return filteredOperations(await getOperations());
}

function effectiveStock(product, operations) {
  return operations
    .filter((operation) => ["pending", "syncing", "local"].includes(operation.status))
    .reduce((stock, operation) => {
      if (operation.type === "sale") {
        const sold = operation.data.items
          .filter((item) => item.product_id === product.id)
          .reduce((sum, item) => sum + item.quantity, 0);
        return stock - sold;
      }
      if (
        operation.type === "restock" &&
        operation.data.product_id === product.id
      ) {
        return stock + operation.data.quantity;
      }
      return stock;
    }, Number(product.stock_quantity));
}

async function renderProducts() {
  const query = $("#product-search").value.trim().toLowerCase();
  const operations = await currentOperations();
  const visibleProducts = products.filter((product) => (
    !query ||
    product.name.toLowerCase().includes(query) ||
    product.sku.toLowerCase().includes(query) ||
    String(product.barcode || "").toLowerCase().includes(query)
  ));

  const productCards = visibleProducts.map((product) => {
    const availableStock = effectiveStock(product, operations);
    const stock = product.is_service ? "Service" : `${availableStock} in stock`;
    const lowStock = !product.is_service && availableStock <= Number(product.low_stock_threshold ?? 5);
    const stockBadge = !product.is_service && availableStock === 0
      ? '<span class="status-pill disconnected">OUT OF STOCK</span>'
      : lowStock
        ? '<span class="status-pill low-stock">LOW STOCK</span>'
        : "";
    const price = Number(product.retail_price).toFixed(2);
    const size = product.bottle_size ? ` · ${escapeHtml(product.bottle_size)}` : "";
    const caseInfo = product.case_price
      ? `<div class="product-meta">Case of ${Number(product.units_per_case)} · KSh ${Number(product.case_price).toFixed(2)}</div>`
      : "";
    const productImage = product.image_data || product.image_url;
    return `
      <article class="product-card">
        ${productImage ? `<img class="product-thumbnail" src="${escapeHtml(productImage)}" alt="${escapeHtml(product.name)}" loading="lazy">` : ""}
        <h3>${escapeHtml(product.name)}</h3>
        <div class="product-meta">${escapeHtml(product.sku)}${size}<br>${escapeHtml(product.category_name || "")}<br>${escapeHtml(stock)} ${stockBadge}</div>
        ${caseInfo}
        <div class="product-bottom">
          <span class="product-price">KSh ${price}</span>
          <button type="button" data-add-product="${product.id}" ${!product.is_service && availableStock <= 0 ? "disabled" : ""}>Add</button>
        </div>
      </article>`;
  });
  productList.innerHTML = productCards.join("") || '<p class="muted">No products match your search.</p>';
}

function selectedPrice(product) {
  return Number(
    $("#price-type").value === "wholesale"
      ? product.wholesale_price
      : product.retail_price,
  );
}

function updateCartCount() {
  const count = [...cart.values()].reduce((total, item) => total + item.quantity, 0);
  cartCount.textContent = `${count} item${count === 1 ? "" : "s"}`;
  completeSale.disabled = cart.size === 0;
}

function renderCart() {
  const entries = [...cart.values()];
  cartList.innerHTML = entries.map(({ product, quantity }) => `
    <div class="cart-row">
      <strong>${escapeHtml(product.name)}</strong>
      <strong>KSh ${(selectedPrice(product) * quantity).toFixed(2)}</strong>
      <small>${quantity} × KSh ${selectedPrice(product).toFixed(2)}</small>
      <div class="quantity-controls">
        <button type="button" data-quantity-change="${product.id}" data-change="-1" aria-label="Decrease quantity">−</button>
        <span>${quantity}</span>
        <button type="button" data-quantity-change="${product.id}" data-change="1" aria-label="Increase quantity">+</button>
        <button type="button" class="remove" data-remove-product="${product.id}">Remove</button>
      </div>
    </div>`).join("") || '<p class="muted">Add products from the inventory.</p>';

  const subtotal = entries.reduce(
    (total, item) => total + selectedPrice(item.product) * item.quantity,
    0,
  );
  const discount = Math.max(0, Number($("#discount").value) || 0);
  $("#sale-total").textContent = Math.max(0, subtotal - discount).toFixed(2);
  updateCashChange();
  updateCartCount();
}

function renderPaymentFields() {
  const fields = {
    cash: [
      ["amount_tendered", "Amount Tendered (KSh)", true, "number"],
    ],
    till_number: [
      ["till_number", "Till Number", true, "text"],
      ["transaction_code", "M-Pesa Ref (optional)", false, "text"],
      ["payer_name", "Payer Name (optional)", false, "text"],
    ],
    paybill: [
      ["paybill_number", "Business/Paybill Number", true, "text"],
      ["account_number", "Account Number", true, "text"],
    ],
    send_money: [
      ["phone_number", "Phone Number", true, "tel"],
      ["transaction_code", "M-Pesa Ref (optional)", false, "text"],
    ],
  }[paymentMethod.value] || [];

  paymentFields.innerHTML = fields.map(([name, label, required, type]) => `
    <label for="payment-${name}">${label}</label>
    <input id="payment-${name}" name="${name}" type="${type}" ${type === "number" ? 'min="0" step="0.01"' : ""} ${required ? "required" : ""} />`
  ).join("");
  if (paymentMethod.value === "cash") {
    paymentFields.insertAdjacentHTML(
      "beforeend",
      '<p class="small">Change Due: KSh <strong id="cash-change">0.00</strong></p>',
    );
    $("#payment-amount_tendered").addEventListener("input", updateCashChange);
  }
}

function updateCashChange() {
  const tenderedInput = $("#payment-amount_tendered");
  const changeOutput = $("#cash-change");
  if (!tenderedInput || !changeOutput) return;
  const tendered = Number(tenderedInput.value);
  const due = Number($("#sale-total").textContent);
  changeOutput.textContent = Number.isFinite(tendered)
    ? Math.max(0, tendered - due).toFixed(2)
    : "0.00";
}

function renderCustomers() {
  customerSelect.innerHTML = '<option value="">Walk-in Customer</option>' +
    customers.map((customer) => (
      `<option value="${customer.id}">${escapeHtml(customer.name)}${customer.phone ? ` · ${escapeHtml(customer.phone)}` : ""}</option>`
    )).join("");
}

function renderRestockProducts() {
  const options = products
    .filter((product) => !product.is_service)
    .map((product) => `<option value="${product.id}">${escapeHtml(product.name)} · ${escapeHtml(product.sku)}</option>`)
    .join("");
  $("#restock-product").innerHTML = options || '<option value="">No stock products available</option>';
}

$("#local-category-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = $("#local-category-name").value.trim();
  const categories = await getLocalCategories();
  if (categories.some((category) => category.name.toLowerCase() === name.toLowerCase())) {
    showMessage(appMessage, "That local category already exists.", true);
    return;
  }
  await saveLocalCategory({ name, created_at: new Date().toISOString() });
  $("#local-category-form").reset();
  await renderLocalCategoryOptions();
  showMessage(appMessage, `Category "${name}" saved on this device.`);
});

$("#local-product-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const barcode = $("#local-product-barcode").value.trim();
  const existing = await getLocalProducts();
  if (existing.some((product) => product.sku.toLowerCase() === barcode.toLowerCase())) {
    showMessage(appMessage, "That barcode / SKU is already assigned to a product.", true);
    return;
  }
  const categoryId = $("#local-product-category").value
    ? Number($("#local-product-category").value)
    : null;
  const categories = await getLocalCategories();
  const category = categories.find((item) => item.id === categoryId);
  const product = {
    name: $("#local-product-name").value.trim(),
    sku: barcode,
    barcode,
    category_id: categoryId,
    category_name: category?.name || "",
    image_data: await readProductImage($("#local-product-image").files[0]),
    cost_price: Number($("#local-product-cost").value),
    retail_price: Number($("#local-product-retail").value),
    wholesale_price: Number($("#local-product-wholesale").value),
    bottle_size: $("#local-product-size").value,
    units_per_case: Number($("#local-product-case-units").value),
    case_price: $("#local-product-case-price").value
      ? Number($("#local-product-case-price").value)
      : null,
    stock_quantity: Number($("#local-product-stock").value),
    low_stock_threshold: Number($("#local-product-threshold").value),
    is_service: false,
    bottle_size: "",
    units_per_case: 1,
    case_price: null,
    created_at: new Date().toISOString(),
  };
  if (
    !product.name ||
    !barcode ||
    ![product.cost_price, product.retail_price, product.wholesale_price].every(Number.isFinite) ||
    !Number.isInteger(product.units_per_case) ||
    product.units_per_case < 1 ||
    (product.case_price !== null && (!Number.isFinite(product.case_price) || product.case_price < 0)) ||
    !Number.isInteger(product.stock_quantity) ||
    product.stock_quantity < 0 ||
    !Number.isInteger(product.low_stock_threshold) ||
    product.low_stock_threshold < 0
  ) {
    showMessage(appMessage, "Enter a name, unique barcode, valid prices, and non-negative whole-number stock values.", true);
    return;
  }
  try {
    await saveLocalProduct(product);
    products = await getLocalProducts();
    $("#local-product-form").reset();
    $("#local-product-cost").value = "0";
    $("#local-product-stock").value = "0";
    $("#local-product-threshold").value = "5";
    $("#local-product-case-units").value = "1";
    await renderAll();
    showMessage(appMessage, `${product.name} saved to this device.`);
  } catch (error) {
    showMessage(appMessage, `Could not save product: ${error.message}`, true);
  }
});

$("#local-restock-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const barcode = $("#local-restock-barcode").value.trim().toLowerCase();
  const quantity = Number($("#local-restock-quantity").value);
  const product = products.find((item) => (
    item.sku.toLowerCase() === barcode ||
    String(item.barcode || "").toLowerCase() === barcode
  ));
  if (!product || !Number.isInteger(quantity) || quantity < 1) {
    showMessage(appMessage, "Scan a known product barcode and enter a positive whole-number quantity.", true);
    return;
  }
  await saveOperation({
    id: crypto.randomUUID(),
    type: "restock",
    status: "local",
    owner_key: ownerKey(),
    created_at: new Date().toISOString(),
    data: { product_id: product.id, quantity },
  });
  $("#local-restock-form").reset();
  await renderAll();
  showMessage(appMessage, `${quantity} units added to ${product.name} on this device.`);
});

$("#refresh-local-report").addEventListener("click", renderLocalReport);
$("#local-report-start").addEventListener("change", renderLocalReport);
$("#local-report-end").addEventListener("change", renderLocalReport);

$("#park-order").addEventListener("click", async () => {
  if (!cart.size) {
    showMessage(appMessage, "Add at least one item before parking this order.", true);
    return;
  }
  const name = $("#hold-tab-name").value.trim() ||
    $("#sale-customer-name").value.trim();
  if (!name) {
    showMessage(appMessage, "Enter a customer or table name to identify this tab.", true);
    $("#hold-tab-name").focus();
    return;
  }
  const tabs = await getOpenTabs(ownerKey());
  const tabId = activeTabId || crypto.randomUUID();
  const tab = {
    id: tabId,
    name,
    customer_name: $("#sale-customer-name").value.trim(),
    price_type: $("#price-type").value,
    discount: $("#discount").value,
    cart: [...cart.values()].map(({ product, quantity }) => ({
      product_id: product.id,
      quantity,
    })),
    updated_at: new Date().toISOString(),
  };
  const existingIndex = tabs.findIndex((entry) => entry.id === tabId);
  if (existingIndex >= 0) tabs[existingIndex] = tab;
  else tabs.push(tab);
  await saveOpenTabs(ownerKey(), tabs);
  activeTabId = null;
  cart = new Map();
  $("#sale-customer-name").value = "";
  $("#hold-tab-name").value = "";
  await renderAll();
  showMessage(appMessage, `Order parked for ${name}.`);
});

$("#open-tabs-list").addEventListener("click", async (event) => {
  const resumeButton = event.target.closest("[data-resume-tab]");
  const deleteButton = event.target.closest("[data-delete-tab]");
  const tabs = await getOpenTabs(ownerKey());
  if (deleteButton) {
    if (!window.confirm("Delete this open customer tab?")) return;
    await saveOpenTabs(ownerKey(), tabs.filter((tab) => tab.id !== deleteButton.dataset.deleteTab));
    if (activeTabId === deleteButton.dataset.deleteTab) activeTabId = null;
    await renderOpenTabs();
    return;
  }
  if (!resumeButton) return;
  const tab = tabs.find((entry) => entry.id === resumeButton.dataset.resumeTab);
  if (!tab) return;
  if (cart.size && !window.confirm("Replace the current cart with this saved tab? The current cart will be cleared.")) return;
  const restoredCart = new Map();
  const operations = await currentOperations();
  for (const tabItem of tab.cart) {
    const product = products.find((candidate) => candidate.id === tabItem.product_id);
    if (!product) {
      showMessage(appMessage, "A product in this tab is no longer in the cached inventory.", true);
      return;
    }
    if (!product.is_service && effectiveStock(product, operations) < tabItem.quantity) {
      showMessage(appMessage, `Not enough current stock to resume ${tab.name}: ${product.name}.`, true);
      return;
    }
    restoredCart.set(product.id, { product, quantity: tabItem.quantity });
  }
  cart = restoredCart;
  activeTabId = tab.id;
  $("#hold-tab-name").value = tab.name;
  $("#sale-customer-name").value = tab.customer_name || tab.name;
  $("#price-type").value = tab.price_type || "retail";
  $("#discount").value = tab.discount || "0";
  await renderAll();
  showMessage(appMessage, `Resumed tab for ${tab.name}.`);
});

$("#export-local-report").addEventListener("click", async () => {
  const sales = (await currentOperations()).filter(
    (operation) => operation.type === "sale" && operation.status === "local",
  );
  const rows = [["Date", "Customer", "Payment", "Total", "Items"]];
  sales.forEach((sale) => {
    const count = sale.data.items.reduce((total, item) => total + item.quantity, 0);
    rows.push([
      new Date(sale.created_at).toLocaleString(),
      sale.data.customer_name || "Walk-in Customer",
      sale.data.payment_method,
      Number(sale.total_amount).toFixed(2),
      String(count),
    ]);
  });
  const csv = rows.map((row) => row.map((value) => (
    `"${String(value).replaceAll('"', '""')}"`
  )).join(",")).join("\r\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const download = document.createElement("a");
  download.href = url;
  download.download = "chiwas-local-sales.csv";
  download.click();
  URL.revokeObjectURL(url);
});

function downloadJsonBackup(backup) {
  const contents = JSON.stringify(backup, null, 2);
  const url = URL.createObjectURL(new Blob([contents], { type: "application/json" }));
  const download = document.createElement("a");
  download.href = url;
  download.download = `chiwas-pos-backup-${new Date().toISOString().slice(0, 10)}.json`;
  download.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function parseCsvRows(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const character = text[index];
    if (quoted && character === '"' && text[index + 1] === '"') {
      field += '"';
      index += 1;
    } else if (character === '"') {
      quoted = !quoted;
    } else if (!quoted && character === ",") {
      row.push(field);
      field = "";
    } else if (!quoted && (character === "\n" || character === "\r")) {
      if (character === "\r" && text[index + 1] === "\n") index += 1;
      row.push(field);
      if (row.some((value) => value !== "")) rows.push(row);
      row = [];
      field = "";
    } else {
      field += character;
    }
  }
  if (quoted) throw new Error("CSV backup has an unterminated quoted value.");
  row.push(field);
  if (row.some((value) => value !== "")) rows.push(row);
  return rows;
}

function parseCsvBackup(text) {
  const rows = parseCsvRows(text);
  if (rows[0]?.[0] !== "collection" || rows[0]?.[1] !== "record_json") {
    throw new Error("CSV backup must start with collection,record_json.");
  }
  const collections = {
    categories: [],
    products: [],
    catalog_products: [],
    operations: [],
    open_tabs: [],
  };
  for (const [collection, recordJson] of rows.slice(1)) {
    if (!Object.hasOwn(collections, collection)) {
      throw new Error(`Unsupported CSV backup collection: ${collection}`);
    }
    collections[collection].push(JSON.parse(recordJson));
  }
  return {
    format: "chiwas-pos-backup",
    version: 1,
    ...collections,
  };
}

$("#export-local-backup").addEventListener("click", async () => {
  const [categories, localProducts, catalogProducts, operations, openTabs] = await Promise.all([
    getLocalCategories(),
    getLocalProducts(),
    getProducts(),
    currentOperations(),
    getOpenTabs(ownerKey()),
  ]);
  downloadJsonBackup({
    format: "chiwas-pos-backup",
    version: 1,
    exported_at: new Date().toISOString(),
    categories,
    products: localProducts,
    catalog_products: catalogProducts,
    operations,
    open_tabs: openTabs,
  });
  showMessage(appMessage, "JSON backup downloaded. Keep it somewhere safe.");
});

$("#export-local-csv-backup").addEventListener("click", async () => {
  const [categories, localProducts, catalogProducts, operations, openTabs] = await Promise.all([
    getLocalCategories(),
    getLocalProducts(),
    getProducts(),
    currentOperations(),
    getOpenTabs(ownerKey()),
  ]);
  const collections = {
    categories,
    products: localProducts,
    catalog_products: catalogProducts,
    operations,
    open_tabs: openTabs,
  };
  const rows = [["collection", "record_json"]];
  Object.entries(collections).forEach(([collection, records]) => {
    records.forEach((record) => rows.push([collection, JSON.stringify(record)]));
  });
  const csv = rows.map((row) => row.map((value) => (
    `"${String(value).replaceAll('"', '""')}"`
  )).join(",")).join("\r\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8" }));
  const download = document.createElement("a");
  download.href = url;
  download.download = `chiwas-pos-backup-${new Date().toISOString().slice(0, 10)}.csv`;
  download.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  showMessage(appMessage, "CSV backup downloaded. Keep it somewhere safe.");
});

$("#import-local-backup").addEventListener("click", () => {
  $("#import-local-backup-file").click();
});

$("#import-local-csv-backup").addEventListener("click", () => {
  $("#import-local-backup-file").click();
});

$("#import-local-backup-file").addEventListener("change", async (event) => {
  const [file] = event.target.files || [];
  event.target.value = "";
  if (!file) return;
  if (file.size > 25 * 1024 * 1024) {
    showMessage(appMessage, "Backup exceeds the 25 MB import limit.", true);
    return;
  }
  if (!window.confirm("Restore this backup? It will replace the current local categories, products, sales, stock operations, and open tabs on this device.")) return;

  try {
    const contents = await file.text();
    const backup = file.name.toLowerCase().endsWith(".csv")
      ? parseCsvBackup(contents)
      : JSON.parse(contents);
    const collections = ["categories", "products", "catalog_products", "operations"];
    if (
      backup?.format !== "chiwas-pos-backup" ||
      backup.version !== 1 ||
      !collections.every((key) => Array.isArray(backup[key])) ||
      collections.some((key) => backup[key].length > 10000)
    ) {
      throw new Error("This file is not a supported Chiwas POS backup.");
    }
    if (backup.categories.some((category) => !category || typeof category.name !== "string")) {
      throw new Error("Backup contains an invalid category.");
    }
    const allProducts = [...backup.products, ...backup.catalog_products];
    if (allProducts.some((product) => (
      !product ||
      !Number.isInteger(Number(product.id)) ||
      typeof product.name !== "string" ||
      typeof product.sku !== "string" ||
      !Number.isFinite(Number(product.stock_quantity))
    ))) {
      throw new Error("Backup contains an invalid product.");
    }
    if (backup.operations.some((operation) => (
      !operation ||
      typeof operation.id !== "string" ||
      !["sale", "restock"].includes(operation.type) ||
      !operation.data ||
      typeof operation.data !== "object"
    ))) {
      throw new Error("Backup contains an invalid sale or stock operation.");
    }
    if (backup.open_tabs !== undefined && (
      !Array.isArray(backup.open_tabs) ||
      backup.open_tabs.length > 10000 ||
      backup.open_tabs.some((tab) => (
        !tab ||
        typeof tab.id !== "string" ||
        typeof tab.name !== "string" ||
        !Array.isArray(tab.cart)
      ))
    )) {
      throw new Error("Backup contains an invalid open customer tab.");
    }

    const restoredOperations = backup.operations.map((operation) => {
      const { error, ...restoredOperation } = operation;
      return {
        ...restoredOperation,
        owner_key: ownerKey(),
        status: "local",
      };
    });
    await replaceLocalBackup({
      ...backup,
      operations: restoredOperations,
    });
    await saveOpenTabs(ownerKey(), (backup.open_tabs || []).map((tab) => ({
      ...tab,
      owner_key: ownerKey(),
    })));
    await refreshCachedProducts();
    await renderAll();
    showMessage(appMessage, `Backup restored: ${backup.products.length} local products and ${restoredOperations.length} operations.`);
  } catch (error) {
    showMessage(appMessage, `Backup restore failed: ${error.message}`, true);
  }
});

async function renderQueue() {
  const operations = await currentOperations();
  const pending = operations.filter((operation) => operation.status === "pending").length;
  queueCount.textContent = session.mode === "standalone"
    ? `${operations.length} saved`
    : `${pending} pending`;
  queueList.innerHTML = operations.map((operation) => {
    const label = operation.type === "sale" ? "Sale" : "Restock";
    const state = operation.status === "rejected"
      ? `<span class="queue-error">${escapeHtml(operation.error)}</span>`
      : `<span>${operation.status === "local" ? "Saved on device" : escapeHtml(operation.status)}</span>`;
    const controls = operation.status === "rejected"
      ? `<button type="button" data-retry-operation="${operation.id}">Retry</button>
         <button type="button" data-discard-operation="${operation.id}">Discard</button>`
      : "";
    return `<li><span>${label} · ${new Date(operation.created_at).toLocaleString()}</span><span>${state} ${controls}</span></li>`;
  }).join("") || '<li class="muted">No queued operations.</li>';
}

async function renderAll() {
  await Promise.all([renderProducts(), renderQueue()]);
  renderRestockProducts();
  renderCart();
  await renderLocalCategoryOptions();
  await renderLocalReport();
  await renderOpenTabs();
}

function updateConnectionStatus() {
  const pill = $("#connection-status");
  if (session?.mode === "standalone") {
    pill.textContent = "Standalone on this device";
    pill.classList.add("disconnected");
    return;
  }
  const online = isOnline();
  pill.textContent = online ? "Connected" : "No connection";
  pill.classList.toggle("disconnected", !online);
  if (session && !online) {
    $("#catalog-updated").textContent ||= "Using locally cached inventory.";
  }
}

async function syncQueue() {
  if (!session || session.mode === "standalone" || !isOnline() || queueIsSyncing) return;
  const pendingOperations = (await currentOperations())
    .filter((operation) => operation.status === "pending");
  const operations = pendingOperations.slice(0, 100);
  if (!operations.length) {
    showMessage(appMessage, "No pending operations to sync.");
    return;
  }

  queueIsSyncing = true;
  let syncMore = false;
  await Promise.all(operations.map((operation) => {
    operation.status = "syncing";
    return saveOperation(operation);
  }));
  await renderQueue();
  try {
    const response = await apiRequest("/api/pos/sync/", {
      method: "POST",
      body: JSON.stringify({
        operations: operations.map(({ id, type, data }) => ({ id, type, data })),
      }),
    });
    const returnedIds = new Set(response.results.map((result) => result.id));
    syncMore = pendingOperations.length > operations.length &&
      operations.every((operation) => returnedIds.has(operation.id));
    for (const result of response.results) {
      const operation = operations.find((queued) => queued.id === result.id);
      if (!operation) continue;
      if (result.status === "synced") {
        await removeOperation(operation.id);
        const receiptStatus = receiptPanel.querySelector("[data-receipt-operation]");
        if (receiptStatus?.dataset.receiptOperation === operation.id) {
          receiptStatus.textContent = result.invoice_id
            ? `SALE SYNCED · INVOICE #${result.invoice_id}`
            : "RESTOCK SYNCED";
        }
      } else {
        operation.status = "rejected";
        operation.error = result.error;
        await saveOperation(operation);
      }
    }
    await Promise.all(operations
      .filter((operation) => !returnedIds.has(operation.id))
      .map((operation) => {
        operation.status = "pending";
        return saveOperation(operation);
      }));
    const succeeded = response.results.filter((result) => result.status === "synced").length;
    const rejected = response.results.length - succeeded;
    showMessage(
      appMessage,
      `${succeeded} operation${succeeded === 1 ? "" : "s"} synced${rejected ? `; ${rejected} need attention` : ""}.`,
      rejected > 0,
    );
    await refreshCatalog();
  } catch (error) {
    await Promise.all(operations.map((operation) => {
      operation.status = "pending";
      return saveOperation(operation);
    }));
    showMessage(appMessage, `Sync not completed: ${error.message}. Operations remain on this device.`, true);
  } finally {
    queueIsSyncing = false;
    await renderAll();
    if (syncMore && isOnline()) await syncQueue();
  }
}

function makeReceipt(operation, cashier) {
  const items = operation.receipt_lines.map((item) => (
    `<tr><td>${escapeHtml(item.name)}<br>${item.quantity} × KSh ${item.unit_price.toFixed(2)}</td><td>KSh ${item.line_total.toFixed(2)}</td></tr>`
  )).join("");
  const paymentDetails = {
    till_number: `Till: ${escapeHtml(operation.data.till_number)}${operation.data.transaction_code ? ` | M-Pesa Ref: ${escapeHtml(operation.data.transaction_code)}` : ""}${operation.data.payer_name ? ` | Payer: ${escapeHtml(operation.data.payer_name)}` : ""}`,
    paybill: `Paybill No: ${escapeHtml(operation.data.paybill_number)} | Acc No: ${escapeHtml(operation.data.account_number)}`,
    send_money: `Phone: ${escapeHtml(operation.data.phone_number)}${operation.data.transaction_code ? ` | M-Pesa Ref: ${escapeHtml(operation.data.transaction_code)}` : ""}`,
  }[operation.data.payment_method] || "";

  const saleRecordStatus = operation.status === "local"
    ? "SALE RECORDED ON THIS DEVICE"
    : "SALE PENDING SYNC";
  receiptPanel.innerHTML = `
    <img class="receipt-logo" src="${logoPath}" alt="CHIWAS LIQUOR STORE &amp; RESTAURANT">
    <p>OPPOSITE QUICKMART</p>
    <p data-receipt-operation="${operation.id}">${saleRecordStatus}<br>Reference ${operation.id}</p>
    <hr>
    <table>${items}</table>
    <hr>
    <p>Customer: ${escapeHtml(operation.data.customer_name || customers.find(customer => customer.id === Number(operation.data.customer_id))?.name || "Walk-in Customer")}</p>
    <p>Payment Mode: ${escapeHtml(operation.data.payment_method.replaceAll("_", " ").toUpperCase())}<br>${paymentDetails}</p>
    <p>Total: KSh ${Number(operation.total_amount).toFixed(2)}</p>
    ${operation.data.payment_method === "cash" ? `<p>Tendered: KSh ${Number(operation.data.amount_tendered).toFixed(2)}<br>Change: KSh ${(Number(operation.data.amount_tendered) - Number(operation.total_amount)).toFixed(2)}</p>` : ""}
    <hr>
    <p>Cashier: ${escapeHtml(cashier)}<br>${new Date(operation.created_at).toLocaleString()}<br>Thank you for your business!</p>
    <label class="receipt-width-control" for="receipt-width">Paper width
      <select id="receipt-width"><option value="80">80 mm</option><option value="58">58 mm</option></select>
    </label>
    <button type="button" id="print-receipt">Print receipt</button>
    <button type="button" id="close-receipt">Back to POS</button>`;
  receiptPanel.classList.remove("hidden");
  $("#receipt-width").addEventListener("change", (event) => {
    receiptPanel.classList.toggle("paper-58", event.target.value === "58");
  });
  $("#print-receipt").addEventListener("click", () => window.print());
  $("#close-receipt").addEventListener("click", () => receiptPanel.classList.add("hidden"));
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  loginMessage.textContent = "";
  if (loginMode.value === "standalone") {
    const username = $("#username").value.trim().toLowerCase();
    const user = await getLocalUser(username);
    if (!user) {
      showMessage(loginMessage, "No local account was found. Use first-time setup on this device.", true);
      return;
    }
    const enteredHash = await hashLocalPassword(
      $("#password").value,
      new Uint8Array(user.salt),
    );
    if (enteredHash !== user.password_hash) {
      showMessage(loginMessage, "The local username or password is incorrect.", true);
      return;
    }
    $("#password").value = "";
    await createLocalSession(user.username, user.display_name);
    return;
  }
  const apiBase = normalizeApiBase(apiBaseInput.value);
  if (!apiBase) {
    showMessage(loginMessage, "Enter the HTTPS URL for the POS backend.", true);
    return;
  }
  let parsedApiBase;
  try {
    parsedApiBase = new URL(apiBase);
  } catch {
    showMessage(loginMessage, "Enter a valid backend URL.", true);
    return;
  }
  const localHost = ["localhost", "127.0.0.1"].includes(parsedApiBase.hostname);
  const trustedLan = parsedApiBase.protocol === "http:" && isTrustedLanHost(parsedApiBase.hostname);
  if (parsedApiBase.protocol !== "https:" && !localHost && !trustedLan) {
    showMessage(loginMessage, "Use HTTPS, or a trusted private-LAN server address.", true);
    return;
  }
  try {
    const response = await fetch(`${apiBase}/api/pos/login/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: $("#username").value.trim(),
        password: $("#password").value,
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Sign-in failed.");
    await saveSession({ ...data, apiBase, mode: "server" });
    $("#password").value = "";
    setSessionView();
    await refreshCatalog();
    await syncQueue();
  } catch (error) {
    showMessage(loginMessage, `Cannot sign in: ${error.message}`, true);
  }
});

loginMode.addEventListener("change", () => {
  const serverMode = loginMode.value === "server";
  $("#backend-url-field").classList.toggle("hidden", !serverMode);
  apiBaseInput.required = serverMode;
  $("#show-local-setup").classList.toggle("hidden", !serverMode);
  if (!serverMode) {
    loginPanel.querySelector("p.muted").textContent =
      "Standalone mode uses this device's local database and needs no server connection.";
  } else {
    loginPanel.querySelector("p.muted").textContent =
      "Sign in to manage inventory and sales on this device or connect to your store server.";
  }
});

$("#show-local-setup").addEventListener("click", async () => {
  loginMode.value = "standalone";
  loginMode.dispatchEvent(new Event("change"));
  if (await getLocalUserCount()) {
    showMessage(loginMessage, "A local owner account already exists on this device. Sign in to continue.", true);
    return;
  }
  setLocalSetupVisible(true);
});

$("#back-to-login").addEventListener("click", () => setLocalSetupVisible(false));

$("#local-setup-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const username = $("#local-setup-username").value.trim().toLowerCase();
  const displayName = $("#local-setup-name").value.trim();
  const password = $("#local-setup-password").value;
  const confirmation = $("#local-setup-confirm").value;
  if (username.length < 3 || !displayName) {
    showMessage($("#local-setup-message"), "Enter a username of at least 3 characters and your name.", true);
    return;
  }
  if (password.length < 10 || password !== confirmation) {
    showMessage($("#local-setup-message"), "Use a matching password of at least 10 characters.", true);
    return;
  }
  if (await getLocalUserCount()) {
    showMessage($("#local-setup-message"), "A local owner account already exists.", true);
    return;
  }
  try {
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const passwordHash = await hashLocalPassword(password, salt);
    await saveLocalUser({
      username,
      display_name: displayName,
      salt: Array.from(salt),
      password_hash: passwordHash,
      created_at: new Date().toISOString(),
    });
    for (const name of DEFAULT_CATEGORIES) {
      await saveLocalCategory({ name, created_at: new Date().toISOString() });
    }
    $("#local-setup-form").reset();
    await createLocalSession(username, displayName);
    showMessage(appMessage, "Standalone owner account created on this device.");
  } catch (error) {
    showMessage($("#local-setup-message"), `Could not create the local account: ${error.message}`, true);
  }
});

async function refreshCachedProducts() {
  products = session?.mode === "standalone"
    ? await getLocalProducts()
    : await getProducts();
}

$("#continue-saved-session").addEventListener("click", async () => {
  const savedSession = await loadSession();
  if (!savedSession) return;
  session = savedSession;
  await refreshCachedProducts();
  customers = await getSetting(`catalog-customers:${ownerKey()}`) || [];
  renderCustomers();
  setSessionView();
  const cachedAt = await getSetting(`catalog-updated:${ownerKey()}`);
  if (cachedAt) {
    $("#catalog-updated").textContent = `Cached ${new Date(cachedAt).toLocaleString()}`;
  }
});

productList.addEventListener("click", async (event) => {
  const button = event.target.closest("[data-add-product]");
  if (!button) return;
  const product = products.find((item) => item.id === Number(button.dataset.addProduct));
  if (!product) return;
  const stock = effectiveStock(product, await currentOperations());
  const currentQuantity = cart.get(product.id)?.quantity || 0;
  if (!product.is_service && stock <= currentQuantity) {
    showMessage(appMessage, `${product.name} has no available stock on this device.`, true);
    return;
  }
  const item = cart.get(product.id) || { product, quantity: 0 };
  item.quantity += 1;
  cart.set(product.id, item);
  await renderAll();
});

cartList.addEventListener("click", async (event) => {
  const removeButton = event.target.closest("[data-remove-product]");
  if (removeButton) {
    cart.delete(Number(removeButton.dataset.removeProduct));
    await renderAll();
    return;
  }
  const changeButton = event.target.closest("[data-quantity-change]");
  if (!changeButton) return;
  const id = Number(changeButton.dataset.quantityChange);
  const item = cart.get(id);
  if (!item) return;
  const nextQuantity = item.quantity + Number(changeButton.dataset.change);
  if (nextQuantity < 1) {
    cart.delete(id);
  } else {
    const stock = item.product.is_service
      ? Number.MAX_SAFE_INTEGER
      : effectiveStock(item.product, await currentOperations());
    item.quantity = Math.min(nextQuantity, stock);
    cart.set(id, item);
  }
  await renderAll();
});

$("#product-search").addEventListener("input", renderProducts);
$("#price-type").addEventListener("change", renderCart);
$("#discount").addEventListener("input", renderCart);
paymentMethod.addEventListener("change", renderPaymentFields);
customerSelect.addEventListener("change", () => {
  const customer = customers.find((item) => item.id === Number(customerSelect.value));
  if (customer) $("#sale-customer-name").value = customer.name;
});

saleForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!cart.size) return;
  const items = [...cart.values()].map(({ product, quantity }) => ({
    product_id: product.id,
    quantity,
  }));
  for (const item of items) {
    const product = products.find((candidate) => candidate.id === item.product_id);
    if (!product.is_service && effectiveStock(product, await currentOperations()) < item.quantity) {
      showMessage(appMessage, `Not enough cached stock for ${product.name}. Sync inventory before retrying.`, true);
      return;
    }
  }
  const formData = new FormData(saleForm);
  const paymentData = Object.fromEntries(formData.entries());
  const subtotal = [...cart.values()].reduce(
    (total, item) => total + selectedPrice(item.product) * item.quantity,
    0,
  );
  const discount = Number($("#discount").value) || 0;
  if (discount < 0 || discount > subtotal) {
    showMessage(appMessage, "Discount must be between zero and the sale subtotal.", true);
    return;
  }
  const totalAmount = Math.max(0, subtotal - discount);
  const customerName = $("#sale-customer-name").value.trim() ||
    customers.find((customer) => customer.id === Number(customerSelect.value))?.name || "";
  if (!customerName) {
    showMessage(appMessage, "Enter the customer name for the receipt.", true);
    $("#sale-customer-name").focus();
    return;
  }
  const tendered = paymentData.amount_tendered === undefined
    ? null
    : Number(paymentData.amount_tendered);
  if (paymentMethod.value === "cash" && (!Number.isFinite(tendered) || tendered < totalAmount)) {
    showMessage(appMessage, "Cash received must be at least the sale total.", true);
    return;
  }
  const operation = {
    id: crypto.randomUUID(),
    type: "sale",
    status: session.mode === "standalone" ? "local" : "pending",
    owner_key: ownerKey(),
    created_at: new Date().toISOString(),
    total_amount: totalAmount,
    receipt_lines: [...cart.values()].map(({ product, quantity }) => {
      const unitPrice = selectedPrice(product);
      return {
        name: product.name,
        quantity,
        unit_price: unitPrice,
        unit_cost: Number(product.cost_price),
        line_total: unitPrice * quantity,
      };
    }),
    data: {
      items,
      customer_id: customerSelect.value || "",
      customer_name: customerName,
      price_type: $("#price-type").value,
      discount: String(discount),
      payment_method: paymentMethod.value,
      till_number: paymentData.till_number || "",
      transaction_code: paymentData.transaction_code || "",
      payer_name: paymentData.payer_name || "",
      paybill_number: paymentData.paybill_number || "",
      account_number: paymentData.account_number || "",
      phone_number: paymentData.phone_number || "",
      amount_tendered: tendered,
    },
  };
  await saveOperation(operation);
  if (activeTabId) {
    const tabs = (await getOpenTabs(ownerKey())).filter((tab) => tab.id !== activeTabId);
    await saveOpenTabs(ownerKey(), tabs);
    activeTabId = null;
    $("#hold-tab-name").value = "";
  }
  makeReceipt(operation, session.display_name);
  cart = new Map();
  saleForm.reset();
  $("#discount").value = "0";
  $("#sale-customer-name").value = "";
  renderPaymentFields();
  await renderAll();
  showMessage(
    appMessage,
    session.mode === "standalone"
      ? "Sale recorded on this device. No server is required."
      : isOnline()
        ? "Sale saved locally; syncing now."
        : "Sale saved on this device. It will sync when you reconnect.",
  );
  if (session.mode !== "standalone" && isOnline()) await syncQueue();
});

restockForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const productId = Number($("#restock-product").value);
  const quantity = Number($("#restock-quantity").value);
  if (!session.can_adjust_stock || !productId || !Number.isInteger(quantity) || quantity <= 0) {
    showMessage(appMessage, "Choose a product and a positive whole-number quantity.", true);
    return;
  }
  await saveOperation({
    id: crypto.randomUUID(),
    type: "restock",
    status: session.mode === "standalone" ? "local" : "pending",
    owner_key: ownerKey(),
    created_at: new Date().toISOString(),
    data: { product_id: productId, quantity },
  });
  restockForm.reset();
  await renderAll();
  showMessage(
    appMessage,
    session.mode === "standalone"
      ? "Restock recorded on this device."
      : isOnline()
        ? "Restock queued; syncing now."
        : "Restock saved on this device and will sync when online.",
  );
  if (session.mode !== "standalone" && isOnline()) await syncQueue();
});

queueList.addEventListener("click", async (event) => {
  const retry = event.target.closest("[data-retry-operation]");
  const discard = event.target.closest("[data-discard-operation]");
  const operationId = retry?.dataset.retryOperation || discard?.dataset.discardOperation;
  if (!operationId) return;
  const operation = (await currentOperations()).find((item) => item.id === operationId);
  if (!operation) return;
  if (discard) {
    await removeOperation(operationId);
  } else {
    operation.status = "pending";
    delete operation.error;
    await saveOperation(operation);
  }
  await renderAll();
  if (retry && isOnline()) await syncQueue();
});

$("#sync-button").addEventListener("click", async () => {
  if (!isOnline()) {
    showMessage(appMessage, "No connection. Pending changes are saved on this device.");
    return;
  }
  await syncQueue();
  await refreshCatalog();
});

$("#logout-button").addEventListener("click", async () => {
  const wasStandalone = session?.mode === "standalone";
  if (isOnline() && session && session.mode !== "standalone") {
    try {
      await apiRequest("/api/pos/logout/", { method: "POST" });
    } catch (error) {
      showMessage(appMessage, `Server sign-out failed: ${error.message}`, true);
    }
  }
  await clearSession();
  cart = new Map();
  products = [];
  posPanel.classList.add("hidden");
  loginPanel.classList.remove("hidden");
  localSetupPanel.classList.add("hidden");
  loginMode.value = wasStandalone ? "standalone" : "server";
  loginMode.dispatchEvent(new Event("change"));
  $("#continue-saved-session").classList.add("hidden");
});

async function handleConnectionChange(connected) {
  networkConnected = connected;
  updateConnectionStatus();
  if (connected) {
    await syncQueue();
    await refreshCatalog();
  }
}

window.addEventListener("online", () => handleConnectionChange(true));
window.addEventListener("offline", () => handleConnectionChange(false));
document.addEventListener("visibilitychange", async () => {
  if (!document.hidden && isOnline()) {
    await syncQueue();
    await refreshCatalog();
  }
});

async function startApp() {
  const status = await Network.getStatus();
  networkConnected = status.connected;
  await Network.addListener("networkStatusChange", ({ connected }) => {
    handleConnectionChange(connected);
  });
  await App.addListener("appStateChange", async ({ isActive }) => {
    if (isActive) {
      const currentStatus = await Network.getStatus();
      await handleConnectionChange(currentStatus.connected);
    }
  });
  if (!Capacitor.isNativePlatform()) {
    apiBaseInput.value = import.meta.env.VITE_API_BASE_URL || window.location.origin;
  } else {
    apiBaseInput.value = import.meta.env.VITE_API_BASE_URL || "";
  }
  loginMode.dispatchEvent(new Event("change"));
  const localUserCount = await getLocalUserCount();
  $("#show-local-setup").classList.toggle("hidden", localUserCount > 0);
  const savedSession = await loadSession();
  if (savedSession) {
    session = savedSession;
    apiBaseInput.value = savedSession.apiBase;
    loginMode.value = savedSession.mode === "standalone" ? "standalone" : "server";
    $("#username").value = savedSession.username;
    $("#continue-saved-session").classList.remove("hidden");
    await refreshCachedProducts();
    customers = await getSetting(`catalog-customers:${ownerKey()}`) || [];
    renderCustomers();
    setSessionView();
    const cachedAt = await getSetting(`catalog-updated:${ownerKey()}`);
    if (cachedAt) {
      $("#catalog-updated").textContent = `Cached ${new Date(cachedAt).toLocaleString()}`;
    }
    if (isOnline()) {
      await syncQueue();
      await refreshCatalog();
    }
  }
  updateConnectionStatus();
  if ("serviceWorker" in navigator && import.meta.env.PROD && window.isSecureContext) {
    navigator.serviceWorker.register("./service-worker.js").catch((error) => {
      console.error("Could not register the offline app shell:", error);
    });
  }
}

startApp();

# FREE HOUSE BAR & RESTAURANT POS

A monolithic, enterprise-grade Point of Sale (POS) system built with Python, Django, and Bootstrap 5. Developed as a comprehensive final-year Computer Science capstone at Kenyatta University, this system completely bypasses the default Django admin panel to deliver a secure, role-protected frontend for inventory, CRM, and sales management.

**Core Features:**

- **Liquor Store Catalog:** Includes starter categories for spirits, beers, wines, ciders, soft drinks, and mixers, with bottle-size and crate/carton pricing fields.
- **Advanced POS Terminal:** Features dynamic category filtering, retail/wholesale pricing toggles, and seamless cart management.
- **Atomic Transactions:** Utilizes Django's `@transaction.atomic` to guarantee database integrity during stock deductions and invoice creation.
- **Fixed checkout details:** Till No. **5453103** is printed on every Till payment receipt. The checkout adds **16% VAT** to the discounted item subtotal and shows the tax breakdown.
- **Customer Receipts & Product Images:** Record a customer's name on each sale and upload product photos directly to the catalog.
- **Quotations & CRM:** Integrated customer management allowing cashiers to generate and export custom quotes without altering inventory levels.
- **Role-Based Access Control:** Custom security decorators enforcing strict permissions across Admin, Manager, and Cashier roles.

**Tech Stack:** Python, Django, HTML5, CSS3, Bootstrap 5, Chart.js.

## Mobile App and Android APK

The main management application remains server-rendered Django. The separate
`mobile/` Vite + Capacitor client can run in standalone local mode or connect to
the Django backend. Standalone mode stores its local account, catalog, product
photos, sales, and restocks in IndexedDB; it does not require a server. When
connected to the backend, it can refresh the catalog and sync queued
sales/restocks. Synced sales are revalidated against current server stock, and
UUID client references make retries idempotent. Rejected operations stay on
the device for explicit retry or discard. The app shell is precached as a PWA,
and standalone mode supports JSON backup/restore plus CSV sales export.

### Backend setup

Apply the schema changes and start the Django server:

```sh
python manage.py migrate
python manage.py runserver
```

The mobile API lives under `/api/pos/`. POS users authenticate with a
username/password and receive a token; inventory reads are available to POS
roles, while stock restocks are restricted to admins and managers. Serve the
production backend over HTTPS and set the comma-separated
`CORS_ALLOWED_ORIGINS` environment variable to the deployed app origins (for
example `https://localhost,capacitor://localhost,https://pos.example.com`).
The Django Reports page also provides a date-range Z-report. Invoice items
capture cost at sale time for future reports; older invoices with no recorded
cost are explicitly marked as having incomplete profit data.

### Standalone mobile and Android app

The `mobile/` app can create a local owner account and operate without a
Django URL or network connection. In standalone mode, categories, products,
stock adjustments, sales, customer names, and receipts are stored in the
device's IndexedDB. Full JSON and CSV backup/restore plus sales CSV export are
available in the inventory management section. Keep backups outside the device. Local
account credentials are intentionally not included in exported backups.
The mobile POS includes barcode scanning, liquor/restaurant categories and
package sizes, low-stock alerts, restocking, and persistent hold/resume
customer tabs. Its local date-range Z-report shows sales by Cash, Till,
Paybill, and Send Money plus cost-based profit and VAT collected; old sales
without cost snapshots are marked incomplete rather than assigned a guessed
cost. New receipts use the fixed Till No. 5453103 and apply 16% VAT after
discount.

Server mode is optional. It authenticates against Django, caches the catalog,
and queues sales and restocks for sync when online. Android background sync is
not guaranteed while the app is force-closed.

Install Node.js 20 or later and the Android SDK, then build and sync:

```sh
cd mobile
npm install
npm run build
npx cap sync android
npx cap open android
```

For a debug APK, run `cd android && ./gradlew assembleDebug`. The generated
debug APK is signed with the standard Android debug key and is suitable for
testing/installing, not Play Store publication. The project currently targets
Java 21 source compatibility; use a full JDK 21 (including `javac`) for the
Android build.

The Android client stores its server bearer session with
`@aparajita/capacitor-secure-storage` (Android Keystore-backed encryption).
That plugin's browser implementation uses unencrypted local storage and is
intended for development, not production browser deployments. A customer name
is captured for each sale and appears on the receipt; local products can also
include an uploaded picture.

## Desktop and portable packages

See [release/README.md](release/README.md) for the Ubuntu desktop launcher,
portable standalone Windows package, Windows 10/11 Django server build, and
Android SDK/APK build instructions. Run `run_chiwas_linux.sh` on Ubuntu to
start the LAN Django server and open the POS in a Chrome app window. The
Windows and Ubuntu standalone packages are built from `mobile/www` using
`bash release/package_portable.sh`. The Windows 7/8/10/11 ZIP has a local
PowerShell static server and launcher. Extract the Windows ZIP and double-click
`00-SETUP_CHIWAS_POS.bat` to install for the current user, add a Desktop
shortcut, and start the POS. `START_CHIWAS_POS.bat` launches it without
installing. On Ubuntu, run `00-INSTALL_CHIWAS_POS.sh` from the extracted ZIP
to add an Applications menu entry, or run `Start_Chiwas_POS_Linux.sh` for a
one-time launch. Both need a compatible Chromium-based browser. Modern Chrome
no longer supports Windows 7/8; those systems require an older compatible
browser and are not covered by current-browser support. These portable web
packages are not native `.exe`/`.deb` applications.

## Automated GitHub builds and downloads

`.github/workflows/build-pos-releases.yml` runs on pushes to `main` and on
manual dispatch. It builds the debug-signed Android APK and both portable
desktop ZIPs, uploads them as the `free-house-pos-downloads` Actions artifact, and
publishes a GitHub Release for that workflow run.

After pushing a change, download artifacts from **GitHub → Actions → Build
FREE HOUSE POS releases → latest successful run → Artifacts → free-house-pos-downloads**.
For public release assets, go to **GitHub → Releases** and download
`Free-House-POS.apk`, `Free-House-POS-Windows-7-8-10-11.zip`, or
`Free-House-POS-Ubuntu.zip`.

To publish a new build:

```sh
git status
git push origin main
```

Or trigger **Build FREE HOUSE POS releases → Run workflow** from the Actions tab.

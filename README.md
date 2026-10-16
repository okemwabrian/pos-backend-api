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

On first run, open `/setup/` to create the Brian and Chiwas full-access
administrator accounts. Set a password for each account; each password must
contain at least four digits. Numeric passwords such as `1234` and `2580` are
accepted for this local POS. The setup page is disabled after those accounts
exist.

Local POS sessions survive browser restarts and renew while the system is in
use (with a ten-year idle expiration). Sign out to end a session. SQLite data
and uploaded media are stored outside the desktop package and remain on disk
when the app is closed.

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

The Android client is a separate app. It can run in local-only mode using
device IndexedDB, or connect to the Django `/api/pos/` endpoints. Its local
account and data storage are separate from Django; it is not used by the
Windows/Ubuntu desktop downloads.
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

See [release/README.md](release/README.md) for desktop Django installer and
Android APK build instructions. The Windows download is an installer EXE that
installs and launches the server-rendered Django POS without requiring Python
or a terminal. The optional Windows source ZIP and Ubuntu ZIP require Python
for setup. POS data is stored outside the application and remains on disk
when the app is closed. The desktop downloads do not launch the standalone
JavaScript POS app.
The Django pages may still load JavaScript libraries from `static/` for page
features such as charts; their HTML and page rendering use Django templates.
`run_chiwas_linux.sh` remains a developer launcher for serving the Django app
to trusted LAN devices.

## Automated GitHub builds and downloads

`.github/workflows/build-pos-releases.yml` runs on pushes to `main` and on
manual dispatch. It builds the debug-signed Android APK and both Django
desktop ZIPs, uploads them as the `free-house-pos-downloads` Actions artifact, and
publishes a GitHub Release for that workflow run.

After pushing a change, download artifacts from **GitHub → Actions → Build
FREE HOUSE POS releases → latest successful run → Artifacts → free-house-pos-downloads**.
For public release assets, go to **GitHub → Releases** and download
`Free-House-POS.apk`, `FREE-HOUSE-POS-Windows-Setup.exe`,
`FREE-HOUSE-POS-Windows-Source.zip`, or `Free-House-POS-Ubuntu.zip`.
The workflow builds from the exact commit pushed to `main`; local-only files
such as the SQLite database, virtual environment, and `.env` are not pushed or
included. The desktop ZIPs contain the same Django templates and source as the
repository. Each installation creates its own database and media files; those
local records are intentionally not part of GitHub builds. First-time setup
creates both administrator accounts with locally chosen passwords.

To publish a new build:

```sh
git status
git push origin main
```

Or trigger **Build FREE HOUSE POS releases → Run workflow** from the Actions tab.

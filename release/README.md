# FREE HOUSE BAR & RESTAURANT POS packages

## Automated GitHub builds

The workflow at `.github/workflows/build-pos-releases.yml` runs for pushes to
`main` and for manual `workflow_dispatch`. It builds:

- `Free-House-POS.apk` — Android debug APK, signed with Android's debug key.
- `Free-House-POS-Windows-7-8-10-11.zip` — Django server-rendered POS project
  with Windows setup and launch batch files.
- `Free-House-POS-Ubuntu.zip` — Django server-rendered POS project with Ubuntu
  setup and launch scripts.

The three files are uploaded as the `free-house-pos-downloads` Actions artifact and
attached to a GitHub Release for the workflow run. Find run artifacts under
**GitHub → Actions → Build FREE HOUSE POS releases → successful run → Artifacts**;
find permanent downloadable files under **GitHub → Releases**.

## Android standalone operation and backup

The Android app's standalone mode does not need Django or an internet
connection. Its local accounts, categories, products, stock, sales, and
restocks, open customer tabs, and receipts live in IndexedDB on the
device/browser profile. Server mode is
optional and adds catalog refresh and queued sync. A force-closed app cannot
perform background sync.

Use the app's JSON/CSV backup and restore plus CSV sales export regularly, and copy
backups to a separate safe location. JSON backup files do not include local
account credentials. Browser storage is tied to the device/browser profile;
clearing browser data can remove the only local copy.

Standalone and Django reports provide date-range sales totals split by Cash,
Till, Paybill, and Send Money. New server invoices record cost at the time of
sale. Historic sales whose item cost was never recorded are flagged as
incomplete for profit calculations rather than being assigned an assumed cost.
New sales add 16% VAT after discounts and print the fixed Till No. 5453103.
The receipt logo, Android icon, and app title use the Free House branding.

## Local Android build

The checked-in Android project uses Java 21 source compatibility, so install a
full JDK 21 including `javac`, Node.js 20, and Android SDK API 35/build-tools
35.0.0. From the repository root, run:

```sh
bash release/android/build_apk.sh
```

The script builds the web app, syncs Capacitor, assembles a debug APK, and
copies it to `release/android/Free-House-POS.apk`. The APK is debug-signed and is
for direct testing/installing; release signing for Play Store distribution
requires a private signing key and is intentionally not configured in CI.

## Django Windows and Ubuntu desktop packages

Run the package script from the repository root:

```sh
bash release/package_portable.sh
```

The ZIPs are written under `release/dist/`. They package the Django source,
templates, and static assets; the Android standalone client is not included.
Python 3.12 or newer and internet access are needed for first-time dependency
installation. Extract the Windows ZIP to a permanent folder and run
`SETUP_FREE_HOUSE_POS.bat`; on Ubuntu, run `SETUP_FREE_HOUSE_POS.sh`. These
create a per-user virtual environment, install the Python requirements, run
migrations, and start the POS at `http://127.0.0.1:8000/`. Subsequent launches
use `START_FREE_HOUSE_POS.bat` or `START_FREE_HOUSE_POS.sh`.

The first setup page creates both full-access Django superusers, Brian and
Chiwas. Choose a different strong password for each account; Django's password
checks apply. The SQLite database, uploaded media, and generated Django secret
key are stored outside the extracted source directory. The bundled server
listens only on localhost.

## Ubuntu Django LAN development launcher

`run_chiwas_linux.sh` uses the project's virtual environment, applies Django
migrations, and opens the Django POS in a Chrome app window. It listens on
`0.0.0.0:8000` for devices on the trusted local network. This development-style
server must not be exposed to the public internet.

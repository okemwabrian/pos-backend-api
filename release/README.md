# CHIWAS POS release packages

## Automated GitHub builds

The workflow at `.github/workflows/build-pos-releases.yml` runs for pushes to
`main` and for manual `workflow_dispatch`. It builds:

- `Chiwas-Liquor-POS.apk` — Android debug APK, signed with Android's debug key.
- `Chiwas-POS-Windows-7-8-10-11.zip` — local web app with a Windows setup
  batch file, Desktop shortcut creation, and PowerShell local server.
- `Chiwas-POS-Ubuntu.zip` — local web app with an Ubuntu setup script,
  Applications menu entry, and shell launcher.

The three files are uploaded as the `chiwas-pos-downloads` Actions artifact and
attached to a GitHub Release for the workflow run. Find run artifacts under
**GitHub → Actions → Build CHIWAS POS releases → successful run → Artifacts**;
find permanent downloadable files under **GitHub → Releases**.

## Standalone operation and backup

The mobile app's standalone mode does not need Django or an internet
connection. Its owner account, local categories, products, stock, sales, and
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

## Local Android build

The checked-in Android project uses Java 21 source compatibility, so install a
full JDK 21 including `javac`, Node.js 20, and Android SDK API 35/build-tools
35.0.0. From the repository root, run:

```sh
bash release/android/build_apk.sh
```

The script builds the web app, syncs Capacitor, assembles a debug APK, and
copies it to `release/android/Chiwas-POS.apk`. The APK is debug-signed and is
for direct testing/installing; release signing for Play Store distribution
requires a private signing key and is intentionally not configured in CI.

## Portable Windows and Ubuntu builds

After `cd mobile && npm ci && npm run build`, run:

```sh
bash release/package_portable.sh
```

The ZIPs are written under `release/dist/`. On Windows, extract the ZIP and
double-click `00-SETUP_CHIWAS_POS.bat` to install for the current user, create a
Desktop shortcut, and start the POS. `START_CHIWAS_POS.bat` launches it without
installing. Windows requires PowerShell and a Chromium-based browser. On
Ubuntu, run `00-INSTALL_CHIWAS_POS.sh` to create an Applications menu entry, or
run `Start_Chiwas_POS_Linux.sh` directly. Ubuntu requires Python 3 and Chrome
or Chromium. The app and data are stored locally; no Django service is required.

Windows 7/8 are outside current Chrome support and require a compatible older
Chromium browser; modern browser versions are not guaranteed to run on those
operating systems. These ZIPs are portable browser-based applications, not
native installers or executables.

## Ubuntu Django LAN server launcher

`run_chiwas_linux.sh` uses the project's virtual environment, applies Django
migrations, and opens the Django POS in a Chrome app window. It listens on
`0.0.0.0:8000` for devices on the trusted local network. This development-style
server must not be exposed to the public internet.

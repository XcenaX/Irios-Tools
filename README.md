# Irios Tools

Public desktop client for Irios API.

## Build

```powershell
.\rebuild_desktop.bat
```

For one-file releases, use PyInstaller with `--onefile` and publish the executable through GitHub Releases.

## Release

```powershell
.\tools\release_desktop.ps1 -Version 3.0.1
```

The release script builds `Irios.Tools.exe`, uploads it to GitHub Releases, updates `releases/latest.json`, commits the version bump, and pushes `main`.

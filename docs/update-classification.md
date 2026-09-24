# Update classification

Every pending update is counted in **Total**, and may also be tagged **Security**, **Kernel** and/or **Critical**. A single package can carry several tags; for example, a kernel security fix is tagged all three. So the category counts don't add up to the total.

## Security updates

Security updates come from the distribution's own security data, not from guessing by package name.

### Debian and Ubuntu

An update is a security update when its candidate version comes from a **security repository**, one whose name contains `-security` (for example `noble-security` or `bookworm-security`).

`apt list --upgradable` shows the repositories for each update:

```text
openssl/noble-updates,noble-security 3.0.13-0ubuntu3.4 amd64 [upgradable from: 3.0.13-0ubuntu3.1]
curl/noble-updates 8.5.0-2ubuntu10.4 amd64 [upgradable from: 8.5.0-2ubuntu10.1]
```

Here `openssl` is a security update and `curl` is not.

> **Why do my Ubuntu nodes show 0 security updates?** Ubuntu installs security updates automatically every day through `unattended-upgrades`, which is on by default. A healthy Ubuntu server usually has no security updates waiting; the remaining updates are ordinary bug-fix updates. This is expected.

### Rocky Linux, RHEL, AlmaLinux and CentOS

An update is a security update when the package appears in the security advisories reported by:

```bash
dnf updateinfo list --security
```

(or `yum updateinfo list --security` on systems without `dnf`). The advisory lists the fixed package and version, for example:

```text
RLSA-2024:5363 Important/Sec. kernel-core-5.14.0-427.33.1.el9_4.x86_64
```

Package names are matched exactly, so an advisory for `openssl-libs` doesn't mark `openssl` as a security update.

> **Note:** some repositories and mirrors don't publish advisory data (common with CentOS Stream and some third-party repositories). Nodes using them always show 0 security updates, although their totals are still correct.

## Kernel updates

An update is a kernel update when the package name starts with:

| Family | Prefixes |
| --- | --- |
| Debian/Ubuntu | `linux-image`, `linux-headers` |
| RHEL family | `kernel` (for example `kernel`, `kernel-core`, `kernel-modules`) |

On Ubuntu, kernel updates usually appear as the meta-packages `linux-image-generic` and `linux-headers-generic`, or their cloud variants such as `linux-image-virtual` or `linux-image-azure`.

A new kernel is only used after a **reboot**.

## Critical packages

Critical packages are core system components where an outdated version is most risky. An update is critical when the package is a kernel package or its name starts with:

| Prefix | Component |
| --- | --- |
| `openssl`, `libssl` | TLS and cryptography library |
| `openssh` | SSH server and client |
| `sudo` | Privilege escalation |
| `systemd` | Init system and service manager |
| `glibc`, `libc6` | C standard library (RHEL / Debian names) |

These packages are critical whether or not the update is a security fix. Prioritise them in patch windows, and restart the affected services (or reboot) after updating them.

## Totals

**Total** is every package the package manager reports as upgradable:

- Debian/Ubuntu: every line of `apt list --upgradable`.
- RHEL family: every package line of `dnf check-update`. Header lines, blank lines and the *Obsoleting Packages* section are ignored, and long package names that wrap onto two lines are counted once.

## Checking a node by hand

To see what Patchli sees, run the same commands on the node as the registered user.

Debian/Ubuntu: everything, then only the updates Patchli would tag:

```bash
apt list --upgradable 2>/dev/null
apt list --upgradable 2>/dev/null | grep -E -- '-security|linux-image|linux-headers|openssl|libssl|openssh|sudo|systemd|glibc|libc6'
```

RHEL family:

```bash
dnf -q check-update
dnf -q updateinfo list --security
```

If the dashboard's counts don't match what these commands show, please [open an issue](https://github.com/Mohammad-Sameer-Infra/linux-patch-dashboard/issues) and include the output.

#!/usr/bin/env python3
"""
sync_profile.py — Autonomous profile README synchronization script
Synchronizes ACESVAGE GitHub profile README with latest status across:
- python-security-toolkit (30 scripts roadmap)
- c-threat-hunter (20 programs roadmap)
- linux-admin-scripts (30 scripts roadmap)

Works both locally (inspecting filesystem / git) and in GitHub Actions (via GitHub API).
"""

import os
import sys
import json
import re
from pathlib import Path
import urllib.request
import urllib.error

USER = "ACESVAGE"
REPO_NAMES = ["python-security-toolkit", "c-threat-hunter", "linux-admin-scripts"]

def get_base_dir() -> Path:
    # If script is in ACESVAGE/scripts/, base repo is ACESVAGE
    return Path(__file__).resolve().parent.parent

def inspect_local_repo(repo_path: Path):
    if not repo_path.exists():
        return None
    
    data = {}
    if repo_path.name == "python-security-toolkit":
        scripts = []
        for folder in ["recon", "scanning", "hardening", "log-analysis", "crypto", "automation"]:
            p = repo_path / folder
            if p.exists():
                for f in p.glob("*.py"):
                    if not f.name.startswith("__"):
                        scripts.append(f"{folder}/{f.name}")
        data["deployed_count"] = len(scripts)
        data["total"] = 30
        data["deployed_files"] = scripts
    elif repo_path.name == "c-threat-hunter":
        programs = []
        for folder in ["static-analysis", "process-inspection", "memory-analysis", "system-integrity"]:
            p = repo_path / folder
            if p.exists():
                for f in p.glob("*.c"):
                    programs.append(f"{folder}/{f.name}")
        data["deployed_count"] = len(programs)
        data["total"] = 20
        data["deployed_files"] = programs
    elif repo_path.name == "linux-admin-scripts":
        scripts = []
        for folder in ["admin", "cybersecurity"]:
            p = repo_path / folder
            if p.exists():
                for f in p.rglob("*.sh"):
                    rel = f.relative_to(p)
                    scripts.append(f"{folder}/{rel.as_posix()}")
        data["deployed_count"] = len(scripts)
        data["total"] = 30
        data["deployed_files"] = scripts
        
    return data

def fetch_github_api(endpoint: str, token: str = None):
    url = f"https://api.github.com/{endpoint.lstrip('/')}"
    headers = {"User-Agent": "ACESVAGE-Profile-Sync"}
    if token:
        headers["Authorization"] = f"token {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"[WARN] GitHub API request failed for {endpoint}: {e}")
        return None

def inspect_remote_repo(repo_name: str, token: str = None):
    tree = fetch_github_api(f"repos/{USER}/{repo_name}/git/trees/main?recursive=1", token)
    if not tree or "tree" not in tree:
        return None
        
    paths = [item["path"] for item in tree["tree"] if item["type"] == "blob"]
    data = {}
    if repo_name == "python-security-toolkit":
        scripts = [p for p in paths if p.endswith(".py") and not Path(p).name.startswith("__") and any(p.startswith(f) for f in ["recon/", "scanning/", "hardening/", "log-analysis/", "crypto/", "automation/"])]
        data["deployed_count"] = len(scripts)
        data["total"] = 30
        data["deployed_files"] = scripts
    elif repo_name == "c-threat-hunter":
        programs = [p for p in paths if p.endswith(".c") and any(p.startswith(f) for f in ["static-analysis/", "process-inspection/", "memory-analysis/", "system-integrity/"])]
        data["deployed_count"] = len(programs)
        data["total"] = 20
        data["deployed_files"] = programs
    elif repo_name == "linux-admin-scripts":
        scripts = [p for p in paths if p.endswith(".sh") and (p.startswith("admin/") or p.startswith("cybersecurity/"))]
        data["deployed_count"] = len(scripts)
        data["total"] = 30
        data["deployed_files"] = scripts
        
    return data

def gather_status():
    base_dir = get_base_dir()
    token = os.getenv("GITHUB_TOKEN")
    results = {}
    
    # Try local parent directory first (sister repos in C:\Users\HomePC)
    parent_dir = base_dir.parent
    for name in REPO_NAMES:
        local_dir = parent_dir / name
        info = inspect_local_repo(local_dir)
        if not info:
            info = inspect_remote_repo(name, token)
        results[name] = info
        
    return results

def update_readme(readme_path: Path, status: dict) -> bool:
    content = readme_path.read_text(encoding="utf-8")
    original = content
    
    # Check python-security-toolkit
    py_info = status.get("python-security-toolkit")
    if py_info:
        count = py_info["deployed_count"]
        # Update summary line
        content = re.sub(
            r"(<summary>🛡️ <b>python-security-toolkit</b> — 30-script Python security suite).*?(</summary>)",
            r"\1 (" + f"{count}/30 deployed" + r")\2",
            content
        )
        content = re.sub(
            r"Currently \*\*(\d+) scripts deployed\*\* with the recon phase complete and network scanning underway:",
            f"Currently **{count} scripts deployed** with the recon phase complete and network scanning underway:",
            content
        )

    # Check c-threat-hunter
    c_info = status.get("c-threat-hunter")
    if c_info:
        count = c_info["deployed_count"]
        # Check if details block exists, replace or update
        c_details_block = f"""<details>
<summary>🎯 <b>c-threat-hunter</b> — 20-program C malware & threat hunting suite ({count}/20 deployed)</summary>
<br/>

A low-level **20-program C suite** exploring OS internals, malware detection, and binary analysis (Win32 & POSIX). Currently **{count} program deployed** with Phase 1 static analysis underway:

| Phase | Module | Programs | What It Does |
|---|---|---|---|
| `Phase 1` | `static-analysis/` | `pe_header_parser.c` (✅ deployed), `elf_header_parser.c` (⏳ next), `section_entropy.c`, `string_extractor.c`, `hash_validator.c` | DOS/NT headers, section mapping, imports/exports, entropy calculation, string carving |
| `Phase 2` | `process-inspection/` | 🔄 *Coming soon* (`proc_enumerator.c`, `hollowing_detector.c`, etc.) | Snapshot inspection, DLL enumeration, thread start auditing, process hollowing detection |
| `Phase 3` | `memory-analysis/` | 🔄 *Coming soon* (`page_perms_audit.c`, `pattern_scanner.c`, etc.) | RWX page auditing, memory scanning, memory dumps, VAD tree walking |
| `Phase 4` | `system-integrity/` | 🔄 *Coming soon* (`autorun_auditor.c`, `hook_detector.c`, etc.) | Run keys, inline API hooks (ntdll detours), driver auditing, real-time FIM |

- Built with **C11**, cross-platform (MinGW / GCC / Clang / MSVC)
- Includes standalone compilation scripts, unified Makefiles, and modular headers

</details>"""
        # Replace existing c-threat-hunter details block
        c_pattern = r"(?s)<details>\s*<summary>🎯 <b>c-threat-hunter</b>.*?</details>"
        if re.search(c_pattern, content):
            content = re.sub(c_pattern, c_details_block, content)

    # Check linux-admin-scripts
    linux_info = status.get("linux-admin-scripts")
    if linux_info:
        count = linux_info["deployed_count"]
        linux_details_block = f"""<details>
<summary>🐧 <b>linux-admin-scripts</b> — 30-script Bash sysadmin & security suite ({count}/30 deployed)</summary>
<br/>

A structured **30-script Bash suite** covering Linux administration and cybersecurity automation. Currently **{count} scripts deployed** in Phase 1 (Foundation):

| Phase | Module | Scripts | What It Does |
|---|---|---|---|
| `Phase 1` | `admin/` | `user_management.sh`, `disk_management.sh`, `network_management.sh`, `backup_restore.sh` | Interactive user/group administration, storage diagnostics & quotas, network diagnostics & firewall rules, tar/rsync incremental backups |
| `Phase 2` | `cybersecurity/scanning` & `recon` | 🔄 *Coming soon* (`host_discovery.sh`, `port_scanner.sh`, `subdomain_enum.sh`, etc.) | Ping sweeps, port scanning, OSINT domain reconnaissance, system hardening |
| `Phase 3` | `cybersecurity/log-analysis` | 🔄 *Coming soon* (`failed_login_detector.sh`, `intrusion_detector.sh`, etc.) | Failed login & brute-force detection, file integrity checking, network traffic monitoring |
| `Phase 4` | `cybersecurity/ctf` | 🔄 *Coming soon* (`web_recon.sh`, `hash_cracker_helper.sh`, etc.) | Web directory busting, password hash cracking assistance, CTF utilities |

- Tested across **Ubuntu, Debian, Fedora, CentOS, RHEL, and Arch**
- Robust error handling (`set -euo pipefail`), root privilege verification, and ANSI colorized outputs

</details>"""
        linux_pattern = r"(?s)<details>\s*<summary>🐧 <b>linux-admin-scripts</b>.*?</details>"
        if re.search(linux_pattern, content):
            content = re.sub(linux_pattern, linux_details_block, content)

    # Update GitHub Trophies section if still pointing directly to broken demo
    trophy_clean = """## 🏆 GitHub Trophies

<div align="center">
  <!-- 
    NOTE: The upstream demo service (github-profile-trophy.vercel.app) has been paused by Vercel (HTTP 402 Payment Required).
    To restore trophies, deploy your own instance for free from https://github.com/ryo-ma/github-profile-trophy and update the endpoint URL.
  -->
  <a href="https://github.com/ryo-ma/github-profile-trophy">
    <img src="https://img.shields.io/badge/Trophies-Self--Host%20Instance%20Ready-00bfff?style=for-the-badge&logo=github&labelColor=0d1117" alt="GitHub Trophies Status"/>
  </a>
  <br/><br/>
  <sub><i>🏆 Showcase temporarily paused while upstream Vercel deployment is offline. Check live activity and streaks below!</i></sub>
</div>"""
    trophy_pattern = r"(?s)## 🏆 GitHub Trophies\s*<div align=\"center\">\s*<img src=\"https://github-profile-trophy\.vercel\.app/.*?</div>"
    if re.search(trophy_pattern, content):
        content = re.sub(trophy_pattern, trophy_clean, content)

    # Update Roadmap section
    roadmap_block = """## 🗺️ The Roadmap — What's Next

```
🔄 Currently Building:
├── 🐍 Python Toolkit: Network scanning (host_discovery ✅, port_scanner ✅, banner_grabber ⏳)
├── ⚙️ C Threat Hunter: Static analysis (pe_header_parser ✅, elf_header_parser ⏳)
├── 🐧 Linux Admin Suite: Core sysadmin (user_mgmt ✅, disk_mgmt ✅, net_mgmt ✅, backup ✅, monitor ⏳)
└── 🔐 Hardening & Memory analysis: SSH auditor, SSL validator & RWX detection

🎯 On the Horizon:
├── 🏴 CTF challenge scripts & writeups
├── 📡 SIEM integration & log correlation
├── 🕵️ Full incident response automation
└── 🧪 Malware analysis sandbox tooling
```"""
    roadmap_pattern = r"(?s)## 🗺️ The Roadmap — What's Next\s*```.*?```"
    if re.search(roadmap_pattern, content):
        content = re.sub(roadmap_pattern, roadmap_block, content)

    if content != original:
        readme_path.write_text(content, encoding="utf-8")
        return True
    return False

def main():
    base_dir = get_base_dir()
    readme_path = base_dir / "README.md"
    if not readme_path.exists():
        print(f"[ERROR] README.md not found at {readme_path}")
        sys.exit(1)
        
    print("[INFO] Gathering companion repository status...")
    status = gather_status()
    for name, info in status.items():
        if info:
            print(f"  - {name}: {info['deployed_count']}/{info['total']} items deployed")
        else:
            print(f"  - {name}: [not found or API limit]")
            
    print("[INFO] Updating README.md...")
    changed = update_readme(readme_path, status)
    if changed:
        print("[SUCCESS] README.md was synchronized and updated.")
    else:
        print("[INFO] README.md is already up to date.")

if __name__ == "__main__":
    main()

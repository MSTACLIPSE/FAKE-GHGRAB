        ███╗   ███╗███████╗████████╗ █████╗  ██████╗ ██████╗  █████╗ ██████╗ ██████╗ ███████╗██████╗ 
        ████╗ ████║██╔════╝╚══██╔══╝██╔══██╗██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗
        ██╔████╔██║███████╗   ██║   ███████║██║  ███╗██████╔╝███████║██████╔╝██████╔╝█████╗  ██████╔╝
        ██║╚██╔╝██║╚════██║   ██║   ██╔══██║██║   ██║██╔══██╗██╔══██║██╔══██╗██╔══██╗██╔══╝  ██╔══██╗
        ██║ ╚═╝ ██║███████║   ██║   ██║  ██║╚██████╔╝██║  ██║██║  ██║██████╔╝██████╔╝███████╗██║  ██║
        ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
                                — grab what you need, leave the rest —

 MSTAGRABBER is a pure GUI tool that lets you browse and download any public GitHub repository’s files with a cyberpunk purple interface. No command-line fu required — just point, click, and grab.

Built for OSINT researchers, archivers, and anyone who wants to pull a repo’s contents without cloning the whole thing.

# ✨ Features
🖱️ Pure GUI — No terminal commands after launch. Tkinter-based, cross-platform.

🔐 Token support — Anonymous (60 req/hr) or authenticated (5000 req/hr via GitHub token).

📂 Recursive browsing — Navigate repo folders like a file manager.

✅ Selective download — Pick individual files, not the whole repo.

📦 ZIP packaging — Downloaded files are saved as a single ZIP archive.

🎨 Purple / Hacker theme — Dark background, neon cyan/purple accents, retro console vibe.

⚡ Async fetching — Non-blocking API calls; UI stays responsive.

🧭 Breadcrumb navigation — Easy “up” / “root” buttons to jump around.

🔍 Repository filter — Quick-search through a user’s repos.

🚫 No dependencies outside standard library + requests + tkinter (usually bundled with Python).

# 🚀 Quick Start
Prerequisites
Python 3.7+

requests library

Install
bash
# Clone the repository
git clone https://github.com/MSTACLIPSE/MSTAGRAB.git
cd MSTAGRAB

# Install dependency (if not already present)
pip install requests
Run
bash
python MSTAGRAB.py
With a GitHub token (recommended for heavy use):

bash
python MSTAGRAB.py --token ghp_your_token_here
Or set the token inside the GUI via the [03] SET TOKEN button.

🧪 How It Works
Enter a GitHub username → fetches all public repositories (sorted by last updated).

Select a repo → loads the file tree from the default branch.

Navigate folders → double‑click directories, use UP / ROOT buttons.

Select files → click the checkbox column or press SPACE on a file.

Download → press ENTER (or click the green button) → saves a ZIP with your chosen files.

https://via.placeholder.com/800x400?text=MSTAGRABBER+in+action
(Screenshot placeholder — imagine a purple TK window with repo list and file tree.)

# ⚙️ GUI Controls
Key / Button	Action
ENTER on username	Fetch repositories
Double‑click repo	Select it and load file browser
SPACE on a file	Toggle selection
ENTER in file view	Download selected files (ZIP)
UP button	Go to parent directory
ROOT button	Jump back to repo root
BACK TO REPOS	Return to repository selection screen
SET TOKEN	Enter your GitHub PAT (stored in RAM only)
EXIT / [99] EXIT	Close the application
🔐 Rate Limits & Tokens
Mode	Requests per hour
Anonymous	60
Authenticated	5000
Get a token from GitHub Settings → Developer settings → Personal access tokens (classic). No permissions needed (only public repo access).

# 📁 Project Structure

MSTAGRABBER/

├── MSTAGRAB.py         # The entire application (one-file deploy)

├── README.md           # This file

└── LICENSE             # The License
# 🧰 Tech Stack
Python 3 – core logic

Tkinter – native GUI (no external UI libs)

Requests – GitHub API v3

Threading – non‑blocking fetches

Zipfile – on‑the‑fly ZIP creation

# 📜 License
MIT / GPL-3.0 (you choose – original script has no license block, but it’s open. I’d recommend MIT for simplicity).

text
MIT License – use freely, modify, share. No warranty.
# 🙏 Acknowledgements
Built by @MSTACLIPSE

Inspired by the need to fetch single files from GitHub without cloning.

Purple aesthetic courtesy of ANSI escape codes in spirit (but Tkinter pixels).




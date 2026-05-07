#!/usr/bin/env python3
"""
MSTAGRABBER - GitHub File Grabber
Pure GUI window - Purple CDXTOOL aesthetic
Workflow: Username → Repo list → File browser → Download
No admin required.
"""

import os
import sys
import zipfile
import io
import threading
from typing import List, Dict, Optional
import requests
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

# ----------------------------------------------------------------------
# GitHub API
# ----------------------------------------------------------------------

class GitHubAPI:
    def __init__(self, token: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MSTAGRABBER/1.0"
        })
        if token:
            self.session.headers.update({"Authorization": f"token {token}"})

    def _get(self, url: str, params: dict = None) -> dict:
        resp = self.session.get(url, params=params)
        if resp.status_code == 404:
            raise ValueError("Not found")
        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            raise RuntimeError("Rate limit exceeded. Use --token or wait.")
        resp.raise_for_status()
        return resp.json()

    def get_user_repos(self, username: str) -> List[Dict]:
        repos = []
        page = 1
        while True:
            url = f"https://api.github.com/users/{username}/repos"
            params = {"per_page": 100, "page": page, "sort": "updated", "direction": "desc"}
            resp = self.session.get(url, params=params)
            if resp.status_code == 404:
                raise ValueError(f"User '{username}' not found")
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            repos.extend(data)
            page += 1
        return repos

    def get_repo_contents(self, owner: str, repo: str, path: str, branch: str) -> List[Dict]:
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": branch}
        resp = self.session.get(url, params=params)
        if resp.status_code == 404:
            return []
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict):
            return [data]
        return data

    def get_default_branch(self, owner: str, repo: str) -> str:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        data = self._get(url)
        return data.get("default_branch", "main")

    def download_file(self, owner: str, repo: str, file_path: str, branch: str) -> bytes:
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
        resp = self.session.get(raw_url)
        resp.raise_for_status()
        return resp.content

# ----------------------------------------------------------------------
# MSTAGRABBER GUI - Purple Hacker Theme
# ----------------------------------------------------------------------

class MSTAGRABBER:
    def __init__(self, token: Optional[str] = None):
        self.api = GitHubAPI(token)
        self.token = token
        
        # State
        self.username = ""
        self.repos = []
        self.selected_repo = None
        self.owner = ""
        self.repo_name = ""
        self.branch = ""
        self.current_path = ""
        self.navigation_stack = []
        self.selected_files = []
        
        # Build GUI
        self.root = tk.Tk()
        self.root.title("MSTAGRABBER - GitHub File Grabber v4.6")
        self.root.geometry("1250x750")
        self.root.minsize(1050, 650)
        self.root.configure(bg="#0f0f1a")
        
        # Color scheme
        self.colors = {
            'bg': '#0f0f1a',
            'purple': '#9b59b6',
            'dark_purple': '#8e44ad',
            'light_purple': '#c39bd3',
            'cyan': '#00e5ff',
            'white': '#ffffff',
            'gray': '#888888',
            'black': '#0a0a0f',
            'green': '#2ecc71',
            'red': '#e74c3c',
            'yellow': '#f1c40f'
        }
        
        self.setup_ui()
        self.show_username_screen()
        
    def setup_ui(self):
        self.main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ASCII Header - CORRECTED MSTAGRABBER
        self.header_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        
        ascii_art = r"""
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║         ███╗   ███╗███████╗████████╗ █████╗  ██████╗ ██████╗  █████╗ ██████╗ ██████╗ ███████╗██████╗             ║
║         ████╗ ████║██╔════╝╚══██╔══╝██╔══██╗██╔════╝ ██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗            ║
║         ██╔████╔██║███████╗   ██║   ███████║██║  ███╗██████╔╝███████║██████╔╝██████╔╝█████╗  ██████╔╝            ║
║         ██║╚██╔╝██║╚════██║   ██║   ██╔══██║██║   ██║██╔══██╗██╔══██║██╔══██╗██╔══██╗██╔══╝  ██╔══██╗            ║
║         ██║ ╚═╝ ██║███████║   ██║   ██║  ██║╚██████╔╝██████╔╝██║  ██║██████╔╝██████╔╝███████╗██║  ██║            ║
║         ╚═╝     ╚═╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝            ║
║                                                                                                                  ║
║                              GitHub File Grabber - v.0.0.1                                                       ║
║                                   MADE BY @MSTACLIPSE                                                            ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
"""
        ascii_label = tk.Label(self.header_frame, text=ascii_art, 
                                font=("Consolas", 7), fg=self.colors['purple'], 
                                bg=self.colors['bg'], justify=tk.LEFT)
        ascii_label.pack()
        
        # Content area
        self.content_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        self.content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Status bar
        self.status_var = tk.StringVar(value="[READY] MSTAGRABBER initialized")
        self.status_bar = tk.Label(self.main_frame, textvariable=self.status_var,
                                    font=("Consolas", 9), fg=self.colors['gray'],
                                    bg=self.colors['black'], anchor=tk.W, padx=5)
        self.status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    # ------------------------------------------------------------------
    # SCREEN 1: USERNAME INPUT
    # ------------------------------------------------------------------
    def show_username_screen(self):
        self.clear_content()
        
        input_frame = tk.Frame(self.content_frame, bg=self.colors['black'],
                                relief=tk.RIDGE, bd=2)
        input_frame.pack(pady=60, padx=50, fill=tk.BOTH, expand=True)
        
        divider = tk.Label(input_frame, text="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                          font=("Consolas", 10), fg=self.colors['cyan'], bg=self.colors['black'])
        divider.pack(pady=(30, 10))
        
        title = tk.Label(input_frame, text="🔐 ENTER GITHUB USERNAME", 
                         font=("Consolas", 16, "bold"), 
                         fg=self.colors['purple'], bg=self.colors['black'])
        title.pack(pady=10)
        
        divider2 = tk.Label(input_frame, text="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
                           font=("Consolas", 10), fg=self.colors['cyan'], bg=self.colors['black'])
        divider2.pack(pady=(10, 30))
        
        entry_frame = tk.Frame(input_frame, bg=self.colors['black'])
        entry_frame.pack(pady=20)
        
        prompt = tk.Label(entry_frame, text="└─ Username:",
                          font=("Consolas", 13, "bold"), fg=self.colors['purple'],
                          bg=self.colors['black'])
        prompt.pack(side=tk.LEFT, padx=(0, 10))
        
        self.username_entry = tk.Entry(entry_frame, font=("Consolas", 13), width=35,
                                        bg=self.colors['bg'], fg=self.colors['white'],
                                        insertbackground=self.colors['white'],
                                        relief=tk.SUNKEN, bd=1)
        self.username_entry.pack(side=tk.LEFT)
        self.username_entry.bind("<Return>", lambda e: self.fetch_repos())
        
        btn_frame = tk.Frame(input_frame, bg=self.colors['black'])
        btn_frame.pack(pady=30)
        
        fetch_btn = tk.Button(btn_frame, text="[ENTER] FETCH REPOSITORIES", command=self.fetch_repos,
                              font=("Consolas", 11, "bold"), bg=self.colors['purple'], fg='white',
                              activebackground=self.colors['dark_purple'], cursor="hand2",
                              padx=25, pady=8)
        fetch_btn.pack(side=tk.LEFT, padx=5)
        
        token_btn = tk.Button(btn_frame, text="[03] SET TOKEN", command=self.set_token,
                              font=("Consolas", 11), bg=self.colors['gray'], fg='white',
                              activebackground='#666', cursor="hand2", padx=20, pady=8)
        token_btn.pack(side=tk.LEFT, padx=5)
        
        exit_btn = tk.Button(btn_frame, text="[99] EXIT", command=self.exit_app,
                             font=("Consolas", 11), bg=self.colors['red'], fg='white',
                             activebackground='#c0392b', cursor="hand2", padx=20, pady=8)
        exit_btn.pack(side=tk.LEFT, padx=5)
        
        if not self.token:
            hint = tk.Label(input_frame, text="💡 Tip: Use 'Set Token' for higher rate limits (5000/hr vs 60/hr)",
                           font=("Consolas", 9), fg=self.colors['yellow'], bg=self.colors['black'])
            hint.pack(pady=(20, 10))
        
        self.status_var.set("[INPUT] Enter GitHub username and press ENTER")
    
    def fetch_repos(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showwarning("Input Error", "Please enter a GitHub username")
            return
        
        self.username = username
        self.status_var.set(f"[FETCHING] Repositories for @{username}...")
        self.root.update()
        
        def fetch_thread():
            try:
                repos = self.api.get_user_repos(username)
                self.repos = repos
                self.root.after(0, self.show_repo_selection)
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Failed to fetch repos: {e}"))
        
        threading.Thread(target=fetch_thread, daemon=True).start()
    
    # ------------------------------------------------------------------
    # SCREEN 2: REPOSITORY SELECTION
    # ------------------------------------------------------------------
    def show_repo_selection(self):
        self.clear_content()
        
        if not self.repos:
            self.show_error("No repositories found for this user")
            self.show_username_screen()
            return
        
        header_panel = tk.Frame(self.content_frame, bg=self.colors['black'], relief=tk.RIDGE, bd=1)
        header_panel.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header_panel, text=f"📦 REPOSITORIES @{self.username}",
                font=("Consolas", 14, "bold"), fg=self.colors['purple'],
                bg=self.colors['black']).pack(side=tk.LEFT, padx=15, pady=8)
        
        tk.Label(header_panel, text=f"Count: {len(self.repos)}",
                font=("Consolas", 10), fg=self.colors['cyan'],
                bg=self.colors['black']).pack(side=tk.RIGHT, padx=15)
        
        filter_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        filter_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(filter_frame, text="🔍 Filter:",
                font=("Consolas", 10), fg=self.colors['white'],
                bg=self.colors['bg']).pack(side=tk.LEFT, padx=10)
        
        self.filter_entry = tk.Entry(filter_frame, font=("Consolas", 11), width=40,
                                      bg=self.colors['black'], fg=self.colors['white'],
                                      insertbackground=self.colors['white'])
        self.filter_entry.pack(side=tk.LEFT, padx=5)
        self.filter_entry.bind("<KeyRelease>", self.apply_repo_filter)
        
        list_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.repo_listbox = tk.Listbox(list_frame, font=("Consolas", 11),
                                        bg=self.colors['black'], fg=self.colors['white'],
                                        selectbackground=self.colors['purple'],
                                        selectforeground='white',
                                        yscrollcommand=scrollbar.set,
                                        relief=tk.FLAT, bd=0)
        self.repo_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.repo_listbox.yview)
        
        self.repo_display_list = []
        self.repo_data_map = {}
        
        for repo in self.repos:
            name = repo['name']
            private = "🔒" if repo['private'] else "📁"
            stars = repo['stargazers_count']
            desc = repo['description'][:60] if repo['description'] else "No description"
            display = f"{private} {name} ★{stars} - {desc}"
            self.repo_listbox.insert(tk.END, display)
            self.repo_display_list.append(display)
            self.repo_data_map[display] = repo
        
        self.repo_listbox.bind("<Double-Button-1>", self.select_repo)
        self.repo_listbox.bind("<Return>", self.select_repo)
        
        btn_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        select_btn = tk.Button(btn_frame, text="[ENTER] SELECT REPOSITORY", command=self.select_repo,
                               font=("Consolas", 11, "bold"), bg=self.colors['purple'], fg='white',
                               activebackground=self.colors['dark_purple'], cursor="hand2",
                               padx=20, pady=5)
        select_btn.pack(side=tk.LEFT, padx=5)
        
        back_btn = tk.Button(btn_frame, text="[ESC] BACK", command=self.show_username_screen,
                             font=("Consolas", 11), bg=self.colors['gray'], fg='white',
                             activebackground='#666', cursor="hand2", padx=20, pady=5)
        back_btn.pack(side=tk.LEFT, padx=5)
        
        self.status_var.set(f"[SELECT] Loaded {len(self.repos)} repos. Double-click or press ENTER to select")
    
    def apply_repo_filter(self, event=None):
        query = self.filter_entry.get().lower()
        self.repo_listbox.delete(0, tk.END)
        
        for display in self.repo_display_list:
            if query in display.lower():
                self.repo_listbox.insert(tk.END, display)
    
    def select_repo(self, event=None):
        selection = self.repo_listbox.curselection()
        if not selection:
            messagebox.showwarning("Selection Error", "Please select a repository")
            return
        
        display = self.repo_listbox.get(selection[0])
        repo = self.repo_data_map[display]
        
        self.selected_repo = repo
        self.owner = repo['owner']['login']
        self.repo_name = repo['name']
        
        self.status_var.set(f"[LOADING] {self.owner}/{self.repo_name}...")
        self.root.update()
        
        def load_branch_thread():
            try:
                branch = self.api.get_default_branch(self.owner, self.repo_name)
                self.branch = branch
                self.current_path = ""
                self.navigation_stack = []
                self.selected_files = []
                self.root.after(0, self.show_file_browser)
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Failed to load repo: {e}"))
        
        threading.Thread(target=load_branch_thread, daemon=True).start()
    
    # ------------------------------------------------------------------
    # SCREEN 3: FILE BROWSER
    # ------------------------------------------------------------------
    def show_file_browser(self):
        self.clear_content()
        self.selected_files = []
        
        info_frame = tk.Frame(self.content_frame, bg=self.colors['black'], relief=tk.RIDGE, bd=1)
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        repo_info = f"📁 {self.owner}/{self.repo_name}  @  {self.branch}"
        tk.Label(info_frame, text=repo_info, font=("Consolas", 12, "bold"),
                fg=self.colors['purple'], bg=self.colors['black']).pack(side=tk.LEFT, padx=15, pady=8)
        
        self.path_var = tk.StringVar(value=f"📂 /{self.current_path}")
        tk.Label(info_frame, textvariable=self.path_var, font=("Consolas", 10),
                fg=self.colors['cyan'], bg=self.colors['black']).pack(side=tk.LEFT, padx=20)
        
        nav_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        nav_frame.pack(fill=tk.X, pady=5)
        
        up_btn = tk.Button(nav_frame, text="⬆ UP", command=self.go_up,
                          font=("Consolas", 10, "bold"), bg=self.colors['dark_purple'], fg='white',
                          activebackground=self.colors['purple'], cursor="hand2", padx=15)
        up_btn.pack(side=tk.LEFT, padx=2)
        
        root_btn = tk.Button(nav_frame, text="🏠 ROOT", command=self.go_root,
                            font=("Consolas", 10, "bold"), bg=self.colors['dark_purple'], fg='white',
                            activebackground=self.colors['purple'], cursor="hand2", padx=15)
        root_btn.pack(side=tk.LEFT, padx=2)
        
        back_btn = tk.Button(nav_frame, text="↺ BACK TO REPOS", command=self.show_repo_selection,
                            font=("Consolas", 10), bg=self.colors['gray'], fg='white',
                            activebackground='#666', cursor="hand2", padx=15)
        back_btn.pack(side=tk.RIGHT, padx=2)
        
        tree_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        columns = ("type", "size", "select")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="tree headings", height=28)
        
        self.tree.heading("#0", text="Name")
        self.tree.heading("type", text="Type")
        self.tree.heading("size", text="Size")
        self.tree.heading("select", text="✓")
        
        self.tree.column("#0", width=550)
        self.tree.column("type", width=100)
        self.tree.column("size", width=120)
        self.tree.column("select", width=60)
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=self.colors['black'], 
                       foreground=self.colors['white'], fieldbackground=self.colors['black'],
                       rowheight=26, font=("Consolas", 10))
        style.map('Treeview', background=[('selected', self.colors['purple'])])
        style.configure("Treeview.Heading", background=self.colors['dark_purple'],
                       foreground='white', font=("Consolas", 10, "bold"))
        
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        h_scroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<space>", self.on_space)
        self.root.bind("<Return>", lambda e: self.download_selected())
        
        btn_frame = tk.Frame(self.content_frame, bg=self.colors['bg'])
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.download_btn = tk.Button(btn_frame, text="⬇ DOWNLOAD SELECTED FILES [ENTER]",
                                      command=self.download_selected,
                                      font=("Consolas", 12, "bold"), bg=self.colors['green'],
                                      fg='white', activebackground='#27ae60', cursor="hand2",
                                      padx=25, pady=8)
        self.download_btn.pack()
        
        self.selection_var = tk.StringVar(value="Selected: 0 files")
        tk.Label(btn_frame, textvariable=self.selection_var,
                font=("Consolas", 11), fg=self.colors['yellow'], bg=self.colors['bg']).pack(pady=5)
        
        self.file_vars = {}
        self.load_directory()
    
    def load_directory(self):
        self.status_var.set(f"[LOADING] /{self.current_path}")
        self.root.update()
        
        def load_thread():
            try:
                contents = self.api.get_repo_contents(
                    self.owner, self.repo_name, self.current_path, self.branch
                )
                self.root.after(0, lambda: self.populate_tree(contents))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Load failed: {e}"))
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def populate_tree(self, contents):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.file_vars.clear()
        
        if self.current_path:
            parent_id = self.tree.insert("", "end", text=".. (parent directory)", 
                                         values=("DIR", ""), tags=("parent",))
            self.tree.tag_bind(parent_id, "<Double-1>", lambda e: self.go_up())
        
        dirs = [c for c in contents if c["type"] == "dir"]
        files = [c for c in contents if c["type"] == "file"]
        
        for d in dirs:
            item_id = self.tree.insert("", "end", text=f"📁 {d['name']}", 
                                       values=("DIRECTORY", ""), tags=("dir", d['path']))
            self.tree.tag_bind(item_id, "<Double-1>", 
                              lambda e, name=d['name']: self.enter_directory(name))
        
        for f in files:
            size_kb = f.get("size", 0) // 1024
            if size_kb < 1024:
                size_str = f"{size_kb} KB"
            else:
                size_str = f"{size_kb//1024} MB"
            
            item_id = self.tree.insert("", "end", text=f"📄 {f['name']}",
                                       values=("FILE", size_str, "□"),
                                       tags=("file", f['path']))
            
            var = tk.BooleanVar(value=False)
            self.file_vars[f['path']] = (var, f, item_id)
            var.trace_add("write", lambda *a, path=f['path'], v=var: self.update_checkbox_display(path, v))
            
            self.tree.tag_bind(item_id, "<Button-1>", 
                              lambda e, path=f['path'], v=var: self.toggle_selection(path, v))
        
        self.update_selection_count()
        self.status_var.set(f"[READY] {len(dirs)} directories, {len(files)} files. SPACE to select, ENTER to download")
    
    def toggle_selection(self, path, var):
        var.set(not var.get())
    
    def update_checkbox_display(self, path, var):
        for item in self.tree.get_children():
            tags = self.tree.item(item, "tags")
            if tags and len(tags) > 1 and tags[1] == path:
                check = "☑" if var.get() else "□"
                self.tree.set(item, "select", check)
                break
        self.update_selection_count()
    
    def update_selection_count(self):
        selected = sum(1 for var, _, _ in self.file_vars.values() if var.get())
        self.selection_var.set(f"Selected: {selected} files")
    
    def on_double_click(self, event):
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item:
            return
        tags = self.tree.item(item, "tags")
        if tags and "dir" in tags:
            name = self.tree.item(item, "text").replace("📁 ", "")
            if name == ".. (parent directory)":
                self.go_up()
            else:
                self.enter_directory(name)
    
    def on_space(self, event):
        item = self.tree.selection()[0] if self.tree.selection() else None
        if not item:
            return
        tags = self.tree.item(item, "tags")
        if tags and len(tags) > 1 and tags[0] == "file":
            path = tags[1]
            if path in self.file_vars:
                var, _, _ = self.file_vars[path]
                var.set(not var.get())
    
    def enter_directory(self, dir_name):
        self.navigation_stack.append(self.current_path)
        self.current_path = dir_name if not self.current_path else f"{self.current_path}/{dir_name}"
        self.load_directory()
    
    def go_up(self):
        if self.navigation_stack:
            self.current_path = self.navigation_stack.pop()
        else:
            self.current_path = ""
        self.load_directory()
    
    def go_root(self):
        self.navigation_stack = []
        self.current_path = ""
        self.load_directory()
    
    def download_selected(self):
        selected = [(path, item) for path, (var, item, _) in self.file_vars.items() if var.get()]
        
        if not selected:
            messagebox.showwarning("No Selection", "Select files with SPACE or click the ✓ column")
            return
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP files", "*.zip")],
            initialfile=f"{self.repo_name}_MSTAGRABBER.zip"
        )
        if not save_path:
            return
        
        self.download_btn.config(state=tk.DISABLED, text="⬇ DOWNLOADING...")
        self.status_var.set(f"[DOWNLOAD] Fetching {len(selected)} files...")
        self.root.update()
        
        def download_thread():
            try:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
                    for idx, (file_path, item) in enumerate(selected):
                        self.root.after(0, lambda i=idx+1: self.status_var.set(f"[DOWNLOAD] {i}/{len(selected)}: {file_path.split('/')[-1]}"))
                        content = self.api.download_file(self.owner, self.repo_name, file_path, self.branch)
                        zf.writestr(file_path, content)
                
                zip_buffer.seek(0)
                with open(save_path, "wb") as f:
                    f.write(zip_buffer.getvalue())
                
                self.root.after(0, lambda: self.download_complete(save_path, len(selected)))
            except Exception as e:
                self.root.after(0, lambda: self.show_error(f"Download failed: {e}"))
        
        threading.Thread(target=download_thread, daemon=True).start()
    
    def download_complete(self, save_path, count):
        self.download_btn.config(state=tk.NORMAL, text="⬇ DOWNLOAD SELECTED FILES [ENTER]")
        self.status_var.set(f"[COMPLETE] Saved {count} files to {save_path}")
        messagebox.showinfo("Download Complete", f"✅ Saved {count} files to:\n{save_path}")
        self.show_repo_selection()
    
    def set_token(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Set GitHub Token")
        dialog.geometry("550x200")
        dialog.configure(bg=self.colors['bg'])
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Enter GitHub Personal Access Token", 
                font=("Consolas", 12, "bold"), fg=self.colors['purple'],
                bg=self.colors['bg']).pack(pady=20)
        
        tk.Label(dialog, text="(Leave empty for anonymous - 60 req/hr | Token = 5000 req/hr)",
                font=("Consolas", 9), fg=self.colors['gray'], bg=self.colors['bg']).pack()
        
        token_entry = tk.Entry(dialog, font=("Consolas", 11), width=55,
                                bg=self.colors['black'], fg='white',
                                insertbackground='white', show="*")
        token_entry.pack(pady=20, padx=20)
        
        def save_token():
            token = token_entry.get().strip()
            if token:
                self.api = GitHubAPI(token)
                self.token = token
                self.status_var.set("[TOKEN] Token set - Rate limit increased to 5000/hr")
                messagebox.showinfo("Token Set", "GitHub token configured successfully.")
            else:
                self.status_var.set("[TOKEN] Using anonymous access (60 requests/hr)")
            dialog.destroy()
        
        btn_frame = tk.Frame(dialog, bg=self.colors['bg'])
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Set Token", command=save_token,
                 bg=self.colors['purple'], fg='white', cursor="hand2",
                 padx=20, pady=5, font=("Consolas", 10)).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg=self.colors['gray'], fg='white', cursor="hand2",
                 padx=20, pady=5, font=("Consolas", 10)).pack(side=tk.LEFT, padx=5)
    
    def show_error(self, msg):
        self.status_var.set(f"[ERROR] {msg}")
        messagebox.showerror("Error", msg)
    
    def exit_app(self):
        if messagebox.askyesno("Exit", "Exit MSTAGRABBER?"):
            self.root.destroy()
    
    def run(self):
        self.root.mainloop()

# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="MSTAGRABBER - Purple GUI GitHub Grabber")
    parser.add_argument("--token", help="GitHub personal access token")
    args = parser.parse_args()
    
    app = MSTAGRABBER(token=args.token)
    app.run()

if __name__ == "__main__":
    main()
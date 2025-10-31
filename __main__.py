"""
Simple but feature-rich web browser using PyQt6 + PyQt6 WebEngine.

Features:
- Tabbed browsing (open/close tabs)
- Address bar with navigation and search support
- Back / Forward / Reload / Stop / Home
- Bookmarks (saved to ~/.pyqt6_browser/bookmarks.json)
- Keyboard shortcuts: Ctrl+T (new tab), Ctrl+W (close tab), Ctrl+L (focus URL), Ctrl+R (reload)
- Right-click tab close

Requirements:
- Python 3.8+
- PyQt6 and PyQt6-WebEngine (pip install PyQt6 PyQt6-WebEngine)

Run:
python pyqt6_web_browser.py
"""

# This was created by ChatGPT but edited by The GregTech Guy on YouTube. See https://github.com/thegregtechguy/StupidAIBrowser for more info

import sys
import os
import json
from pathlib import Path
import google.generativeai as ai

from PyQt6.QtCore import QUrl, Qt, QSize
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QToolBar,
    QLineEdit,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QMessageBox,
    QFileDialog,
)
from PyQt6.QtGui import QAction
from PyQt6.QtGui import QIcon, QKeySequence

# Important: importing QWebEngineView initializes the WebEngine
from PyQt6.QtWebEngineWidgets import QWebEngineView

with open("aiBrowser.json", "r") as credentialFile:
    credentialData = json.load(credentialFile)
apiKey = credentialData["api"]

ai.configure(api_key=apiKey)
model = ai.GenerativeModel('models/gemini-2.0-flash-lite')
APP_DIR = Path.home() / ".pyqt6_browser"
BOOKMARKS_FILE = APP_DIR / "bookmarks.json"
prompt = "You are an AI who makes web pages. You are going to create a homepage for a browser named StupidInternetBrowser. It relies a lot on AI like you, to operate. Create buttons such as 'New Tab' and a search bar that leads to https://chatgpt.com as a prompt. Include JavaScript within the HTML file that makes the buttons work. Show ONLY the HTML of the file. DO NOT INCLUDE MARKDOWN. DO NOT INCLUDE ANY OTHER TEXT. DO NOT INCLUDE MARKDOWN SUCH AS '''HTML."
rawResponse = model.generate_content(prompt)
fullResponse = rawResponse.text.strip()
with open("aiindex.html", "w") as indexPage:
    indexPage.write(fullResponse)
myDirectory = Path(__file__).resolve().parent
HOME_PAGE = QUrl.fromLocalFile(os.fspath(myDirectory / "aiindex.html"))

class BrowserTab(QWidget):
    def __init__(self, url: str | None = None):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.webview = QWebEngineView()
        if url:
            self.webview.setUrl(QUrl(url))
        else:
            self.webview.setUrl(QUrl(HOME_PAGE))

        self.layout.addWidget(self.webview)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 Web Browser")
        self.setMinimumSize(900, 600)

        APP_DIR.mkdir(parents=True, exist_ok=True)
        self._load_bookmarks()

        self._create_toolbar()
        self._create_tabs()

    def _create_toolbar(self):
        navtb = QToolBar("Navigation")
        navtb.setIconSize(QSize(16, 16))
        self.addToolBar(navtb)

        # Back
        back_btn = QAction("Back", self)
        back_btn.setShortcut(QKeySequence.StandardKey.Back)
        back_btn.triggered.connect(lambda: self._current_view().back())
        navtb.addAction(back_btn)

        # Forward
        forward_btn = QAction("Forward", self)
        forward_btn.setShortcut(QKeySequence.StandardKey.Forward)
        forward_btn.triggered.connect(lambda: self._current_view().forward())
        navtb.addAction(forward_btn)

        # Reload
        reload_btn = QAction("Reload", self)
        reload_btn.setShortcut(QKeySequence.StandardKey.Refresh)
        reload_btn.triggered.connect(lambda: self._current_view().reload())
        navtb.addAction(reload_btn)

        # Stop
        stop_btn = QAction("Stop", self)
        stop_btn.triggered.connect(lambda: self._current_view().stop())
        navtb.addAction(stop_btn)

        navtb.addSeparator()

        # Home
        home_btn = QAction("Home", self)
        home_btn.setShortcut(QKeySequence("Ctrl+H"))
        home_btn.triggered.connect(self._go_home)
        navtb.addAction(home_btn)

        # Address bar
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self._navigate_to_url)
        self.urlbar.setClearButtonEnabled(True)
        self.urlbar.setPlaceholderText("Enter URL or search term and press Enter")
        navtb.addWidget(self.urlbar)

        # Add bookmark
        bookmark_btn = QAction("Bookmark", self)
        bookmark_btn.setShortcut(QKeySequence("Ctrl+D"))
        bookmark_btn.triggered.connect(self._add_bookmark)
        navtb.addAction(bookmark_btn)

        # Bookmarks menu (simple: open from dialog)
        open_bm = QAction("Open Bookmark...", self)
        open_bm.triggered.connect(self._open_bookmark)
        navtb.addAction(open_bm)

        navtb.addSeparator()

        # New tab
        new_tab_action = QAction("New Tab", self)
        new_tab_action.setShortcut(QKeySequence("Ctrl+T"))
        new_tab_action.triggered.connect(self._add_tab)
        navtb.addAction(new_tab_action)

        # Close tab
        close_tab_action = QAction("Close Tab", self)
        close_tab_action.setShortcut(QKeySequence("Ctrl+W"))
        close_tab_action.triggered.connect(self._close_current_tab)
        navtb.addAction(close_tab_action)

    def _create_tabs(self):
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self._close_tab_idx)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(self.tabs)

        # Add initial tab
        self._add_tab(HOME_PAGE)

    def _add_tab(self, url: str | None = None):
        if isinstance(url, bool):  # called by QAction accidentally
            url = None
        tab = BrowserTab(url)
        i = self.tabs.addTab(tab, "New Tab")
        self.tabs.setCurrentIndex(i)

        webview = tab.webview
        webview.urlChanged.connect(lambda qurl, webview=webview: self._update_urlbar(qurl, webview))
        tabPrompt = f"You are a helpful assistant who names internet browser tabs in one word. The URL of the page will be provided to you, and you need to only make one word for the name. ONLY INCLUDE THE ONE WORD. DO NOT INCLUDE ANY MARKDOWN. DO NOT INCLUDE ANY OTHER WORDS. DO NOT USE ANY HTML. The URL is: {url}"
        rawResponse = model.generate_content(tabPrompt)
        tabTitle = rawResponse.text.strip()
        print(tabTitle)
        webview.titleChanged.connect(lambda title, i=i: self.tabs.setTabText(i, tabTitle))
        webview.iconChanged.connect(lambda icon, i=i: self.tabs.setTabIcon(i, icon))

    def _current_view(self) -> QWebEngineView:
        current_widget = self.tabs.currentWidget()
        if current_widget:
            return current_widget.webview
        return None

    def _navigate_to_url(self):
        text = self.urlbar.text().strip()
        if not text:
            return
        url = self._interpret_text_as_url(text)
        view = self._current_view()
        if view:
            view.setUrl(QUrl(url))

    def _interpret_text_as_url(self, text: str) -> str:
        # naive URL vs search detection
        if "://" in text or text.startswith("www.") or text.endswith(".com") or text.endswith(".org") or text.endswith(".net"):
            if not text.startswith("http"):
                return "https://" + text
            return text
        # Otherwise use Google search
        from urllib.parse import quote_plus

        return f"https://chatgpt.com/?prompt={quote_plus(text)}"

    def _update_urlbar(self, qurl: QUrl, webview: QWebEngineView):
        # Only update address bar if the sender is the current tab's webview
        if webview != self._current_view():
            return
        self.urlbar.setText(qurl.toString())
        self.urlbar.setCursorPosition(0)

    def _on_tab_changed(self, index: int):
        view = self._current_view()
        if view:
            self.urlbar.setText(view.url().toString())
            self.urlbar.setCursorPosition(0)

    def _close_tab_idx(self, i: int):
        if self.tabs.count() < 2:
            self.close()
            return
        self.tabs.removeTab(i)

    def _close_current_tab(self):
        idx = self.tabs.currentIndex()
        if idx >= 0:
            self._close_tab_idx(idx)

    def _go_home(self):
        view = self._current_view()
        if view:
            view.setUrl(QUrl(HOME_PAGE))

    # Bookmarks
    def _load_bookmarks(self):
        self.bookmarks = []
        try:
            if BOOKMARKS_FILE.exists():
                with open(BOOKMARKS_FILE, "r", encoding="utf-8") as f:
                    self.bookmarks = json.load(f)
        except Exception:
            self.bookmarks = []

    def _save_bookmarks(self):
        try:
            with open(BOOKMARKS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.bookmarks, f, indent=2, ensure_ascii=False)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save bookmarks: {e}")

    def _add_bookmark(self):
        view = self._current_view()
        if not view:
            return
        url = view.url().toString()
        title = view.title() or url
        # Avoid duplicates
        if any(bm["url"] == url for bm in self.bookmarks):
            QMessageBox.information(self, "Bookmark", "This page is already bookmarked.")
            return
        self.bookmarks.append({"title": title, "url": url})
        self._save_bookmarks()
        QMessageBox.information(self, "Bookmark", "Page bookmarked.")

    def _open_bookmark(self):
        if not self.bookmarks:
            QMessageBox.information(self, "Bookmarks", "No bookmarks yet. Press Ctrl+D to add one.")
            return
        # Let user choose a bookmark via a simple file-like dialog
        items = [f"{bm['title']} — {bm['url']}" for bm in self.bookmarks]
        item, ok = QFileDialog.getOpenFileName(self, "Open Bookmark (pick from list)")
        # QFileDialog doesn't support picking from a list; implement a fallback chooser
        if not ok or not item:
            # fallback: use a simple selection via QMessageBox
            from PyQt6.QtWidgets import QInputDialog

            choice, ok2 = QInputDialog.getItem(self, "Bookmarks", "Choose a bookmark:", items, 0, False)
            if ok2 and choice:
                url = choice.split(" — ")[-1]
                self._add_tab(url)
            return


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("PyQt6 Browser")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

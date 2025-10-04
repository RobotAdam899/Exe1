# sim_chaos_vm_jumpscare.py
# Gereksinimler: python3, PyQt6
# Kurulum: pip install PyQt6
# Çalıştır: python sim_chaos_vm_jumpscare.py
# KULLAN: Sadece SANAL MAKİNEDE deneyin. Panik butonu: Ctrl+Shift+Q

import sys
import random
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QMessageBox, QVBoxLayout, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QCursor, QFont, QKeySequence, QShortcut

# Ayarlar
INITIAL_WINDOWS = 50
MAX_WINDOWS = 200
CLONE_ON_CLOSE = 3     # Bir pencere kapatıldığında kaç tane ek açılsın (zararsız, küçük sayı)
GLITCH_INTERVAL_MS = 300  # Glitch animasyon sıklığı

# Global state
all_windows = []
app_ref = None

def safe_random_geometry(screen_rect):
    w = random.randint(240, 520)
    h = random.randint(160, 420)
    x = random.randint(max(0, screen_rect.left()), max(0, screen_rect.right() - w))
    y = random.randint(max(0, screen_rect.top()), max(0, screen_rect.bottom() - h))
    return x, y, w, h

class GlitchWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowTitle("Sanal VM - Simulated Window")
        self.label = QLabel("", self)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(QFont("Consolas", 18, QFont.Weight.Bold))
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # başlangıç stil
        self.setStyleSheet("background-color: black; color: white; border: 2px solid #111;")
        self.show()

        # Glitch animasyonu
        self.glitch_timer = QTimer(self)
        self.glitch_timer.timeout.connect(self._glitch_step)
        self.glitch_timer.start(GLITCH_INTERVAL_MS + random.randint(-150, 300))

        # Fare çarpı işareti (cursor)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        all_windows.append(self)

    def _glitch_step(self):
        # rastgele parça: metin, renk, pozisyon küçük sarsıntı
        texts = ["GLITCH", "ERROR", "█▒▒▒▒", "⚠︎", "404 VM", "!!", "ŞAŞMA"]
        text = random.choice(texts)
        # rastgele renk paleti (zararsız)
        fg = random.choice(["#FFFFFF", "#FF66CC", "#66FF66", "#66CCFF", "#FFFF66"])
        bg = random.choice(["#000000", "#330000", "#001133", "#113300", "#1a001a"])
        self.label.setText(text)
        self.setStyleSheet(f"background-color: {bg}; color: {fg};")
        # küçük sarsıntı hareketi
        offset_x = random.randint(-10, 10)
        offset_y = random.randint(-10, 10)
        self.move(max(0, self.x() + offset_x), max(0, self.y() + offset_y))

    def closeEvent(self, event):
        # Kapamayı engelle: yerine CLONE_ON_CLOSE pencere oluştur (ekranın kararlılığı için sınır)
        event.ignore()
        # Kaç tane daha açılacağını hesapla (sınır dahil)
        current_count = len(all_windows)
        if current_count < MAX_WINDOWS:
            to_create = min(CLONE_ON_CLOSE, MAX_WINDOWS - current_count)
            for _ in range(to_create):
                spawn_glitch_window()
        # kısa bir "jumpscare" tarzı stil değişimi
        self._temporary_flash()

    def _temporary_flash(self):
        old_style = self.styleSheet()
        self.setStyleSheet("background-color: white; color: black;")
        QTimer.singleShot(140, lambda: self.setStyleSheet(old_style))

def spawn_glitch_window():
    screen = app_ref.primaryScreen()
    screen_rect = screen.availableGeometry()
    x, y, w, h = safe_random_geometry(screen_rect)
    wgt = GlitchWindow()
    wgt.setGeometry(x, y, w, h)
    wgt.show()

def create_initial_windows(n):
    for _ in range(n):
        spawn_glitch_window()

def kill_all_and_exit():
    # Tüm pencereleri kapat ve çık
    for w in list(all_windows):
        try:
            w.glitch_timer.stop()
        except Exception:
            pass
        try:
            w.close()
        except Exception:
            pass
    QApplication.quit()

def show_startup_warning():
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle("UYARI - SANAL MAKİNEDE ÇALIŞTIRIN")
    msg.setText(
        "Bu simülasyon **rahatsız edici** bir pencere davranışı üretir.\n\n"
        "Sadece SANAL MAKİNE üzerinde çalıştırın. Programda acil kapatma tuşu: Ctrl+Shift+Q\n\n"
        "Devam etmek istiyor musunuz?"
    )
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    resp = msg.exec()
    return resp == QMessageBox.StandardButton.Yes

def main():
    global app_ref
    app = QApplication(sys.argv)
    app_ref = app

    # Kısa yol: Ctrl+Shift+Q => acil kapama
    shortcut = QShortcut(QKeySequence("Ctrl+Shift+Q"), app.activeWindow() if app.activeWindow() else None)
    # QShortcut bir parent beklediği için ana pencere yoksa uygulamaya bağlayalım via timer
    def ensure_shortcut():
        # bağla tüm açık pencerelere (basit yol)
        for w in all_windows:
            QShortcut(QKeySequence("Ctrl+Shift+Q"), w).activated.connect(kill_all_and_exit)
    QTimer.singleShot(250, ensure_shortcut)

    # Ayrıca global key için bir yedek kısayol oluştur: her yeni pencereye bağlama
    # (create_initial_windows içinde de pencereler oluştuğunda ekleniyor)

    ok = show_startup_warning()
    if not ok:
        print("Kullanıcı iptal etti. Çıkılıyor.")
        sys.exit(0)

    create_initial_windows(INITIAL_WINDOWS)

    # Her pencere açıldığında ona acil kapatma kısayolunu bağlayalım
    def attach_shortcuts_periodically():
        for w in all_windows:
            # Eğer zaten bağlı değilse bağla
            if not hasattr(w, "_kill_shortcut_attached"):
                sc = QShortcut(QKeySequence("Ctrl+Shift+Q"), w)
                sc.activated.connect(kill_all_and_exit)
                w._kill_shortcut_attached = True
    attach_timer = QTimer()
    attach_timer.timeout.connect(attach_shortcuts_periodically)
    attach_timer.start(300)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()

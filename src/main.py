import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QWidget, QCheckBox, QTextEdit, QProgressBar, QLineEdit,
                             QCalendarWidget)
from PyQt6.QtCore import Qt, QDate, QThread, pyqtSignal, QObject, pyqtSlot
from PyQt6.QtGui import QIcon
import qdarktheme
from scraping import run_scraper
import traceback
import logging
from datetime import datetime, timedelta
from utils import clean_data
from utils import analysis


class AnalysisThread(QThread):
    update_log = pyqtSignal(str)
    update_total_progress = pyqtSignal(int)
    update_crawler_progress = pyqtSignal(int)
    update_crawler_status = pyqtSignal(str)
    analysis_finished = pyqtSignal()

    def __init__(self, start_date, end_date, skip_crawl):
        QThread.__init__(self)
        self.start_date = start_date
        self.end_date = end_date
        self.skip_crawl = skip_crawl

    def set_dates(self, start_date, end_date):
        today = datetime.now().date()

        if start_date == "" and end_date == "":
            # 如果兩個日期都沒有提供，使用今天作為結束日期，一個月前作為開始日期
            self.end_date = today
            self.start_date = today
        elif start_date == "":
            # 如果只提供了結束日期，使用一個月前作為開始日期
            self.end_date = end_date
            self.start_date = end_date
        elif end_date == "":
            # 如果只提供了開始日期，使用今天作為結束日期
            self.start_date = start_date
            self.end_date = today
        else:
            # 如果兩個日期都提供了，直接使用
            self.start_date = start_date
            self.end_date = end_date

        self.update_log.emit(f"分析日期範圍：從 {self.start_date} 到 {self.end_date}\n")

    def run(self):
        self.running = True
        try:
            # steps = ["爬蟲", "數據清理", "文本分析", "評分", "最終分析"]
            steps = ["爬蟲", "數據清理", "文本分析"]
            switcher = {
                "爬蟲": run_scraper,
                "數據清理": clean_data,
                "文本分析": analysis
            }
            for i, step in enumerate(steps):
                if not self.running:
                    break
                self.update_log.emit(f"開始{step}...\n")
                self.update_total_progress.emit(int((i + 1) / len(steps) * 100))
                self.set_dates(self.start_date, self.end_date)
                if step == "爬蟲":
                    sitemap_url = "https://technews.tw/sitemap.xml"
                    self.df = switcher.get(step)(sitemap_url, self.start_date, self.end_date, self.progress_callback )
                else :
                    self.df = switcher.get(step)(self.df)

                self.update_log.emit(f"{step}完成\n")
                self.update_log.emit("=" * 100 + "\n")

            if self.running:
                self.update_log.emit("分析完成")
            else:
                self.update_log.emit("分析被用戶中止")
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            error_details = traceback.extract_tb(exc_traceback)

            error_msg = f"錯誤類型: {exc_type.__name__}\n"
            error_msg += f"錯誤信息: {str(e)}\n"
            error_msg += "錯誤追蹤:\n"
            for frame in error_details:
                filename = frame.filename
                line_no = frame.lineno
                func_name = frame.name
                error_msg += f"  文件 '{filename}', 第 {line_no} 行, 在 {func_name} 函數\n"

            self.update_log.emit(error_msg)
            logging.error(error_msg)
        finally:
            self.running = False
            self.analysis_finished.emit()

    def progress_callback(self, progress, message):
        # print(f"Progress: {progress * 100}%, Message: {message}")  # 調試輸出
        self.update_crawler_progress.emit( int( progress * 100) )
        self.update_crawler_status.emit(message)
        # self.update_log.emit(message + "\n")

    def terminate(self):
        # 方法 1: 使用 PyQt 的 terminate 方法
        super().terminate()
        self.wait()  # 等待線程結束

class DateSelector(QWidget):
    def __init__(self, label):
        super().__init__()
        layout = QHBoxLayout()
        self.setLayout(layout)

        self.label = QLabel(label)
        self.date_edit = QLineEdit()
        self.date_edit.setReadOnly(True)
        self.calendar_button = QPushButton(icon=QIcon.fromTheme("calendar"))
        self.calendar_button.clicked.connect(self.show_calendar)

        layout.addWidget(self.label)
        layout.addWidget(self.date_edit)
        layout.addWidget(self.calendar_button)

        self.calendar = QCalendarWidget()
        self.calendar.setWindowFlags(Qt.WindowType.Popup)
        self.calendar.clicked.connect(self.set_date)

    def show_calendar(self):
        pos = self.calendar_button.mapToGlobal(self.calendar_button.rect().bottomRight())
        self.calendar.move(pos)
        self.calendar.show()

    def set_date(self, date):
        self.date_edit.setText(date.toString("yyyy/MM/dd"))
        self.calendar.hide()


class NewsAnalysisGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("科技新聞分析系統")
        self.setGeometry(100, 100, 1024, 800)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.create_title_bar()
        self.create_widgets()

        self.analysis_thread = None

        self.isRunning = False

    def create_title_bar(self):
        title_bar = QWidget()
        title_layout = QHBoxLayout(title_bar)
        title_label = QLabel("科技新聞分析系統")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        close_button = QPushButton("×")
        close_button.setFixedSize(30, 30)
        close_button.clicked.connect(self.close)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_button)
        self.main_layout.addWidget(title_bar)

    def create_widgets(self):
        # 日期選擇
        date_frame = QWidget()
        date_layout = QHBoxLayout(date_frame)
        self.start_date = DateSelector("開始日期:")
        date_layout.addWidget(self.start_date)
        self.end_date = DateSelector("結束日期:")
        date_layout.addWidget(self.end_date)
        self.main_layout.addWidget(date_frame)

        # 控制選項
        control_frame = QWidget()
        control_layout = QHBoxLayout(control_frame)
        self.skip_crawl = QCheckBox("跳過爬蟲")
        control_layout.addWidget(self.skip_crawl)
        self.start_button = QPushButton("開始分析")
        self.start_button.clicked.connect(self.start_analysis)
        control_layout.addStretch()
        control_layout.addWidget(self.start_button)
        self.main_layout.addWidget(control_frame)

        # 進度條
        progress_frame = QWidget()
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.addWidget(QLabel("總進度:"))
        self.total_progress = QProgressBar()
        progress_layout.addWidget(self.total_progress)


        progress_layout.addWidget(QLabel("爬蟲進度:"))
        self.crawler_progress = QProgressBar()
        self.crawler_progress.setRange(0, 100)
        progress_layout.addWidget(self.crawler_progress)
        self.crawler_status = QLabel("")
        progress_layout.addWidget(self.crawler_status)
        self.main_layout.addWidget(progress_frame)

        # 日誌
        log_frame = QWidget()
        log_layout = QVBoxLayout(log_frame)
        log_layout.addWidget(QLabel("日誌:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        log_layout.addWidget(self.log_text)
        self.main_layout.addWidget(log_frame)

        # 結果
        result_frame = QWidget()
        result_layout = QVBoxLayout(result_frame)
        result_layout.addWidget(QLabel("分析結果:"))
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        result_layout.addWidget(self.result_text)
        self.main_layout.addWidget(result_frame)

    def start_analysis(self):

        if ( self.isRunning == True ) :
            self.stop_analysis()
            return

        self.isRunning = True

        start_date = self.start_date.date_edit.text()
        end_date = self.end_date.date_edit.text()
        skip_crawl = self.skip_crawl.isChecked()

        self.log_text.clear()
        self.result_text.clear()
        self.total_progress.setValue(0)
        self.crawler_progress.setValue(0)
        self.crawler_status.setText("")
        self.start_button.setText("停止分析")

        # 假設 AnalysisThread 是 QThread 的子類
        self.analysis_thread = AnalysisThread(start_date, end_date, skip_crawl)
        # 連接信號
        self.analysis_thread.update_log.connect(self.update_log)
        self.analysis_thread.update_total_progress.connect(self.total_progress.setValue)
        self.analysis_thread.update_crawler_progress.connect(self.update_crawler_progress)
        self.analysis_thread.update_crawler_status.connect(self.crawler_status.setText)
        self.analysis_thread.analysis_finished.connect(self.on_analysis_finished)
        self.analysis_thread.finished.connect(self.analysis_thread.deleteLater)  # 添加這行來正確清理線程

        self.analysis_thread.start()

    def stop_analysis(self):
        self.analysis_thread.terminate()
        self.start_button.setText("開始分析")
        self.update_total_progress(0)
        self.update_log( "取消分析........." )
        self.isRunning = False

    @pyqtSlot(str)
    def update_log(self, message):
        self.log_text.append(message)
        self.log_text.verticalScrollBar().setValue(self.log_text.verticalScrollBar().maximum())

    @pyqtSlot(int)
    def update_total_progress(self, value):
        self.total_progress.setValue(value)

    @pyqtSlot(int)
    def update_crawler_progress(self, value):
        self.crawler_progress.setValue(value)

    @pyqtSlot(str)
    def update_crawler_status(self, status):
        self.crawler_status.setText(status)

    @pyqtSlot()
    def on_analysis_finished(self):
        self.start_button.setText("開始分析")
        self.update_log("分析完成")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos)
            self.dragPos = event.globalPosition().toPoint()
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark")
    window = NewsAnalysisGUI()
    window.show()
    sys.exit(app.exec())
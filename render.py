import sys
import argparse
from clocks.cq_editor.main_window import MainWindow
from PyQt5.QtWidgets import QApplication

NAME = 'CQ-editor-bodge'

#need to initialize QApp here, otherewise svg icons do not work on windows
app = QApplication(sys.argv,
                   applicationName=NAME)

def main():


    win = MainWindow(filename="wall_clock_04.py")
    # win.render()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":

    main()

import sys
import warnings

# Suppress deprecation warnings from torch.hub cached YOLOv5 code
warnings.filterwarnings("ignore", category=FutureWarning, message=".*torch.cuda.amp.autocast.*")
warnings.filterwarnings("ignore", category=UserWarning, message=".*autocast.*")

import torch

from PyQt5.QtWidgets import QApplication

from Tool_Model.MainWindowModel import MainWindowClass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindowClass()
    window.show()
    try:
        sys.exit(app.exec_())
    except Exception as e:
        print(e)
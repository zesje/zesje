import sys
import os
sys.path.append(os.getcwd())

from server import app
app.run(debug=True)

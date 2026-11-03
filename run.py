import os
import sys
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("==================================================================")
    print("  SevaSetu - Hyperlocal Community Services & Medicine Platform")
    print("  Regional Hubs: Gudlavalleru (521356) | Gudivada | Machilipatnam")
    print("  Rural & Low-Literacy Accessible Interface")
    print("==================================================================")
    print("  Open your browser at: http://127.0.0.1:5000")
    print("  Press Ctrl+C to stop.")
    print("==================================================================")
    app.run(debug=True, host='127.0.0.1', port=5000)

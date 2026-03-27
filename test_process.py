import logging
logging.basicConfig(level=logging.INFO)

from api.main import process_document
import sys

# Create a mock PDF
with open("test.pdf", "w") as f:
    f.write("This is a physics test. The electron has mass. It orbits the nucleus.")

# Process it
process_document("test.pdf", "test.pdf")
print("FINISHED TEST PROCESS!")

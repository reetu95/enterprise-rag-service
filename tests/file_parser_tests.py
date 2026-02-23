from app.file_parser import FileParser

# Change this to a real file inside your sources folder
test_file = "sources/0fd16b59-0b48-4607-9f6a-ec46a952f5f6.txt"

try:
    parser = FileParser(test_file)
    content = parser.parse()
    print("Parsed successfully.")
    print("First 500 characters:")
    print(content[:500])
except Exception as e:
    print(f"Test failed: {e}")